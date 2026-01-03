#!/usr/bin/env python3
"""
Configure WAF IP allowlist restrictions for complete lockdown.

This script will apply IP restrictions to BOTH:
1. API Gateway WAF (REGIONAL scope)
2. CloudFront WAF (CLOUDFRONT scope)

For each WAF, it will:
1. Create or update IP sets with allowed IP addresses
2. Add an IP allowlist rule to the Web ACL (highest priority)
3. Set default action to Block (restrictive mode)
4. Preserve existing rules

Usage:
    python configure_ip_restriction.py
    python configure_ip_restriction.py --ips 203.0.113.1/32,198.51.100.1/32
    python configure_ip_restriction.py --auto-detect-ip
    python configure_ip_restriction.py --api-only  # Only restrict API Gateway
    python configure_ip_restriction.py --cloudfront-only  # Only restrict CloudFront
"""

import argparse
import json
import sys
import re
import time
import copy
from typing import List, Optional
import boto3
from botocore.exceptions import ClientError

# Configuration
AWS_REGION = "us-east-1"
API_IPV4_IPSET_NAME = "ApiGatewayAllowlist"
API_IPV6_IPSET_NAME = "ApiGatewayAllowlistIPv6"
CF_IPV4_IPSET_NAME = "CloudFrontAllowlist"
CF_IPV6_IPSET_NAME = "CloudFrontAllowlistIPv6"


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


def detect_current_ip() -> Optional[str]:
    """Detect current public IPv4 address."""
    try:
        import urllib.request
        with urllib.request.urlopen('https://ifconfig.me', timeout=5) as response:
            return response.read().decode('utf-8').strip()
    except Exception as e:
        log_warn(f"Could not auto-detect IP: {e}")
        return None


def validate_ip_cidr(ip_cidr: str) -> bool:
    """
    Validate IP address in CIDR format.
    
    Args:
        ip_cidr: IP address in CIDR format (e.g., "203.0.113.1/32")
        
    Returns:
        True if valid, False otherwise
    """
    # IPv4 CIDR pattern
    ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}(/\d{1,2})?$'
    # IPv6 CIDR pattern (simplified)
    ipv6_pattern = r'^([0-9a-fA-F:]+)(/\d{1,3})?$'
    
    if re.match(ipv4_pattern, ip_cidr) or re.match(ipv6_pattern, ip_cidr):
        return True
    return False


def parse_ip_addresses(ip_string: str) -> tuple[List[str], List[str]]:
    """
    Parse IP addresses string into IPv4 and IPv6 lists.
    
    Args:
        ip_string: Comma-separated IP addresses in CIDR format
        
    Returns:
        Tuple of (ipv4_list, ipv6_list)
    """
    ipv4_addresses = []
    ipv6_addresses = []
    
    for ip in ip_string.split(','):
        ip = ip.strip()
        if not ip:
            continue
        
        # Validate IP format
        if not validate_ip_cidr(ip):
            log_warn(f"Invalid IP format: {ip}. Skipping...")
            continue
        
        # Add /32 for IPv4 or /128 for IPv6 if no CIDR specified
        if '/' not in ip:
            if ':' in ip:
                ip = f"{ip}/128"  # IPv6
            else:
                ip = f"{ip}/32"   # IPv4
        
        # Simple check: IPv6 contains colons
        if ':' in ip:
            ipv6_addresses.append(ip)
        else:
            ipv4_addresses.append(ip)
    
    return ipv4_addresses, ipv6_addresses


def start_propagation_timer():
    """
    Start a timer that counts up to show elapsed time since WAF changes.
    Runs until user presses Ctrl+C or for 5 minutes.
    """
    print()
    log_info("Starting propagation timer...")
    print("Press Ctrl+C to stop the timer and exit")
    print()
    
    start_time = time.time()
    max_duration = 300  # 5 minutes
    
    try:
        while True:
            elapsed = time.time() - start_time
            
            if elapsed >= max_duration:
                print(f"\r⏱️  Elapsed time: {int(elapsed // 60)}m {int(elapsed % 60)}s (5 minutes reached)", end="", flush=True)
                print()
                log_info("Timer completed. WAF changes should be propagated by now.")
                break
            
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            print(f"\r⏱️  Elapsed time: {minutes}m {seconds}s", end="", flush=True)
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        print(f"\r⏱️  Elapsed time: {minutes}m {seconds}s (stopped by user)", end="", flush=True)
        print()
        log_info("Timer stopped.")


