#!/usr/bin/env python3
"""
Verify WAF is blocking by checking if a specific IP would be allowed.
"""

import boto3
import sys
from botocore.exceptions import ClientError

AWS_REGION = "us-east-1"

def check_ip_in_allowlist(ip_to_check: str):
    """Check if an IP is in any of the allowlist IP sets."""
    print(f"Checking if IP {ip_to_check} is in allowlists...\n")
    
    for scope, scope_name in [("CLOUDFRONT", "CloudFront"), ("REGIONAL", "API Gateway")]:
        print(f"{scope_name} WAF:")
        waf_region = "us-east-1" if scope == "CLOUDFRONT" else AWS_REGION
        wafv2_client = boto3.client('wafv2', region_name=waf_region)
        
        try:
            # List IP sets
            response = wafv2_client.list_ip_sets(Scope=scope)
            ip_sets = response.get('IPSets', [])
            
            found_in_allowlist = False
            
            for ipset in ip_sets:
                name = ipset.get('Name', '')
                # Check if this is an allowlist IP set
                if 'Allowlist' in name or 'allowlist' in name.lower():
                    try:
                        ipset_details = wafv2_client.get_ip_set(
                            Scope=scope,
                            Id=ipset['Id'],
                            Name=name
                        )
                        addresses = ipset_details.get('IPSet', {}).get('Addresses', [])
                        
                        # Check if IP is in this set
                        for addr in addresses:
                            # Handle CIDR notation
                            if '/' in addr:
                                ip_part, cidr = addr.split('/')
                                if ip_part == ip_to_check:
                                    print(f"  ✅ Found in {name}: {addr}")
                                    found_in_allowlist = True
                                # For simplicity, we're doing exact match
                                # In production, you'd want to check CIDR ranges
                            else:
                                if addr == ip_to_check:
                                    print(f"  ✅ Found in {name}: {addr}")
                                    found_in_allowlist = True
                        
                        if addresses:
                            print(f"  {name} contains {len(addresses)} address(es)")
                            for addr in addresses[:5]:
                                print(f"    - {addr}")
                            if len(addresses) > 5:
                                print(f"    ... and {len(addresses) - 5} more")
                    except ClientError as e:
                        print(f"  ⚠️  Error checking {name}: {e}")
            
            if not found_in_allowlist:
                print(f"  ❌ IP {ip_to_check} is NOT in any allowlist")
                print(f"  ⚠️  This IP should be BLOCKED by WAF")
            else:
                print(f"  ✅ IP {ip_to_check} is in allowlist - should be ALLOWED")
            
            print()
            
        except ClientError as e:
            print(f"  ❌ Error: {e}\n")

def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_waf_blocking.py <IP_ADDRESS>")
        print("Example: python verify_waf_blocking.py 104.234.212.131")
        sys.exit(1)
    
    ip_to_check = sys.argv[1]
    check_ip_in_allowlist(ip_to_check)
    
    print("="*60)
    print("Recommendations:")
    print("="*60)
    print("""
1. If IP is NOT in allowlist but you can still access:
   - Clear browser cache and try again
   - Try incognito/private browsing mode
   - Wait 2-3 minutes for WAF propagation
   - Check CloudFront cache (may need invalidation)

2. If you need to block this IP:
   - Make sure it's NOT in any allowlist IP sets
   - Verify WAF default action is BLOCK
   - Verify IPAllowlist rule is at priority 0
   - Verify USOnlyGeoMatch rule is removed

3. To test blocking:
   - Use curl from a different IP
   - Check CloudWatch WAF metrics for blocked requests
    """)

if __name__ == "__main__":
    main()

