#!/usr/bin/env python3
"""
Email Domain Setup Automation Script
Automates Route 53 and Amazon SES configuration for dual email setup:
- Proton Mail for receiving/personal email
- Amazon SES for application email sending

Prerequisites:
- AWS credentials configured (aws configure)
- boto3 installed (pip install boto3 --break-system-packages)
- Proton Mail DNS values collected manually
"""

import boto3
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from botocore.exceptions import ClientError


class EmailDomainSetup:
    def __init__(self, domain: str, region: str = 'us-east-1'):
        """
        Initialize the email domain setup automation.
        
        Args:
            domain: Your domain name (e.g., 'example.com')
            region: AWS region for SES (default: us-east-1)
        """
        self.domain = domain
        self.region = region
        self.ses_client = boto3.client('ses', region_name=region)
        self.route53_client = boto3.client('route53')
        self.hosted_zone_id = None
        
    def find_hosted_zone(self) -> Optional[str]:
        """Find the Route 53 hosted zone ID for the domain."""
        print(f"\n🔍 Finding Route 53 hosted zone for {self.domain}...")
        
        try:
            response = self.route53_client.list_hosted_zones()
            
            for zone in response['HostedZones']:
                # Remove trailing dot from zone name for comparison
                zone_name = zone['Name'].rstrip('.')
                if zone_name == self.domain:
                    self.hosted_zone_id = zone['Id'].split('/')[-1]
                    print(f"✅ Found hosted zone: {self.hosted_zone_id}")
                    return self.hosted_zone_id
                    
            print(f"❌ No hosted zone found for {self.domain}")
            return None
            
        except ClientError as e:
            print(f"❌ Error finding hosted zone: {e}")
            return None
    
    def get_existing_records(self) -> Dict[str, List]:
        """Get existing DNS records to avoid duplicates."""
        if not self.hosted_zone_id:
            return {}
            
        try:
            response = self.route53_client.list_resource_record_sets(
                HostedZoneId=self.hosted_zone_id
            )
            
            records = {}
            for record in response['ResourceRecordSets']:
                key = f"{record['Name']}:{record['Type']}"
                records[key] = record
                
            return records
            
        except ClientError as e:
            print(f"⚠️  Error getting existing records: {e}")
            return {}
    
    def create_route53_record(self, name: str, record_type: str, 
                            values: List[str], ttl: int = 300,
                            action: str = 'UPSERT') -> bool:
        """
        Create or update a Route 53 DNS record.
        
        Args:
            name: Record name (e.g., '', 'mail', '_dmarc')
            record_type: DNS record type (MX, TXT, CNAME, etc.)
            values: List of record values
            ttl: Time to live in seconds
            action: UPSERT (create/update), CREATE, or DELETE
        """
        if not self.hosted_zone_id:
            print("❌ No hosted zone ID available")
            return False
            
        # Construct full record name
        if name:
            full_name = f"{name}.{self.domain}."
        else:
            full_name = f"{self.domain}."
        
        # Format values based on record type
        if record_type == 'TXT':
            # TXT records need to be quoted
            formatted_values = [{'Value': f'"{v}"'} for v in values]
        elif record_type == 'MX':
            # MX records are already in "priority server" format
            formatted_values = [{'Value': v} for v in values]
        elif record_type == 'CNAME':
            # CNAME values should end with a dot
            formatted_values = [{'Value': v if v.endswith('.') else f"{v}."} for v in values]
        else:
            formatted_values = [{'Value': v} for v in values]
        
        change_batch = {
            'Changes': [{
                'Action': action,
                'ResourceRecordSet': {
                    'Name': full_name,
                    'Type': record_type,
                    'TTL': ttl,
                    'ResourceRecords': formatted_values
                }
            }]
        }
        
        try:
            response = self.route53_client.change_resource_record_sets(
                HostedZoneId=self.hosted_zone_id,
                ChangeBatch=change_batch
            )
            
            print(f"✅ {action} {record_type} record: {name or '@'}")
            return True
            
        except ClientError as e:
            if 'it already exists' in str(e):
                print(f"ℹ️  {record_type} record already exists: {name or '@'}")
                return True
            else:
                print(f"❌ Error creating {record_type} record {name or '@'}: {e}")
                return False
    
    def setup_proton_dns(self, proton_values: Dict) -> bool:
        """
        Set up Proton Mail DNS records.
        
        Args:
            proton_values: Dictionary containing Proton DNS values
                {
                    'verification': 'protonmail-verification=xxxxx',
                    'mx': ['10 mail.protonmail.ch', '20 mailsec.protonmail.ch'],  # Optional
                    'spf': 'v=spf1 include:_spf.protonmail.ch mx ~all',  # Optional
                    'dkim': [
                        {'host': 'protonmail._domainkey', 'value': 'xxx.proton.ch.'},
                        {'host': 'protonmail2._domainkey', 'value': 'xxx.proton.ch.'},
                        {'host': 'protonmail3._domainkey', 'value': 'xxx.proton.ch.'}
                    ],
                    'dmarc': 'v=DMARC1; p=quarantine; ...'
                }
        """
        print("\n📧 Setting up Proton Mail DNS records...")
        
        success = True
        
        # 1. Verification TXT record
        if 'verification' in proton_values:
            success &= self.create_route53_record(
                name='',
                record_type='TXT',
                values=[proton_values['verification']]
            )
        
        # 2. MX records (use config or defaults)
        mx_values = proton_values.get('mx', [
            '10 mail.protonmail.ch',
            '20 mailsec.protonmail.ch'
        ])
        success &= self.create_route53_record(
            name='',
            record_type='MX',
            values=mx_values
        )
        
        # 3. SPF record (use config or default)
        # Default includes both Proton Mail and Amazon SES for dual email setup
        spf_value = proton_values.get('spf', 'v=spf1 include:_spf.protonmail.ch include:amazonses.com mx ~all')
        success &= self.create_route53_record(
            name='',
            record_type='TXT',
            values=[spf_value]
        )
        
        # 4. DKIM records
        if 'dkim' in proton_values:
            for dkim in proton_values['dkim']:
                success &= self.create_route53_record(
                    name=dkim['host'],
                    record_type='CNAME',
                    values=[dkim['value']]
                )
        
        # 5. DMARC record
        if 'dmarc' in proton_values:
            success &= self.create_route53_record(
                name='_dmarc',
                record_type='TXT',
                values=[proton_values['dmarc']]
            )
        
        return success
    
    def setup_ses_domain(self, mail_subdomain: str = 'mail') -> bool:
        """
        Set up SES domain verification and custom MAIL FROM domain.
        
        Args:
            mail_subdomain: Subdomain for custom MAIL FROM (e.g., 'mail' or 'bounce')
        """
        print(f"\n📨 Setting up Amazon SES for {self.domain}...")
        
        try:
            # 1. Verify domain identity
            print(f"  → Verifying domain in SES...")
            response = self.ses_client.verify_domain_identity(Domain=self.domain)
            verification_token = response['VerificationToken']
            print(f"  ✅ Domain verification initiated")
            print(f"     Verification token: {verification_token}")
            
            # 2. Enable Easy DKIM
            print(f"  → Enabling Easy DKIM...")
            dkim_response = self.ses_client.verify_domain_dkim(Domain=self.domain)
            dkim_tokens = dkim_response['DkimTokens']
            print(f"  ✅ DKIM enabled with {len(dkim_tokens)} tokens")
            
            # 3. Add DKIM CNAME records to Route 53
            print(f"  → Adding DKIM records to Route 53...")
            for token in dkim_tokens:
                self.create_route53_record(
                    name=f"{token}._domainkey",
                    record_type='CNAME',
                    values=[f"{token}.dkim.amazonses.com"]
                )
            
            # 4. Set up custom MAIL FROM domain
            mail_from_domain = f"{mail_subdomain}.{self.domain}"
            print(f"  → Setting up custom MAIL FROM domain: {mail_from_domain}...")
            
            self.ses_client.set_identity_mail_from_domain(
                Identity=self.domain,
                MailFromDomain=mail_from_domain,
                BehaviorOnMXFailure='UseDefaultValue'
            )
            
            # 5. Add MX record for MAIL FROM subdomain
            mx_value = f"10 feedback-smtp.{self.region}.amazonses.com"
            self.create_route53_record(
                name=mail_subdomain,
                record_type='MX',
                values=[mx_value]
            )
            
            # 6. Add SPF record for MAIL FROM subdomain
            spf_value = 'v=spf1 include:amazonses.com ~all'
            self.create_route53_record(
                name=mail_subdomain,
                record_type='TXT',
                values=[spf_value]
            )
            
            print(f"✅ SES setup complete for {self.domain}")
            return True
            
        except ClientError as e:
            print(f"❌ Error setting up SES: {e}")
            return False
    
    def verify_ses_status(self) -> Dict:
        """Check SES domain verification and DKIM status."""
        print(f"\n🔍 Checking SES verification status...")
        
        try:
            # Check domain verification
            verification = self.ses_client.get_identity_verification_attributes(
                Identities=[self.domain]
            )
            
            # Check DKIM status
            dkim = self.ses_client.get_identity_dkim_attributes(
                Identities=[self.domain]
            )
            
            domain_status = verification['VerificationAttributes'].get(self.domain, {})
            dkim_status = dkim['DkimAttributes'].get(self.domain, {})
            
            status = {
                'domain_verified': domain_status.get('VerificationStatus') == 'Success',
                'dkim_enabled': dkim_status.get('DkimEnabled', False),
                'dkim_verified': dkim_status.get('DkimVerificationStatus') == 'Success'
            }
            
            print(f"  Domain verification: {'✅' if status['domain_verified'] else '⏳ Pending'}")
            print(f"  DKIM enabled: {'✅' if status['dkim_enabled'] else '❌'}")
            print(f"  DKIM verified: {'✅' if status['dkim_verified'] else '⏳ Pending'}")
            
            return status
            
        except ClientError as e:
            print(f"❌ Error checking SES status: {e}")
            return {}
    
    def wait_for_dns_propagation(self, max_wait: int = 300) -> bool:
        """
        Wait for DNS records to propagate.
        
        Args:
            max_wait: Maximum seconds to wait
        """
        print(f"\n⏳ Waiting for DNS propagation (max {max_wait}s)...")
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            time.sleep(30)
            elapsed = int(time.time() - start_time)
            print(f"  ... {elapsed}s elapsed")
            
            status = self.verify_ses_status()
            if status.get('domain_verified') and status.get('dkim_verified'):
                print("✅ DNS records propagated and verified!")
                return True
        
        print("⏳ DNS propagation may still be in progress. Check back in a few minutes.")
        return False
    
    def print_summary(self):
        """Print configuration summary."""
        print("\n" + "="*70)
        print("📋 EMAIL DOMAIN SETUP SUMMARY")
        print("="*70)
        print(f"\n🌐 Domain: {self.domain}")
        print(f"📍 AWS Region: {self.region}")
        print(f"🆔 Route 53 Zone: {self.hosted_zone_id}")
        
        print("\n📧 EMAIL FLOW:")
        print("  Incoming mail → Route 53 (MX) → Proton Mail")
        print("  Outgoing personal → Proton Mail → Internet")
        print(f"  Outgoing app → Amazon SES → Internet (via mail.{self.domain})")
        
        print("\n✅ NEXT STEPS:")
        print("  1. Check Proton Mail for green verification checkmarks")
        print("  2. Create email addresses in Proton Mail")
        print("  3. Request SES production access (if needed)")
        print("  4. Test email sending/receiving")
        print("  5. Configure your application to use SES")
        
        print("\n🔗 USEFUL LINKS:")
        print(f"  • SES Console: https://{self.region}.console.aws.amazon.com/ses/")
        print(f"  • Route 53: https://console.aws.amazon.com/route53/")
        print("  • Proton Mail: https://mail.proton.me/")
        print("  • Mail Tester: https://www.mail-tester.com/")
        print("\n" + "="*70 + "\n")


