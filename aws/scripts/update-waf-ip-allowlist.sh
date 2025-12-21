#!/bin/bash

# Script to update WAF IP allowlist with current IP addresses
# NOTE: This script is for ADDITIONAL IP allowlisting on top of geographic restrictions.
# The WAF is configured to only allow IPs from the United States by default.
# This script can be used to add specific IPs that may be outside the US or as an additional layer of security.
#
# This script will:
# 1. Detect your current IPv4 and IPv6 addresses
# 2. Create or update IP sets for both
# 3. Update the WAF Web ACL to allow traffic from these IPs (in addition to US geo-blocking)
# 4. Set default action to Block (restrictive mode)

set -euo pipefail

# Configuration
SCOPE="CLOUDFRONT"
REGION="us-east-1"
IPV4_IPSET_NAME="Allowlist"
IPV6_IPSET_NAME="AllowlistIPv6"
WEBACL_NAME="CloudFrontWebACL-vqZX7V0FN6hP"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    log_error "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    log_error "jq is not installed. Please install it first (brew install jq)."
    exit 1
fi

# Get current IP addresses
log_info "Detecting current IP addresses..."
CURRENT_IPV4=$(curl -s -4 --max-time 5 ifconfig.me 2>/dev/null || echo "")
CURRENT_IPV6=$(curl -s -6 --max-time 5 ifconfig.me 2>/dev/null || echo "")

if [ -z "$CURRENT_IPV4" ] && [ -z "$CURRENT_IPV6" ]; then
    log_error "Could not detect IP addresses. Please check your internet connection."
    exit 1
fi

if [ -n "$CURRENT_IPV4" ]; then
    log_info "IPv4 address: $CURRENT_IPV4"
fi
if [ -n "$CURRENT_IPV6" ]; then
    log_info "IPv6 address: $CURRENT_IPV6"
fi

# Get Web ACL ID
log_info "Looking up Web ACL..."
WEBACL_JSON=$(aws wafv2 list-web-acls --scope "$SCOPE" --region "$REGION" --output json)
WEBACL_ID=$(echo "$WEBACL_JSON" | jq -r ".WebACLs[] | select(.Name == \"$WEBACL_NAME\") | .Id")

if [ -z "$WEBACL_ID" ] || [ "$WEBACL_ID" == "null" ]; then
    log_error "Web ACL '$WEBACL_NAME' not found."
    exit 1
fi

log_info "Found Web ACL: $WEBACL_NAME (ID: $WEBACL_ID)"

# Function to create or update IP set
create_or_update_ipset() {
    local ipset_name=$1
    local ip_address=$2
    local ip_version=$3
    
    log_info "Processing $ip_version IP set: $ipset_name"
    
    # Check if IP set exists
    local ipset_list=$(aws wafv2 list-ip-sets --scope "$SCOPE" --region "$REGION" --output json)
    local ipset_id=$(echo "$ipset_list" | jq -r ".IPSets[]? | select(.Name == \"$ipset_name\") | .Id")
    
    if [ -n "$ipset_id" ] && [ "$ipset_id" != "null" ]; then
        # IP set exists, update it
        log_info "Updating existing IP set: $ipset_name"
        local lock_token=$(aws wafv2 get-ip-set \
            --scope "$SCOPE" \
            --region "$REGION" \
            --name "$ipset_name" \
            --id "$ipset_id" \
            --output json | jq -r '.LockToken')
        
        if [ "$ip_version" == "IPV4" ]; then
            aws wafv2 update-ip-set \
                --scope "$SCOPE" \
                --region "$REGION" \
                --name "$ipset_name" \
                --id "$ipset_id" \
                --lock-token "$lock_token" \
                --addresses "${ip_address}/32" \
                --output json > /dev/null
        else
            aws wafv2 update-ip-set \
                --scope "$SCOPE" \
                --region "$REGION" \
                --name "$ipset_name" \
                --id "$ipset_id" \
                --lock-token "$lock_token" \
                --addresses "${ip_address}/128" \
                --output json > /dev/null
        fi
        log_info "Updated IP set: $ipset_name"
    else
        # IP set doesn't exist, create it
        log_info "Creating new IP set: $ipset_name"
        if [ "$ip_version" == "IPV4" ]; then
            aws wafv2 create-ip-set \
                --scope "$SCOPE" \
                --region "$REGION" \
                --name "$ipset_name" \
                --addresses "${ip_address}/32" \
                --ip-address-version "$ip_version" \
                --output json > /dev/null
        else
            aws wafv2 create-ip-set \
                --scope "$SCOPE" \
                --region "$REGION" \
                --name "$ipset_name" \
                --addresses "${ip_address}/128" \
                --ip-address-version "$ip_version" \
                --output json > /dev/null
        fi
        log_info "Created IP set: $ipset_name"
    fi
}