def prompt_for_ips() -> tuple[List[str], List[str]]:
    """
    Interactively prompt user for IP addresses.
    
    Returns:
        Tuple of (ipv4_list, ipv6_list)
    """
    print()
    print("Enter allowed IPv4 addresses (one per line, or comma-separated)")
    print("Format: IP address in CIDR format (e.g., 203.0.113.1/32)")
    print("Press Enter on empty line when done, or 'q' to quit")
    print()
    
    ipv4_addresses = []
    
    while True:
        try:
            user_input = input("IPv4> ").strip()
            
            if user_input.lower() == 'q':
                log_info("Cancelled by user")
                sys.exit(0)
            
            if not user_input:
                break
            
            # Handle comma-separated input
            if ',' in user_input:
                for ip in user_input.split(','):
                    ip = ip.strip()
                    if ip:
                        ipv4_addresses.append(ip)
            else:
                ipv4_addresses.append(user_input)
                
        except KeyboardInterrupt:
            print()
            log_info("Cancelled by user")
            sys.exit(0)
        except EOFError:
            break
    
    # Parse and validate IPv4
    if ipv4_addresses:
        ip_string = ','.join(ipv4_addresses)
        parsed_ipv4, _ = parse_ip_addresses(ip_string)
        ipv4_addresses = parsed_ipv4
    
    # Ask for IPv6 addresses
    print()
    print("Enter allowed IPv6 addresses (optional, one per line, or comma-separated)")
    print("Format: IP address in CIDR format (e.g., 2001:db8::1/128)")
    print("Press Enter on empty line to skip, or 'q' to quit")
    print()
    
    ipv6_addresses = []
    
    while True:
        try:
            user_input = input("IPv6> ").strip()
            
            if user_input.lower() == 'q':
                log_info("Cancelled by user")
                sys.exit(0)
            
            if not user_input:
                break
            
            # Handle comma-separated input
            if ',' in user_input:
                for ip in user_input.split(','):
                    ip = ip.strip()
                    if ip:
                        ipv6_addresses.append(ip)
            else:
                ipv6_addresses.append(user_input)
                
        except KeyboardInterrupt:
            print()
            log_info("Cancelled by user")
            sys.exit(0)
        except EOFError:
            break
    
    # Parse and validate IPv6
    if ipv6_addresses:
        ip_string = ','.join(ipv6_addresses)
        _, parsed_ipv6 = parse_ip_addresses(ip_string)
        ipv6_addresses = parsed_ipv6
    
    if not ipv4_addresses and not ipv6_addresses:
        log_error("No valid IP addresses provided")
        sys.exit(1)
    
    return ipv4_addresses, ipv6_addresses


