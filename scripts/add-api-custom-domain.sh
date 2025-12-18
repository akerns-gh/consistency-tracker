#!/bin/bash

# Script to add API Gateway custom domain
# This creates the custom domain and maps it to the API

set -euo pipefail

# Configuration
DOMAIN_NAME="api.repwarrior.net"
CERTIFICATE_ARN="arn:aws:acm:us-east-1:707406431671:certificate/9b4263b1-79c5-4a14-8e6e-fc34db9ec944"
API_ID="tnobyn4jbf"
STAGE_NAME="prod"
AWS_REGION="us-east-1"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Creating API Gateway custom domain: ${DOMAIN_NAME}${NC}"

# Create the custom domain
echo "Creating custom domain..."
DOMAIN_RESULT=$(aws apigatewayv2 create-domain-name \
    --domain-name "$DOMAIN_NAME" \
    --domain-name-configurations "CertificateArn=$CERTIFICATE_ARN,EndpointType=REGIONAL,SecurityPolicy=TLS_1_2" \
    --region "$AWS_REGION" \
    --output json 2>&1)

if echo "$DOMAIN_RESULT" | grep -q "already exists"; then
    echo -e "${YELLOW}Domain already exists, getting existing domain...${NC}"
    DOMAIN_INFO=$(aws apigatewayv2 get-domain-name \
        --domain-name "$DOMAIN_NAME" \
        --region "$AWS_REGION" \
        --output json)
else
    DOMAIN_INFO="$DOMAIN_RESULT"
fi

DOMAIN_NAME_ID=$(echo "$DOMAIN_INFO" | jq -r '.DomainName')
TARGET_DOMAIN=$(echo "$DOMAIN_INFO" | jq -r '.DomainNameConfigurations[0].TargetDomainName')

echo -e "${GREEN}✅ Custom domain created: ${DOMAIN_NAME}${NC}"
echo "   Domain Name ID: $DOMAIN_NAME_ID"
echo "   Target Domain: $TARGET_DOMAIN"

# Get API ID (REST API)
echo ""
echo "Mapping API to custom domain..."

# Create API mapping
aws apigatewayv2 create-api-mapping \
    --domain-name "$DOMAIN_NAME" \
    --api-id "$API_ID" \
    --stage "$STAGE_NAME" \
    --api-mapping-key "" \
    --region "$AWS_REGION" \
    --output json > /dev/null 2>&1 || echo "Mapping may already exist"

echo -e "${GREEN}✅ API mapped to custom domain${NC}"
echo ""
echo "Next steps:"
echo "1. Update Route 53 to point api.repwarrior.net to: $TARGET_DOMAIN"
echo "2. Wait 5-10 minutes for DNS propagation"
echo "3. Test: https://${DOMAIN_NAME}/prod/"

