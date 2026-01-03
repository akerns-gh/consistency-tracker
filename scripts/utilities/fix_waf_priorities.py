#!/usr/bin/env python3
"""
Fix WAF priorities: Ensure IPAllowlist is at priority 0 and remove USOnlyGeoMatch.
"""

import boto3
import copy
from botocore.exceptions import ClientError

AWS_REGION = "us-east-1"

def log_info(message: str):
    print(f"ℹ️  {message}")

def log_warn(message: str):
    print(f"⚠️  {message}")

def log_error(message: str):
    print(f"❌ {message}")

def log_success(message: str):
    print(f"✅ {message}")

def fix_cloudfront_waf():
    """Fix CloudFront WAF: Remove USOnlyGeoMatch and ensure IPAllowlist is at priority 0."""
    print("="*60)
    print("Fixing CloudFront WAF Configuration")
    print("="*60)
    print()
    
    wafv2_client = boto3.client('wafv2', region_name='us-east-1')
    scope = "CLOUDFRONT"
    
    # Find Web ACL
    try:
        response = wafv2_client.list_web_acls(Scope=scope)
        web_acls = response.get('WebACLs', [])
        
        web_acl = None
        for wacl in web_acls:
            if wacl['Name'].startswith('CloudFrontWebACL'):
                web_acl = wacl
                break
        
        if not web_acl:
            log_error("CloudFront Web ACL not found")
            return False
        
        web_acl_id = web_acl['Id']
        web_acl_name = web_acl['Name']
        log_info(f"Found Web ACL: {web_acl_name} (ID: {web_acl_id})")
        
        # Get current configuration
        response = wafv2_client.get_web_acl(
            Scope=scope,
            Id=web_acl_id,
            Name=web_acl_name
        )
        web_acl_data = response.get('WebACL', {})
        lock_token = response.get('LockToken')
        current_rules = web_acl_data.get('Rules', [])
        custom_response_bodies = web_acl_data.get('CustomResponseBodies', {})
        
        log_info(f"Current rules: {len(current_rules)}")
        for rule in sorted(current_rules, key=lambda r: r.get('Priority', 999)):
            print(f"  Priority {rule.get('Priority')}: {rule.get('Name')}")
        
        # Process rules
        updated_rules = []
        ip_allowlist_rule = None
        geo_match_found = False
        
        for rule in current_rules:
            rule_name = rule.get('Name', '')
            
            if rule_name == 'IPAllowlist':
                # Keep IPAllowlist but ensure it's at priority 0
                ip_allowlist_rule = copy.deepcopy(rule)
                ip_allowlist_rule['Priority'] = 0
                log_info("Found IPAllowlist rule - will set to priority 0")
            elif rule_name == 'USOnlyGeoMatch':
                # Skip USOnlyGeoMatch - remove it
                geo_match_found = True
                log_warn(f"Found USOnlyGeoMatch rule at priority {rule.get('Priority')} - will remove it")
            else:
                # Keep all other rules, but adjust priorities if needed
                preserved_rule = copy.deepcopy(rule)
                current_priority = preserved_rule.get('Priority', 999)
                
                # If this rule is at priority 0 and it's not IPAllowlist, move it
                if current_priority == 0:
                    preserved_rule['Priority'] = 1
                    log_info(f"Moving {rule_name} from priority 0 to priority 1")
                
                updated_rules.append(preserved_rule)
        
        # Add IPAllowlist at the beginning (priority 0)
        if ip_allowlist_rule:
            updated_rules.insert(0, ip_allowlist_rule)
            log_success("IPAllowlist rule set to priority 0")
        else:
            log_error("IPAllowlist rule not found! Cannot proceed.")
            return False
        
        if geo_match_found:
            log_success("USOnlyGeoMatch rule will be removed")
        else:
            log_info("USOnlyGeoMatch rule not found (already removed)")
        
        # Sort rules by priority to ensure correct order
        updated_rules.sort(key=lambda r: r.get('Priority', 999))
        
        log_info(f"\nUpdated rule order:")
        for rule in updated_rules:
            print(f"  Priority {rule.get('Priority')}: {rule.get('Name')}")
        
        # Update Web ACL
        try:
            log_info("\nUpdating Web ACL...")
            wafv2_client.update_web_acl(
                Scope=scope,
                Id=web_acl_id,
                Name=web_acl_name,
                LockToken=lock_token,
                DefaultAction=web_acl_data.get('DefaultAction', {'Block': {}}),
                Rules=updated_rules,
                VisibilityConfig=web_acl_data.get('VisibilityConfig', {}),
                CustomResponseBodies=custom_response_bodies if custom_response_bodies else None
            )
            
            log_success("Web ACL updated successfully!")
            log_info("Changes will propagate within 2-3 minutes")
            return True
            
        except ClientError as e:
            log_error(f"Failed to update Web ACL: {e}")
            return False
        
    except ClientError as e:
        log_error(f"Error: {e}")
        return False

if __name__ == "__main__":
    fix_cloudfront_waf()