class WAFIPRestrictionConfigurator:
    """Configure WAF IP restrictions for a specific scope (API Gateway or CloudFront)."""
    
    def __init__(
        self,
        scope: str,
        region: str = AWS_REGION,
        web_acl_name: Optional[str] = None,
        web_acl_name_pattern: Optional[str] = None,
        ipv4_ipset_name: str = None,
        ipv6_ipset_name: str = None,
    ):
        """
        Initialize WAF configurator.
        
        Args:
            scope: WAF scope ("REGIONAL" for API Gateway, "CLOUDFRONT" for CloudFront)
            region: AWS region (us-east-1 for CloudFront, can vary for API Gateway)
            web_acl_name: Name of the Web ACL (will auto-detect if None)
            web_acl_name_pattern: Pattern to match Web ACL name (e.g., "ApiGatewayWebACL", "CloudFrontWebACL")
            ipv4_ipset_name: Name for IPv4 IP set
            ipv6_ipset_name: Name for IPv6 IP set
        """
        self.scope = scope
        self.region = region
        self.web_acl_name = web_acl_name
        self.web_acl_name_pattern = web_acl_name_pattern
        self.ipv4_ipset_name = ipv4_ipset_name
        self.ipv6_ipset_name = ipv6_ipset_name
        # Store removed USOnlyGeoMatch rule for restoration
        self.removed_geo_match_rule = None
        # CloudFront WAF must use us-east-1, regardless of scope
        waf_region = "us-east-1" if scope == "CLOUDFRONT" else region
        self.wafv2_client = boto3.client('wafv2', region_name=waf_region)
    
    def find_web_acl(self) -> Optional[dict]:
        """Find the Web ACL for the configured scope."""
        try:
            response = self.wafv2_client.list_web_acls(Scope=self.scope)
            
            web_acls = response.get('WebACLs', [])
            
            if self.web_acl_name:
                # Find by exact name
                for web_acl in web_acls:
                    if web_acl['Name'] == self.web_acl_name:
                        return web_acl
            elif self.web_acl_name_pattern:
                # Find by pattern
                for web_acl in web_acls:
                    if web_acl['Name'].startswith(self.web_acl_name_pattern):
                        return web_acl
            else:
                # Try common patterns
                patterns = ["ApiGatewayWebACL", "CloudFrontWebACL"]
                for pattern in patterns:
                    for web_acl in web_acls:
                        if web_acl['Name'].startswith(pattern):
                            return web_acl
            
            return None
        except ClientError as e:
            log_error(f"Failed to list Web ACLs: {e}")
            return None
    
    def get_web_acl_details(self, web_acl_id: str) -> Optional[dict]:
        """Get full details of a Web ACL including LockToken."""
        try:
            web_acl = self.find_web_acl()
            if not web_acl:
                return None
                
            response = self.wafv2_client.get_web_acl(
                Scope=self.scope,
                Id=web_acl_id,
                Name=web_acl['Name']
            )
            # LockToken is at the top level of the response, not in WebACL
            web_acl_data = response.get('WebACL', {})
            web_acl_data['LockToken'] = response.get('LockToken')
            return web_acl_data
        except ClientError as e:
            log_error(f"Failed to get Web ACL details: {e}")
            return None
    
    def create_or_update_ip_set(
        self,
        ipset_name: str,
        addresses: List[str],
        ip_version: str
    ) -> Optional[str]:
        """
        Create or update an IP set.
        
        Args:
            ipset_name: Name of the IP set
            addresses: List of IP addresses in CIDR format
            ip_version: "IPV4" or "IPV6"
            
        Returns:
            ARN of the IP set, or None if failed
        """
        if not addresses:
            return None
        
        try:
            # Check if IP set exists
            response = self.wafv2_client.list_ip_sets(Scope=self.scope)
            ip_sets = response.get('IPSets', [])
            
            existing_ipset = None
            for ipset in ip_sets:
                if ipset['Name'] == ipset_name:
                    existing_ipset = ipset
                    break
            
            if existing_ipset:
                # Update existing IP set
                log_info(f"Updating existing IP set: {ipset_name}")
                get_response = self.wafv2_client.get_ip_set(
                    Scope=self.scope,
                    Id=existing_ipset['Id'],
                    Name=ipset_name
                )
                
                lock_token = get_response['LockToken']
                
                self.wafv2_client.update_ip_set(
                    Scope=self.scope,
                    Id=existing_ipset['Id'],
                    Name=ipset_name,
                    LockToken=lock_token,
                    Addresses=addresses,
                    Description=f"Allowed IP addresses - {self.scope} scope - {ip_version}"
                )
                
                log_success(f"Updated IP set: {ipset_name} with {len(addresses)} address(es)")
                return existing_ipset['ARN']
            else:
                # Create new IP set
                log_info(f"Creating new IP set: {ipset_name}")
                response = self.wafv2_client.create_ip_set(
                    Scope=self.scope,
                    Name=ipset_name,
                    IPAddressVersion=ip_version,
                    Addresses=addresses,
                    Description=f"Allowed IP addresses - {self.scope} scope - {ip_version}"
                )
                
                log_success(f"Created IP set: {ipset_name} with {len(addresses)} address(es)")
                return response['Summary']['ARN']
                
        except ClientError as e:
            log_error(f"Failed to create/update IP set {ipset_name}: {e}")
            return None
    
    def update_web_acl_with_ip_restriction(
        self,
        ipv4_arn: Optional[str],
        ipv6_arn: Optional[str]
    ) -> bool:
        """
        Update Web ACL to add IP allowlist rule and set default action to Block.
        Temporarily removes USOnlyGeoMatch rule to prevent it from overriding IP restrictions.
        
        Args:
            ipv4_arn: ARN of IPv4 IP set
            ipv6_arn: ARN of IPv6 IP set
            
        Returns:
            True if successful, False otherwise
        """
        if not ipv4_arn and not ipv6_arn:
            log_error("No IP sets provided")
            return False
        
        # Find Web ACL
        web_acl = self.find_web_acl()
        if not web_acl:
            log_error("Web ACL not found. Please specify --web-acl-name")
            log_info("Available Web ACLs:")
            try:
                response = self.wafv2_client.list_web_acls(Scope=self.scope)
                for wacl in response.get('WebACLs', []):
                    print(f"  - {wacl['Name']}")
            except:
                pass
            return False
        
        web_acl_id = web_acl['Id']
        web_acl_name = web_acl['Name']
        self.web_acl_name = web_acl_name  # Update for get_web_acl_details
        
        log_info(f"Found Web ACL: {web_acl_name} (ID: {web_acl_id})")
        
        # Get current Web ACL configuration
        web_acl_details = self.get_web_acl_details(web_acl_id)
        if not web_acl_details:
            return False
        
        lock_token = web_acl_details['LockToken']
        current_rules = web_acl_details.get('Rules', [])
        current_default_action = web_acl_details.get('DefaultAction', {})
        custom_response_bodies = web_acl_details.get('CustomResponseBodies', {})
        
        # Build IP allowlist rule statement
        statements = []
        if ipv4_arn:
            statements.append({
                'IPSetReferenceStatement': {
                    'ARN': ipv4_arn
                }
            })
        if ipv6_arn:
            statements.append({
                'IPSetReferenceStatement': {
                    'ARN': ipv6_arn
                }
            })
        
        # Create rule statement (OR if multiple, direct if single)
        if len(statements) == 1:
            rule_statement = statements[0]
        else:
            rule_statement = {
                'OrStatement': {
                    'Statements': statements
                }
            }
        
        # Create or update IPAllowlist rule
        allowlist_rule = {
            'Name': 'IPAllowlist',
            'Priority': 0,  # Highest priority
            'Statement': rule_statement,
            'Action': {
                'Allow': {}
            },
            'VisibilityConfig': {
                'SampledRequestsEnabled': True,
                'CloudWatchMetricsEnabled': True,
                'MetricName': 'IPAllowlist'
            }
        }
        
        # Update or add the allowlist rule
        # IMPORTANT: Preserve all existing rules except USOnlyGeoMatch (temporarily remove it)
        updated_rules = []
        allowlist_exists = False
        allowlist_current_priority = None
        used_priorities = set()
        geo_match_rule = None
        
        # First pass: check if IPAllowlist exists, get its priority, find USOnlyGeoMatch, and collect all used priorities
        for rule in current_rules:
            if rule['Name'] == 'IPAllowlist':
                allowlist_exists = True
                allowlist_current_priority = rule.get('Priority', 0)
            elif rule['Name'] == 'USOnlyGeoMatch':
                # Store the geo match rule for later restoration
                geo_match_rule = copy.deepcopy(rule)
                log_info("Found USOnlyGeoMatch rule - will temporarily remove it during IP restrictions")
            else:
                # Only add priorities of non-IPAllowlist rules to used_priorities
                used_priorities.add(rule.get('Priority', 0))
        
        # Store removed geo match rule for restoration
        if geo_match_rule:
            self.removed_geo_match_rule = geo_match_rule
        
        # Second pass: preserve all existing rules except IPAllowlist and USOnlyGeoMatch
        for rule in current_rules:
            if rule['Name'] == 'IPAllowlist':
                # Update existing IPAllowlist rule
                updated_rules.append(allowlist_rule)
            elif rule['Name'] == 'USOnlyGeoMatch':
                # Skip USOnlyGeoMatch - temporarily remove it
                log_info("Temporarily removing USOnlyGeoMatch rule to enforce IP restrictions")
            else:
                # Keep existing rule EXACTLY as it is (deep copy to avoid mutation)
                preserved_rule = copy.deepcopy(rule)
                current_priority = preserved_rule.get('Priority', 999)
                
                # If this rule is at priority 0 and it's not IPAllowlist, move it to priority 1
                # This ensures IPAllowlist can be at priority 0 without conflicts
                if current_priority == 0:
                    preserved_rule['Priority'] = 1
                    log_info(f"Moving {rule.get('Name', 'unknown')} from priority 0 to priority 1 to make room for IPAllowlist")
                
                updated_rules.append(preserved_rule)
        
        # Determine priority for IPAllowlist rule - always set to 0
        if not allowlist_exists:
            # IPAllowlist doesn't exist - add it at priority 0
            allowlist_rule['Priority'] = 0
            updated_rules.insert(0, allowlist_rule)
            log_info("IPAllowlist rule added at priority 0 (highest priority)")
        else:
            # IPAllowlist exists - ensure it's at priority 0
            for rule in updated_rules:
                if rule['Name'] == 'IPAllowlist':
                    rule['Priority'] = 0
                    log_info("IPAllowlist rule set to priority 0 (highest priority)")
                    break
        
        # Sort rules by priority to ensure correct order (important for AWS WAF)
        # This prevents duplicate priority errors and ensures rules are evaluated in the correct order
        updated_rules.sort(key=lambda r: r.get('Priority', 999))
        
        log_info(f"Final rule order:")
        for rule in updated_rules:
            print(f"  Priority {rule.get('Priority')}: {rule.get('Name')}")
        
        # Update Web ACL with retry logic
        max_retries = 5
        retry_delay = 2  # Start with 2 seconds
        
        for attempt in range(max_retries):
            try:
                # Get fresh lock token on retry (lock token may have changed)
                if attempt > 0:
                    log_info(f"Retrying Web ACL update (attempt {attempt + 1}/{max_retries})...")
                    fresh_details = self.get_web_acl_details(web_acl_id)
                    if fresh_details:
                        lock_token = fresh_details['LockToken']
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                
                log_info("Updating Web ACL with IP allowlist rule...")
                
                # Prepare update parameters
                update_params = {
                    'Scope': self.scope,
                    'Id': web_acl_id,
                    'Name': web_acl_name,
                    'LockToken': lock_token,
                    'DefaultAction': {
                        'Block': {}  # Block by default
                    },
                    'Rules': updated_rules,
                    'VisibilityConfig': web_acl_details['VisibilityConfig']
                }
                
                # Include custom response bodies if they exist (required for CloudFront WAF)
                if custom_response_bodies:
                    update_params['CustomResponseBodies'] = custom_response_bodies
                
                self.wafv2_client.update_web_acl(**update_params)
                
                log_success("Web ACL updated successfully!")
                if geo_match_rule:
                    log_info("USOnlyGeoMatch rule temporarily removed - will be restored when IP restrictions are removed")
                return True
                
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                if error_code == 'WAFUnavailableEntityException' and attempt < max_retries - 1:
                    log_warn(f"WAF resource temporarily unavailable, will retry: {e}")
                    continue
                else:
                    log_error(f"Failed to update Web ACL: {e}")
                    return False
        
        log_error("Failed to update Web ACL after all retries")
        return False
    
    def configure(
        self,
        ipv4_addresses: List[str],
        ipv6_addresses: List[str]
    ) -> bool:
        """
        Main method to configure IP restrictions.
        
        Args:
            ipv4_addresses: List of IPv4 addresses in CIDR format
            ipv6_addresses: List of IPv6 addresses in CIDR format
            
        Returns:
            True if successful, False otherwise
        """
        scope_name = "API Gateway" if self.scope == "REGIONAL" else "CloudFront"
        log_info(f"Starting {scope_name} WAF IP restriction configuration...")
        
        # Create or update IP sets
        ipv4_arn = None
        ipv6_arn = None
        
        if ipv4_addresses and self.ipv4_ipset_name:
            ipv4_arn = self.create_or_update_ip_set(
                self.ipv4_ipset_name,
                ipv4_addresses,
                "IPV4"
            )
        
        if ipv6_addresses and self.ipv6_ipset_name:
            ipv6_arn = self.create_or_update_ip_set(
                self.ipv6_ipset_name,
                ipv6_addresses,
                "IPV6"
            )
        
        if not ipv4_arn and not ipv6_arn:
            log_error("Failed to create any IP sets")
            return False
        
        # Check if Web ACL exists before trying to update
        web_acl = self.find_web_acl()
        if not web_acl:
            log_error(f"Web ACL not found for {scope_name} WAF")
            log_info("Available Web ACLs:")
            try:
                response = self.wafv2_client.list_web_acls(Scope=self.scope)
                for wacl in response.get('WebACLs', []):
                    print(f"  - {wacl['Name']} (ID: {wacl['Id']})")
            except Exception as e:
                log_warn(f"Could not list Web ACLs: {e}")
            return False
        
        # Update Web ACL
        success = self.update_web_acl_with_ip_restriction(ipv4_arn, ipv6_arn)
        
        if success:
            scope_name = "API Gateway" if self.scope == "REGIONAL" else "CloudFront"
            log_success(f"{scope_name} WAF configuration complete!")
        else:
            scope_name = "API Gateway" if self.scope == "REGIONAL" else "CloudFront"
            log_error(f"{scope_name} WAF configuration failed. Check error messages above.")
        
        return success
    
    def remove_ip_restrictions(self, delete_ip_sets: bool = False) -> bool:
        """
        Remove IP restrictions by deleting the IPAllowlist rule and setting default action to Allow.
        Restores USOnlyGeoMatch rule if it was previously removed.
        
        Args:
            delete_ip_sets: If True, also delete the IP sets. If False, keep them for future use.
            
        Returns:
            True if successful, False otherwise
        """
        scope_name = "API Gateway" if self.scope == "REGIONAL" else "CloudFront"
        log_info(f"Removing {scope_name} WAF IP restrictions...")
        
        # Find Web ACL
        web_acl = self.find_web_acl()
        if not web_acl:
            log_error("Web ACL not found. Please specify --web-acl-name")
            return False
        
        web_acl_id = web_acl['Id']
        web_acl_name = web_acl['Name']
        self.web_acl_name = web_acl_name
        
        log_info(f"Found Web ACL: {web_acl_name} (ID: {web_acl_id})")
        
        # Get current Web ACL configuration
        web_acl_details = self.get_web_acl_details(web_acl_id)
        if not web_acl_details:
            return False
        
        lock_token = web_acl_details['LockToken']
        current_rules = web_acl_details.get('Rules', [])
        custom_response_bodies = web_acl_details.get('CustomResponseBodies', {})
        
        # Remove IPAllowlist rule and restore USOnlyGeoMatch if it was removed
        # IMPORTANT: Preserve all existing rules exactly as they are - only remove IPAllowlist
        updated_rules = []
        allowlist_found = False
        geo_match_exists = False
        
        # Check if USOnlyGeoMatch already exists in current rules
        for rule in current_rules:
            if rule['Name'] == 'USOnlyGeoMatch':
                geo_match_exists = True
                break
        
        for rule in current_rules:
            if rule['Name'] == 'IPAllowlist':
                allowlist_found = True
                log_info("Found IPAllowlist rule, removing it...")
                # Skip this rule (don't add it to updated_rules)
            else:
                # Keep existing rule EXACTLY as it is (deep copy to avoid mutation)
                preserved_rule = copy.deepcopy(rule)
                updated_rules.append(preserved_rule)
        
        # Restore USOnlyGeoMatch rule if it was previously removed and doesn't exist now
        if not geo_match_exists:
            if self.removed_geo_match_rule:
                # Use stored copy if available
                log_info("Restoring USOnlyGeoMatch rule from stored copy...")
                restored_rule = copy.deepcopy(self.removed_geo_match_rule)
            else:
                # Create USOnlyGeoMatch rule from expected configuration
                # This handles the case where the script was run in a different session
                log_info("USOnlyGeoMatch rule not found - creating from expected configuration...")
                restored_rule = {
                    'Name': 'USOnlyGeoMatch',
                    'Priority': 0,
                    'Statement': {
                        'GeoMatchStatement': {
                            'CountryCodes': ['US']  # Only allow US IP addresses
                        }
                    },
                    'Action': {
                        'Allow': {}  # Allow requests from US
                    },
                    'VisibilityConfig': {
                        'SampledRequestsEnabled': True,
                        'CloudWatchMetricsEnabled': True,
                        'MetricName': 'USOnlyGeoMatch'
                    }
                }
            
            # Ensure it's at priority 0 (highest priority)
            restored_rule['Priority'] = 0
            # Adjust other rules' priorities if needed
            for rule in updated_rules:
                if rule.get('Priority') == 0:
                    # Move this rule to priority 1
                    rule['Priority'] = 1
                    log_info(f"Moved {rule.get('Name', 'unknown')} rule from priority 0 to priority 1")
            updated_rules.insert(0, restored_rule)
            log_success("USOnlyGeoMatch rule restored at priority 0")
        
        if not allowlist_found:
            log_warn("IPAllowlist rule not found - restrictions may already be removed")
        
        # Sort rules by priority to ensure correct order (important for AWS WAF)
        updated_rules.sort(key=lambda r: r.get('Priority', 999))
        
        log_info(f"Final rule order after removal:")
        for rule in updated_rules:
            print(f"  Priority {rule.get('Priority')}: {rule.get('Name')}")
        
        # Update Web ACL - remove rule and set default to Allow (with retry logic)
        max_retries = 5
        retry_delay = 2  # Start with 2 seconds
        
        for attempt in range(max_retries):
            try:
                # Get fresh lock token on retry (lock token may have changed)
                if attempt > 0:
                    log_info(f"Retrying Web ACL update (attempt {attempt + 1}/{max_retries})...")
                    fresh_details = self.get_web_acl_details(web_acl_id)
                    if fresh_details:
                        lock_token = fresh_details['LockToken']
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                
                log_info("Updating Web ACL to remove IP restrictions...")
                
                # Prepare update parameters
                update_params = {
                    'Scope': self.scope,
                    'Id': web_acl_id,
                    'Name': web_acl_name,
                    'LockToken': lock_token,
                    'DefaultAction': {
                        'Allow': {}  # Allow by default
                    },
                    'Rules': updated_rules,
                    'VisibilityConfig': web_acl_details['VisibilityConfig']
                }
                
                # Include custom response bodies if they exist (required for CloudFront WAF)
                if custom_response_bodies:
                    update_params['CustomResponseBodies'] = custom_response_bodies
                
                self.wafv2_client.update_web_acl(**update_params)
                
                log_success("IP restrictions removed from Web ACL!")
                
                # Clear stored geo match rule after successful restoration
                if not geo_match_exists and self.removed_geo_match_rule:
                    self.removed_geo_match_rule = None
                
                # Optionally delete IP sets
                if delete_ip_sets:
                    self._delete_ip_sets()
                
                return True
                
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                if error_code == 'WAFUnavailableEntityException' and attempt < max_retries - 1:
                    log_warn(f"WAF resource temporarily unavailable, will retry: {e}")
                    continue
                else:
                    log_error(f"Failed to remove IP restrictions: {e}")
                    return False
        
        log_error("Failed to remove IP restrictions after all retries")
        return False
    
    def _delete_ip_sets(self) -> None:
        """Delete IP sets if they exist."""
        try:
            response = self.wafv2_client.list_ip_sets(Scope=self.scope)
            ip_sets = response.get('IPSets', [])
            
            for ipset in ip_sets:
                if ipset['Name'] in [self.ipv4_ipset_name, self.ipv6_ipset_name]:
                    try:
                        get_response = self.wafv2_client.get_ip_set(
                            Scope=self.scope,
                            Id=ipset['Id'],
                            Name=ipset['Name']
                        )
                        lock_token = get_response['LockToken']
                        
                        self.wafv2_client.delete_ip_set(
                            Scope=self.scope,
                            Id=ipset['Id'],
                            Name=ipset['Name'],
                            LockToken=lock_token
                        )
                        log_success(f"Deleted IP set: {ipset['Name']}")
                    except ClientError as e:
                        log_warn(f"Failed to delete IP set {ipset['Name']}: {e}")
        except ClientError as e:
            log_warn(f"Failed to list IP sets for deletion: {e}")