def main():
    """Main execution function."""
    
    print("="*70)
    print("🚀 EMAIL DOMAIN SETUP AUTOMATION")
    print("="*70)
    
    # Try to load config from JSON file first
    script_dir = Path(__file__).parent
    config_path = script_dir / 'config.json'
    
    config = {}
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            print(f"✅ Loaded configuration from {config_path}")
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  Could not load config file: {e}")
            print("   Using defaults or command-line arguments")
    
    # Configuration with defaults
    DOMAIN = config.get('domain', 'yourdomain.com')
    AWS_REGION = config.get('aws_region', 'us-east-1')
    MAIL_SUBDOMAIN = config.get('mail_subdomain', 'mail')
    HOSTED_ZONE_ID = config.get('hosted_zone_id')
    
    # Proton Mail DNS values - from config or defaults
    PROTON_VALUES = config.get('proton', {
        'verification': 'protonmail-verification=CHANGEME',
        'dkim': [
            {'host': 'protonmail._domainkey', 'value': 'CHANGEME.domains.proton.ch.'},
            {'host': 'protonmail2._domainkey', 'value': 'CHANGEME.domains.proton.ch.'},
            {'host': 'protonmail3._domainkey', 'value': 'CHANGEME.domains.proton.ch.'}
        ],
        'dmarc': 'v=DMARC1; p=quarantine; rua=mailto:CHANGEME@protonmail.com'
    })
    
    # Validation
    if 'CHANGEME' in str(PROTON_VALUES) or DOMAIN == 'yourdomain.com':
        print("\n❌ ERROR: Please update the configuration values!")
        if not config_path.exists():
            print(f"   1. Copy {script_dir / 'config.template.json'} to {config_path}")
        print("   2. Set domain in config.json")
        print("   3. Collect Proton DNS values and update config.json")
        print("   4. Run the script again")
        return
    
    # Initialize setup
    setup = EmailDomainSetup(domain=DOMAIN, region=AWS_REGION)
    
    # Find hosted zone
    if HOSTED_ZONE_ID:
        setup.hosted_zone_id = HOSTED_ZONE_ID
        print(f"✅ Using provided hosted zone ID: {HOSTED_ZONE_ID}")
    elif not setup.find_hosted_zone():
        print(f"\n❌ Please create a Route 53 hosted zone for {DOMAIN} first")
        print("   Or provide hosted_zone_id in config.json")
        return
    
    # Setup Proton DNS
    print("\n" + "="*70)
    print("STEP 1: PROTON MAIL DNS SETUP")
    print("="*70)
    proton_success = setup.setup_proton_dns(PROTON_VALUES)
    
    # Setup SES
    print("\n" + "="*70)
    print("STEP 2: AMAZON SES SETUP")
    print("="*70)
    ses_success = setup.setup_ses_domain(mail_subdomain=MAIL_SUBDOMAIN)
    
    # Verify status
    print("\n" + "="*70)
    print("STEP 3: VERIFICATION")
    print("="*70)
    setup.verify_ses_status()
    
    # Print summary
    setup.print_summary()
    
    if proton_success and ses_success:
        print("✅ Setup completed successfully!")
    else:
        print("⚠️  Setup completed with some errors. Check logs above.")


if __name__ == '__main__':
    main()
