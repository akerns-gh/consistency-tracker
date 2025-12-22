#!/usr/bin/env python3
"""
Email Domain Verification Script
Checks the status of your email domain configuration.
"""

import boto3
import dns.resolver
import json
from typing import Dict, List
from botocore.exceptions import ClientError


class EmailDomainVerifier:
    def __init__(self, domain: str, region: str = 'us-east-1'):
        self.domain = domain
        self.region = region
        self.ses_client = boto3.client('ses', region_name=region)
        
    def check_mx_records(self) -> Dict:
        """Check MX records for the domain."""
        print(f"\n🔍 Checking MX records for {self.domain}...")
        
        try:
            answers = dns.resolver.resolve(self.domain, 'MX')
            mx_records = []
            
            for rdata in answers:
                mx_records.append({
                    'priority': rdata.preference,
                    'server': str(rdata.exchange).rstrip('.')
                })
            
            # Sort by priority
            mx_records.sort(key=lambda x: x['priority'])
            
            # Check for Proton
            proton_found = any('protonmail.ch' in r['server'] for r in mx_records)
            
            print("  📬 MX Records found:")
            for mx in mx_records:
                icon = "✅" if 'protonmail' in mx['server'] else "  "
                print(f"    {icon} Priority {mx['priority']}: {mx['server']}")
            
            return {
                'exists': True,
                'records': mx_records,
                'proton_configured': proton_found
            }
            
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer) as e:
            print(f"  ❌ No MX records found")
            return {'exists': False}
    
    def check_spf_record(self) -> Dict:
        """Check SPF records."""
        print(f"\n🔍 Checking SPF record for {self.domain}...")
        
        try:
            answers = dns.resolver.resolve(self.domain, 'TXT')
            spf_records = []
            
            for rdata in answers:
                txt_value = str(rdata).strip('"')
                if txt_value.startswith('v=spf1'):
                    spf_records.append(txt_value)
            
            if not spf_records:
                print("  ❌ No SPF record found")
                return {'exists': False}
            
            if len(spf_records) > 1:
                print("  ⚠️  WARNING: Multiple SPF records found (this breaks SPF!)")
            
            for spf in spf_records:
                print(f"  📝 SPF: {spf}")
                
                # Check for Proton
                if '_spf.protonmail.ch' in spf:
                    print("    ✅ Proton Mail authorized")
                else:
                    print("    ⚠️  Proton Mail NOT authorized")
                
                # Check for SES
                if 'amazonses.com' in spf:
                    print("    ✅ Amazon SES authorized")
            
            return {
                'exists': True,
                'records': spf_records,
                'multiple': len(spf_records) > 1
            }
            
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            print("  ❌ No SPF record found")
            return {'exists': False}
    
    def check_dkim_records(self) -> Dict:
        """Check DKIM records for both Proton and SES."""
        print(f"\n🔍 Checking DKIM records...")
        
        results = {'proton': [], 'ses': []}
        
        # Check Proton DKIM (we know the names)
        print("  📧 Proton DKIM:")
        for i in ['', '2', '3']:
            selector = f"protonmail{i}._domainkey.{self.domain}"
            try:
                answers = dns.resolver.resolve(selector, 'CNAME')
                value = str(answers[0]).rstrip('.')
                print(f"    ✅ {selector}")
                results['proton'].append(selector)
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                print(f"    ❌ {selector} NOT FOUND")
        
        # We can't easily check SES DKIM without knowing the tokens
        # But we can check via SES API
        print("  📨 SES DKIM:")
        try:
            response = self.ses_client.get_identity_dkim_attributes(
                Identities=[self.domain]
            )
            
            dkim_attrs = response['DkimAttributes'].get(self.domain, {})
            if dkim_attrs.get('DkimEnabled'):
                status = dkim_attrs.get('DkimVerificationStatus', 'Unknown')
                tokens = dkim_attrs.get('DkimTokens', [])
                
                if status == 'Success':
                    print(f"    ✅ DKIM verified ({len(tokens)} tokens)")
                    results['ses'] = tokens
                else:
                    print(f"    ⏳ DKIM status: {status}")
            else:
                print("    ❌ DKIM not enabled")
                
        except ClientError:
            print("    ⚠️  Cannot check SES DKIM (domain may not be verified in SES)")
        
        return results
    
    def check_dmarc_record(self) -> Dict:
        """Check DMARC record."""
        print(f"\n🔍 Checking DMARC record...")
        
        try:
            answers = dns.resolver.resolve(f'_dmarc.{self.domain}', 'TXT')
            
            for rdata in answers:
                dmarc = str(rdata).strip('"')
                if dmarc.startswith('v=DMARC1'):
                    print(f"  ✅ DMARC record found:")
                    print(f"     {dmarc}")
                    
                    # Parse policy
                    if 'p=none' in dmarc:
                        print("     ⚠️  Policy: none (monitoring only)")
                    elif 'p=quarantine' in dmarc:
                        print("     ✅ Policy: quarantine (recommended)")
                    elif 'p=reject' in dmarc:
                        print("     ✅ Policy: reject (strictest)")
                    
                    return {'exists': True, 'value': dmarc}
            
            print("  ❌ No valid DMARC record found")
            return {'exists': False}
            
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            print("  ❌ No DMARC record found")
            return {'exists': False}
    
    def check_ses_status(self) -> Dict:
        """Check SES domain verification status."""
        print(f"\n🔍 Checking Amazon SES status...")
        
        try:
            # Domain verification
            verification = self.ses_client.get_identity_verification_attributes(
                Identities=[self.domain]
            )
            
            # DKIM status
            dkim = self.ses_client.get_identity_dkim_attributes(
                Identities=[self.domain]
            )
            
            # MAIL FROM domain
            mail_from = self.ses_client.get_identity_mail_from_domain_attributes(
                Identities=[self.domain]
            )
            
            domain_verified = verification['VerificationAttributes'].get(
                self.domain, {}
            ).get('VerificationStatus') == 'Success'
            
            dkim_verified = dkim['DkimAttributes'].get(
                self.domain, {}
            ).get('DkimVerificationStatus') == 'Success'
            
            mail_from_domain = mail_from['MailFromDomainAttributes'].get(
                self.domain, {}
            ).get('MailFromDomain', 'Not configured')
            
            mail_from_status = mail_from['MailFromDomainAttributes'].get(
                self.domain, {}
            ).get('MailFromDomainStatus', 'Not configured')
            
            print(f"  Domain verified: {'✅' if domain_verified else '❌'}")
            print(f"  DKIM verified: {'✅' if dkim_verified else '❌'}")
            print(f"  MAIL FROM domain: {mail_from_domain}")
            print(f"  MAIL FROM status: {mail_from_status}")
            
            # Check sending limits
            quota = self.ses_client.get_send_quota()
            print(f"\n  📊 Sending Limits:")
            print(f"    24-hour limit: {int(quota['Max24HourSend'])}")
            print(f"    Per-second rate: {int(quota['MaxSendRate'])}/sec")
            print(f"    Sent in 24h: {int(quota['SentLast24Hours'])}")
            
            return {
                'domain_verified': domain_verified,
                'dkim_verified': dkim_verified,
                'mail_from_configured': mail_from_status == 'Success'
            }
            
        except ClientError as e:
            print(f"  ⚠️  Error checking SES: {e}")
            return {}
    
    def generate_report(self) -> Dict:
        """Generate comprehensive verification report."""
        print("\n" + "="*70)
        print("📋 EMAIL DOMAIN VERIFICATION REPORT")
        print("="*70)
        print(f"Domain: {self.domain}")
        print(f"Region: {self.region}")
        
        # Run all checks
        mx = self.check_mx_records()
        spf = self.check_spf_record()
        dkim = self.check_dkim_records()
        dmarc = self.check_dmarc_record()
        ses = self.check_ses_status()
        
        # Summary
        print("\n" + "="*70)
        print("📊 CONFIGURATION STATUS")
        print("="*70)
        
        checks = {
            'MX Records': mx.get('proton_configured', False),
            'SPF Record': spf.get('exists', False),
            'Proton DKIM': len(dkim.get('proton', [])) == 3,
            'SES DKIM': ses.get('dkim_verified', False),
            'DMARC Record': dmarc.get('exists', False),
            'SES Domain': ses.get('domain_verified', False),
            'SES MAIL FROM': ses.get('mail_from_configured', False)
        }
        
        for check, passed in checks.items():
            icon = "✅" if passed else "❌"
            print(f"  {icon} {check}")
        
        all_passed = all(checks.values())
        
        print("\n" + "="*70)
        if all_passed:
            print("✅ ALL CHECKS PASSED! Your email domain is fully configured.")
        else:
            print("⚠️  SOME CHECKS FAILED. Review the details above.")
        print("="*70 + "\n")
        
        return checks


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 verify_email_setup.py <domain> [aws_region]")
        print("Example: python3 verify_email_setup.py example.com us-east-1")
        sys.exit(1)
    
    domain = sys.argv[1]
    region = sys.argv[2] if len(sys.argv) > 2 else 'us-east-1'
    
    verifier = EmailDomainVerifier(domain=domain, region=region)
    verifier.generate_report()


if __name__ == '__main__':
    main()