def show_interactive_menu() -> str:
    """
    Display interactive menu and get user choice.
    
    Returns:
        User's choice: '1', '2', '3', or 'q'
    """
    print()
    print("=" * 60)
    print("WAF IP Restriction Configuration")
    print("=" * 60)
    print()
    print("What would you like to do?")
    print()
    print("  1. Configure IP restrictions (lockdown)")
    print("  2. Remove IP restrictions (undo lockdown)")
    print("  3. Exit")
    print()
    
    while True:
        try:
            choice = input("Enter your choice (1-3): ").strip()
            if choice in ['1', '2', '3', 'q', 'Q']:
                return choice
            else:
                print("Invalid choice. Please enter 1, 2, 3, or 'q' to quit.")
        except KeyboardInterrupt:
            print()
            log_info("Cancelled by user")
            sys.exit(0)
        except EOFError:
            return '3'


def prompt_for_remove_options() -> tuple[bool, bool, bool]:
    """
    Prompt user for options when removing restrictions.
    
    Returns:
        Tuple of (delete_ip_sets, api_only, cloudfront_only)
    """
    print()
    print("Which WAFs should be affected?")
    print("  1. Both API Gateway and CloudFront (default)")
    print("  2. API Gateway only")
    print("  3. CloudFront only")
    print()
    
    waf_choice = input("Enter choice (1-3, default: 1): ").strip() or "1"
    
    api_only = False
    cloudfront_only = False
    
    if waf_choice == "2":
        api_only = True
    elif waf_choice == "3":
        cloudfront_only = True
    
    print()
    print("Delete IP sets?")
    print("  - Yes: IP sets will be deleted (cannot reuse later)")
    print("  - No: IP sets will be kept (can reuse for future restrictions)")
    print()
    
    delete_choice = input("Delete IP sets? (y/N): ").strip().lower()
    delete_ip_sets = delete_choice in ['y', 'yes']
    
    return delete_ip_sets, api_only, cloudfront_only


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Configure WAF IP allowlist restrictions for complete lockdown (API Gateway + CloudFront)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode - applies to BOTH API Gateway and CloudFront
  python configure_ip_restriction.py
  
  # Auto-detect current IP - applies to BOTH
  python configure_ip_restriction.py --auto-detect-ip
  
  # Specify IPs via command line - applies to BOTH
  python configure_ip_restriction.py --ips "203.0.113.1/32,198.51.100.1/32"
  
  # Only restrict API Gateway (not CloudFront)
  python configure_ip_restriction.py --api-only --ips "203.0.113.1/32"
  
  # Only restrict CloudFront (not API Gateway)
  python configure_ip_restriction.py --cloudfront-only --ips "203.0.113.1/32"
  
  # Remove IP restrictions (undo lockdown)
  python configure_ip_restriction.py --remove-restrictions
  
  # Remove restrictions and delete IP sets
  python configure_ip_restriction.py --remove-restrictions --delete-ip-sets
  
  # Remove only from API Gateway
  python configure_ip_restriction.py --remove-restrictions --api-only
        """
    )
    parser.add_argument(
        '--ips',
        type=str,
        help='Comma-separated list of IP addresses in CIDR format (e.g., "203.0.113.1/32,198.51.100.1/32")'
    )
    parser.add_argument(
        '--auto-detect-ip',
        action='store_true',
        help='Automatically detect and use current public IP address'
    )
    parser.add_argument(
        '--api-only',
        action='store_true',
        help='Only restrict API Gateway WAF (not CloudFront)'
    )
    parser.add_argument(
        '--cloudfront-only',
        action='store_true',
        help='Only restrict CloudFront WAF (not API Gateway)'
    )
    parser.add_argument(
        '--api-web-acl-name',
        type=str,
        help='Name of the API Gateway Web ACL (will auto-detect if not specified)'
    )
    parser.add_argument(
        '--cloudfront-web-acl-name',
        type=str,
        help='Name of the CloudFront Web ACL (will auto-detect if not specified)'
    )
    parser.add_argument(
        '--region',
        type=str,
        default=AWS_REGION,
        help=f'AWS region for API Gateway (default: {AWS_REGION}, CloudFront always uses us-east-1)'
    )
    parser.add_argument(
        '--remove-restrictions',
        action='store_true',
        help='Remove IP restrictions (delete IPAllowlist rule and set default action to Allow)'
    )
    parser.add_argument(
        '--delete-ip-sets',
        action='store_true',
        help='Also delete IP sets when removing restrictions (only used with --remove-restrictions)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.api_only and args.cloudfront_only:
        log_error("Cannot specify both --api-only and --cloudfront-only")
        sys.exit(1)
    
    # Interactive menu mode (when no arguments provided)
    if not any([args.ips, args.auto_detect_ip, args.remove_restrictions]):
        choice = show_interactive_menu()
        
        if choice in ['3', 'q', 'Q']:
            log_info("Exiting...")
            sys.exit(0)
        elif choice == '2':
            # Remove restrictions mode
            args.remove_restrictions = True
            delete_ip_sets, api_only, cloudfront_only = prompt_for_remove_options()
            args.delete_ip_sets = delete_ip_sets
            if api_only:
                args.api_only = True
            elif cloudfront_only:
                args.cloudfront_only = True
        # choice == '1' continues to normal configuration flow
    
    # Determine which WAFs to configure
    configure_api = not args.cloudfront_only
    configure_cloudfront = not args.api_only
    
    if not configure_api and not configure_cloudfront:
        log_error("No WAFs to configure")
        sys.exit(1)
    
    # Handle remove/undo mode
    if args.remove_restrictions:
        log_info("")
        log_info("=" * 60)
        log_info("REMOVING IP RESTRICTIONS")
        log_info("=" * 60)
        log_warn("This will remove IP restrictions and allow all traffic")
        print()
        
        # Remove from API Gateway WAF
        api_success = True
        if configure_api:
            log_info("")
            log_info("=" * 60)
            log_info("Removing API Gateway WAF IP restrictions (REGIONAL scope)")
            log_info("=" * 60)
            api_configurator = WAFIPRestrictionConfigurator(
                scope="REGIONAL",
                region=args.region,
                web_acl_name=args.api_web_acl_name,
                web_acl_name_pattern="ApiGatewayWebACL",
                ipv4_ipset_name=API_IPV4_IPSET_NAME,
                ipv6_ipset_name=API_IPV6_IPSET_NAME,
            )
            api_success = api_configurator.remove_ip_restrictions(delete_ip_sets=args.delete_ip_sets)
        
        # Remove from CloudFront WAF
        cf_success = True
        if configure_cloudfront:
            log_info("")
            log_info("=" * 60)
            log_info("Removing CloudFront WAF IP restrictions (CLOUDFRONT scope)")
            log_info("=" * 60)
            cf_configurator = WAFIPRestrictionConfigurator(
                scope="CLOUDFRONT",
                region="us-east-1",
                web_acl_name=args.cloudfront_web_acl_name,
                web_acl_name_pattern="CloudFrontWebACL",
                ipv4_ipset_name=CF_IPV4_IPSET_NAME,
                ipv6_ipset_name=CF_IPV6_IPSET_NAME,
            )
            cf_success = cf_configurator.remove_ip_restrictions(delete_ip_sets=args.delete_ip_sets)
        
        # Final summary for remove mode
        print()
        print("=" * 60)
        log_success("Removal Summary")
        print("=" * 60)
        print()
        print("WAF Configuration:")
        if configure_api:
            status = "✅ Removed" if api_success else "❌ Failed"
            print(f"  {status} API Gateway WAF (REGIONAL scope)")
        if configure_cloudfront:
            status = "✅ Removed" if cf_success else "❌ Failed"
            print(f"  {status} CloudFront WAF (CLOUDFRONT scope)")
        print()
        print("Settings:")
        print(f"  ✅ Default action: Allow")
        print(f"  ✅ IPAllowlist rule: Removed")
        if args.delete_ip_sets:
            print(f"  ✅ IP sets: Deleted")
        else:
            print(f"  ℹ️  IP sets: Kept (can be reused)")
        print()
        log_warn("Note: WAF rule changes may take 2-3 minutes to propagate.")
        print()
        
        # Start propagation timer
        start_propagation_timer()
        
        overall_success = (not configure_api or api_success) and (not configure_cloudfront or cf_success)
        sys.exit(0 if overall_success else 1)
    
    # Normal configuration mode
    # Determine IP addresses
    ipv4_addresses = []
    ipv6_addresses = []
    
    if args.auto_detect_ip:
        current_ip = detect_current_ip()
        if current_ip:
            # Add /32 for single IP
            if '/' not in current_ip:
                current_ip = f"{current_ip}/32"
            ipv4_addresses.append(current_ip)
            log_info(f"Auto-detected IP: {current_ip}")
        else:
            log_error("Could not auto-detect IP address")
            sys.exit(1)
    elif args.ips:
        ipv4_addresses, ipv6_addresses = parse_ip_addresses(args.ips)
        if not ipv4_addresses and not ipv6_addresses:
            log_error("No valid IP addresses provided")
            sys.exit(1)
    else:
        # Interactive mode - prompt for IPs
        log_info("Interactive mode: Please enter allowed IP addresses")
        ipv4_addresses, ipv6_addresses = prompt_for_ips()
    
    # Configure API Gateway WAF
    api_success = True
    if configure_api:
        log_info("")
        log_info("=" * 60)
        log_info("Configuring API Gateway WAF (REGIONAL scope)")
        log_info("=" * 60)
        api_configurator = WAFIPRestrictionConfigurator(
            scope="REGIONAL",
            region=args.region,
            web_acl_name=args.api_web_acl_name,
            web_acl_name_pattern="ApiGatewayWebACL",
            ipv4_ipset_name=API_IPV4_IPSET_NAME,
            ipv6_ipset_name=API_IPV6_IPSET_NAME,
        )
        api_success = api_configurator.configure(ipv4_addresses, ipv6_addresses)
    
    # Configure CloudFront WAF
    cf_success = True
    if configure_cloudfront:
        log_info("")
        log_info("=" * 60)
        log_info("Configuring CloudFront WAF (CLOUDFRONT scope)")
        log_info("=" * 60)
        cf_configurator = WAFIPRestrictionConfigurator(
            scope="CLOUDFRONT",
            region="us-east-1",  # CloudFront WAF must be in us-east-1
            web_acl_name=args.cloudfront_web_acl_name,
            web_acl_name_pattern="CloudFrontWebACL",
            ipv4_ipset_name=CF_IPV4_IPSET_NAME,
            ipv6_ipset_name=CF_IPV6_IPSET_NAME,
        )
        cf_success = cf_configurator.configure(ipv4_addresses, ipv6_addresses)
    
    # Final summary
    print()
    print("=" * 60)
    log_success("Configuration Summary")
    print("=" * 60)
    print()
    print("Allowed IP addresses:")
    if ipv4_addresses:
        print(f"  ✅ IPv4: {', '.join(ipv4_addresses)}")
    if ipv6_addresses:
        print(f"  ✅ IPv6: {', '.join(ipv6_addresses)}")
    print()
    print("WAF Configuration:")
    if configure_api:
        status = "✅ Configured" if api_success else "❌ Failed"
        print(f"  {status} API Gateway WAF (REGIONAL scope)")
    if configure_cloudfront:
        status = "✅ Configured" if cf_success else "❌ Failed"
        print(f"  {status} CloudFront WAF (CLOUDFRONT scope)")
    print()
    print("Settings:")
    print(f"  ✅ Default action: Block")
    print(f"  ✅ Allowlist rule priority: 0 (highest)")
    print()
    log_warn("Note: WAF rule changes may take 2-3 minutes to propagate.")
    print()
    
    # Start propagation timer
    start_propagation_timer()
    
    # Exit with error if any configuration failed
    overall_success = (not configure_api or api_success) and (not configure_cloudfront or cf_success)
    sys.exit(0 if overall_success else 1)


if __name__ == '__main__':
    main()

