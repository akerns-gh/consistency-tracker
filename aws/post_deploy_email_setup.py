#!/usr/bin/env python3
"""
Post-deploy email domain setup automation.

Integrates email_domain_setup.py into the deployment process.
Reads configuration from aws/app.py and aws/email_tools/config.json.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Optional

# Add parent directory to path to read app.py directly
# We can't import app.py because it imports aws_cdk which conflicts with email module
def get_defaults() -> Dict:
    """Get default values from app.py by reading it directly."""
    aws_dir = Path(__file__).parent
    app_py = aws_dir / 'app.py'
    
    defaults = {
        'domain': 'repwarrior.net',
        'aws_region': 'us-east-1',
        'hosted_zone_id': None,
        'mail_subdomain': 'mail'
    }
    
    # Try to read values from app.py without importing
    if app_py.exists():
        try:
            with open(app_py, 'r') as f:
                content = f.read()
                # Extract DOMAIN_NAME
                import re
                domain_match = re.search(r'DOMAIN_NAME\s*=\s*["\']([^"\']+)["\']', content)
                if domain_match:
                    defaults['domain'] = domain_match.group(1)
                
                # Extract AWS_REGION
                region_match = re.search(r'AWS_REGION\s*=\s*["\']([^"\']+)["\']', content)
                if region_match:
                    defaults['aws_region'] = region_match.group(1)
                
                # Extract HOSTED_ZONE_ID
                zone_match = re.search(r'HOSTED_ZONE_ID\s*=\s*["\']([^"\']+)["\']', content)
                if zone_match:
                    defaults['hosted_zone_id'] = zone_match.group(1)
        except Exception:
            # If we can't read app.py, use defaults
            pass
    
    return defaults


def load_config(config_path: Path) -> Optional[Dict]:
    """Load configuration from JSON file."""
    if not config_path.exists():
        return None
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"⚠️  Error reading config file: {e}")
        return None


def validate_proton_config(config: Dict) -> bool:
    """Check if Proton Mail configuration is complete."""
    proton = config.get('proton', {})
    
    if not proton.get('verification'):
        return False
    
    dkim = proton.get('dkim', [])
    if len(dkim) != 3:
        return False
    
    for dkim_record in dkim:
        if 'CHANGEME' in dkim_record.get('value', ''):
            return False
    
    if 'CHANGEME' in proton.get('verification', ''):
        return False
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Post-deploy email domain setup (SES + Proton Mail)"
    )
    parser.add_argument(
        '--skip-if-no-config',
        action='store_true',
        help='Skip silently if config.json does not exist'
    )
    parser.add_argument(
        '--domain',
        help='Override domain name (defaults to app.py DOMAIN_NAME)'
    )
    parser.add_argument(
        '--region',
        help='Override AWS region (defaults to app.py AWS_REGION)'
    )
    parser.add_argument(
        '--hosted-zone-id',
        help='Override hosted zone ID (defaults to app.py HOSTED_ZONE_ID)'
    )
    args = parser.parse_args()
    
    # Get script directory
    aws_dir = Path(__file__).parent
    # Use email_tools directory to avoid shadowing Python's built-in email module
    email_dir = aws_dir / 'email_tools'
    config_path = email_dir / 'config.json'
    
    # Get defaults from app.py
    defaults = get_defaults()
    
    # Override with CLI arguments
    if args.domain:
        defaults['domain'] = args.domain
    if args.region:
        defaults['aws_region'] = args.region
    if args.hosted_zone_id:
        defaults['hosted_zone_id'] = args.hosted_zone_id
    
    # Load config file
    file_config = load_config(config_path)
    
    if not file_config:
        if args.skip_if_no_config:
            print("ℹ️  Email setup skipped (config.json not found)")
            return 0
        else:
            print("=" * 70)
            print("📧 EMAIL DOMAIN SETUP")
            print("=" * 70)
            print("\n⚠️  Configuration file not found: aws/email_tools/config.json")
            print("\nTo set up email domain configuration:")
            print("  1. Copy aws/email_tools/config.template.json to aws/email_tools/config.json")
            print("  2. Collect Proton Mail DNS values (see aws/email_tools/README.md)")
            print("  3. Fill in the Proton values in config.json")
            print("  4. Re-run this script or deploy again")
            print("\n💡 This step is optional and can be done manually later.")
            return 0
    
    # Merge configs (file config overrides defaults)
    config = {**defaults, **file_config}
    
    # Validate Proton configuration
    if not validate_proton_config(config):
        print("=" * 70)
        print("📧 EMAIL DOMAIN SETUP")
        print("=" * 70)
        print("\n⚠️  Proton Mail configuration is incomplete or contains placeholders")
        print("\nPlease update aws/email_tools/config.json with your Proton Mail DNS values:")
        print("  - proton.verification")
        print("  - proton.dkim[0-2] (3 records)")
        print("  - proton.dmarc")
        print("\nSee aws/email_tools/README.md for instructions on collecting these values.")
        return 1
    
    # Run the email setup script directly to avoid import conflicts with Python's built-in email module
    # We'll call the main() function from email_domain_setup.py by executing it as a script
    email_setup_script = email_dir / 'email_domain_setup.py'
    if not email_setup_script.exists():
        print(f"❌ Email setup script not found: {email_setup_script}")
        return 1
    
    # Use subprocess to run the script in a clean environment
    import subprocess
    import os
    
    print("=" * 70)
    print("📧 EMAIL DOMAIN SETUP")
    print("=" * 70)
    print(f"\n🌐 Domain: {config['domain']}")
    print(f"📍 Region: {config['aws_region']}")
    print(f"📋 Config: {config_path}")
    print()
    
    # Run the script directly - it will read from config.json
    try:
        result = subprocess.run(
            [sys.executable, str(email_setup_script)],
            cwd=str(email_dir),
            check=False,
            capture_output=False
        )
        return result.returncode
    except Exception as e:
        print(f"❌ Error running email setup: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

