#!/usr/bin/env python3
"""
Check current WAF configuration status.

This script shows:
- Current Web ACL rules and their priorities
- Default action
- IP sets and their contents
- Whether USOnlyGeoMatch is present
- Whether IPAllowlist is present
"""

import boto3
import json
from botocore.exceptions import ClientError

AWS_REGION = "us-east-1"

def log_info(message: str):
    """Print info message."""
    print(f"ℹ️  {message}")

def log_warn(message: str):
    """Print warning message."""
    print(f"⚠️  {message}")

def log_error(message: str):
    """Print error message."""
    print(f"❌ {message}")

def log_success(message: str):
    """Print success message."""
    print(f"✅ {message}")

def check_waf(scope: str, scope_name: str):
    """Check WAF configuration for a given scope."""
    print(f"\n{'='*60}")
    print(f"{scope_name} WAF (Scope: {scope})")
    print(f"{'='*60}\n")
    
    waf_region = "us-east-1" if scope == "CLOUDFRONT" else AWS_REGION
    wafv2_client = boto3.client('wafv2', region_name=waf_region)
    
    try:
        # List Web ACLs
        response = wafv2_client.list_web_acls(Scope=scope)
        web_acls = response.get('WebACLs', [])
        
        if not web_acls:
            log_warn(f"No Web ACLs found for {scope_name}")
            return
        
        # Find the relevant Web ACL
        web_acl = None
        patterns = ["ApiGatewayWebACL", "CloudFrontWebACL"]
        for pattern in patterns:
            for wacl in web_acls:
                if wacl['Name'].startswith(pattern):
                    web_acl = wacl
                    break
            if web_acl:
                break
        
        if not web_acl:
            log_warn(f"Could not find expected Web ACL for {scope_name}")
            log_info("Available Web ACLs:")
            for wacl in web_acls:
                print(f"  - {wacl['Name']} (ID: {wacl['Id']})")
            return
        
        log_info(f"Found Web ACL: {web_acl['Name']} (ID: {web_acl['Id']})")
        
        # Get full Web ACL details
        response = wafv2_client.get_web_acl(
            Scope=scope,
            Id=web_acl['Id'],
            Name=web_acl['Name']
        )
        web_acl_data = response.get('WebACL', {})
        
        # Check default action
        default_action = web_acl_data.get('DefaultAction', {})
        if 'Allow' in default_action:
            log_warn("Default Action: ALLOW (open access)")
        elif 'Block' in default_action:
            log_success("Default Action: BLOCK (restrictive)")
        else:
            log_warn(f"Default Action: {default_action}")
        
        # Check rules
        rules = web_acl_data.get('Rules', [])
        print(f"\n📋 Rules ({len(rules)} total):")
        
        if not rules:
            log_warn("No rules configured")
        else:
            # Sort by priority
            sorted_rules = sorted(rules, key=lambda r: r.get('Priority', 999))
            
            ip_allowlist_found = False
            geo_match_found = False
            
            for rule in sorted_rules:
                name = rule.get('Name', 'Unknown')
                priority = rule.get('Priority', 'Unknown')
                action = rule.get('Action', {})
                
                action_type = "ALLOW" if 'Allow' in action else "BLOCK" if 'Block' in action else "COUNT"
                
                print(f"  Priority {priority}: {name} -> {action_type}")
                
                if name == 'IPAllowlist':
                    ip_allowlist_found = True
                    # Show IP set references
                    statement = rule.get('Statement', {})
                    if 'IPSetReferenceStatement' in statement:
                        arn = statement['IPSetReferenceStatement'].get('ARN', '')
                        print(f"    └─ IP Set ARN: {arn}")
                    elif 'OrStatement' in statement:
                        statements = statement['OrStatement'].get('Statements', [])
                        for stmt in statements:
                            if 'IPSetReferenceStatement' in stmt:
                                arn = stmt['IPSetReferenceStatement'].get('ARN', '')
                                print(f"    └─ IP Set ARN: {arn}")
                
                if name == 'USOnlyGeoMatch':
                    geo_match_found = True
                    statement = rule.get('Statement', {})
                    if 'GeoMatchStatement' in statement:
                        countries = statement['GeoMatchStatement'].get('CountryCodes', [])
                        print(f"    └─ Countries: {', '.join(countries)}")
            
            print()
            
            if ip_allowlist_found:
                log_success("IPAllowlist rule is present")
            else:
                log_warn("IPAllowlist rule is NOT present")
            
            if geo_match_found:
                log_warn("USOnlyGeoMatch rule is present (may override IP restrictions!)")
            else:
                log_success("USOnlyGeoMatch rule is NOT present")
        
        # Check IP sets
        print(f"\n🔍 IP Sets:")
        try:
            ip_sets_response = wafv2_client.list_ip_sets(Scope=scope)
            ip_sets = ip_sets_response.get('IPSets', [])
            
            if not ip_sets:
                log_warn("No IP sets found")
            else:
                for ipset in ip_sets:
                    name = ipset.get('Name', 'Unknown')
                    arn = ipset.get('ARN', '')
                    ip_version = ipset.get('IPAddressVersion', 'Unknown')
                    
                    # Get IP set details
                    try:
                        ipset_details = wafv2_client.get_ip_set(
                            Scope=scope,
                            Id=ipset['Id'],
                            Name=name
                        )
                        addresses = ipset_details.get('IPSet', {}).get('Addresses', [])
                        print(f"  {name} ({ip_version}):")
                        print(f"    ARN: {arn}")
                        if addresses:
                            print(f"    Addresses ({len(addresses)}):")
                            for addr in addresses[:10]:  # Show first 10
                                print(f"      - {addr}")
                            if len(addresses) > 10:
                                print(f"      ... and {len(addresses) - 10} more")
                        else:
                            print(f"    Addresses: (empty)")
                    except ClientError as e:
                        print(f"  {name}: Error getting details - {e}")
        except ClientError as e:
            log_error(f"Failed to list IP sets: {e}")
        
    except ClientError as e:
        log_error(f"Error checking {scope_name} WAF: {e}")

def main():
    """Main function."""
    print("="*60)
    print("WAF Configuration Status Check")
    print("="*60)
    
    # Check CloudFront WAF
    check_waf("CLOUDFRONT", "CloudFront")
    
    # Check API Gateway WAF
    check_waf("REGIONAL", "API Gateway")
    
    print("\n" + "="*60)
    print("Diagnosis:")
    print("="*60)
    print("""
If IP restrictions are not working, check:
1. Is IPAllowlist rule present and at priority 0?
2. Is USOnlyGeoMatch rule removed?
3. Is default action set to BLOCK?
4. Are your IPs in the IP sets?
5. Have WAF changes propagated? (can take 2-3 minutes)
    """)

if __name__ == "__main__":
    main()