# Create or update IPv4 IP set
IPV4_IPSET_ARN=""
if [ -n "$CURRENT_IPV4" ]; then
    create_or_update_ipset "$IPV4_IPSET_NAME" "$CURRENT_IPV4" "IPV4"
    IPV4_IPSET_ARN=$(aws wafv2 list-ip-sets --scope "$SCOPE" --region "$REGION" --output json | \
        jq -r ".IPSets[]? | select(.Name == \"$IPV4_IPSET_NAME\") | .ARN")
fi

# Create or update IPv6 IP set
IPV6_IPSET_ARN=""
if [ -n "$CURRENT_IPV6" ]; then
    create_or_update_ipset "$IPV6_IPSET_NAME" "$CURRENT_IPV6" "IPV6"
    IPV6_IPSET_ARN=$(aws wafv2 list-ip-sets --scope "$SCOPE" --region "$REGION" --output json | \
        jq -r ".IPSets[]? | select(.Name == \"$IPV6_IPSET_NAME\") | .ARN")
fi

# Get current Web ACL configuration
log_info "Fetching current Web ACL configuration..."
WEBACL_JSON=$(aws wafv2 get-web-acl \
    --scope "$SCOPE" \
    --region "$REGION" \
    --name "$WEBACL_NAME" \
    --id "$WEBACL_ID" \
    --output json)

LOCK_TOKEN=$(echo "$WEBACL_JSON" | jq -r '.LockToken')
RULES=$(echo "$WEBACL_JSON" | jq -c '.WebACL.Rules')

# Build the updated Allowlist rule
log_info "Building updated Allowlist rule..."

# Create statements array for OR statement
STATEMENTS="[]"

if [ -n "$IPV4_IPSET_ARN" ] && [ "$IPV4_IPSET_ARN" != "null" ]; then
    STATEMENTS=$(echo "$STATEMENTS" | jq --arg arn "$IPV4_IPSET_ARN" \
        '. += [{"IPSetReferenceStatement": {"ARN": $arn}}]')
fi

if [ -n "$IPV6_IPSET_ARN" ] && [ "$IPV6_IPSET_ARN" != "null" ]; then
    STATEMENTS=$(echo "$STATEMENTS" | jq --arg arn "$IPV6_IPSET_ARN" \
        '. += [{"IPSetReferenceStatement": {"ARN": $arn}}]')
fi

# Determine rule statement structure
if [ "$(echo "$STATEMENTS" | jq 'length')" -eq 1 ]; then
    # Single IP set, use direct reference
    ALLOWLIST_STATEMENT=$(echo "$STATEMENTS" | jq '.[0]')
elif [ "$(echo "$STATEMENTS" | jq 'length')" -eq 2 ]; then
    # Multiple IP sets, use OR statement
    ALLOWLIST_STATEMENT=$(echo "{}" | jq --argjson statements "$STATEMENTS" \
        '{OrStatement: {Statements: $statements}}')
else
    log_error "No IP sets available to create allowlist rule."
    exit 1
fi

# Update or create Allowlist rule
ALLOWLIST_RULE=$(echo "{}" | jq \
    --argjson statement "$ALLOWLIST_STATEMENT" \
    '{
        Name: "Allowlist",
        Priority: 0,
        Statement: $statement,
        Action: {Allow: {}},
        VisibilityConfig: {
            SampledRequestsEnabled: true,
            CloudWatchMetricsEnabled: true,
            MetricName: "Allowlist"
        }
    }')

# Update rules array
UPDATED_RULES=$(echo "$RULES" | jq \
    --argjson allowlist_rule "$ALLOWLIST_RULE" \
    'map(if .Name == "Allowlist" then $allowlist_rule else . end) | 
     if map(.Name == "Allowlist") | any then . else [$allowlist_rule] + . end |
     map(if .Name == "RateLimitRule" then .Priority = 1 elif .Name == "AWSManagedRulesCommonRuleSet" then .Priority = 2 else . end) |
     sort_by(.Priority)')

# Save rules to temp file
TEMP_RULES_FILE=$(mktemp)
echo "$UPDATED_RULES" > "$TEMP_RULES_FILE"

# Update Web ACL
log_info "Updating Web ACL..."
aws wafv2 update-web-acl \
    --scope "$SCOPE" \
    --region "$REGION" \
    --name "$WEBACL_NAME" \
    --id "$WEBACL_ID" \
    --lock-token "$LOCK_TOKEN" \
    --default-action Block={} \
    --rules "file://$TEMP_RULES_FILE" \
    --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=ConsistencyTrackerWebACL \
    --output json > /dev/null

# Cleanup
rm -f "$TEMP_RULES_FILE"

log_info "Web ACL updated successfully!"
log_info ""
log_info "Summary:"
if [ -n "$CURRENT_IPV4" ]; then
    log_info "  - IPv4 allowed: $CURRENT_IPV4"
fi
if [ -n "$CURRENT_IPV6" ]; then
    log_info "  - IPv6 allowed: $CURRENT_IPV6"
fi
log_info "  - Default action: Block"
log_info "  - Allowlist rule priority: 0 (highest)"
log_info ""
log_warn "Note: WAF rule changes may take 2-3 minutes to propagate."

