#!/usr/bin/env python3
"""
Check SES Status and Configuration

This script checks the SES account status, verified identities, and sending limits.
"""

import boto3
import sys
from botocore.exceptions import ClientError

AWS_REGION = "us-east-1"
DOMAIN_NAME = "repwarrior.net"
SES_FROM_EMAIL = f"noreply@{DOMAIN_NAME}"

def check_ses_status():
    """Check SES account status and configuration"""
    print("=" * 70)
    print("📧 SES STATUS CHECK")
    print("=" * 70)
    print()
    
    ses_client = boto3.client('ses', region_name=AWS_REGION)
    
    # Check account sending limits
    try:
        quota = ses_client.get_send_quota()
        print("📊 Sending Limits:")
        print(f"   24-hour limit: {int(quota['Max24HourSend'])}")
        print(f"   Per-second rate: {int(quota['MaxSendRate'])}/sec")
        print(f"   Sent in last 24h: {int(quota['SentLast24Hours'])}")
        print()
    except ClientError as e:
        print(f"❌ Error getting send quota: {e}")
        return
    
    # Check account attributes (sandbox mode)
    try:
        attributes = ses_client.get_account_sending_enabled()
        sending_enabled = attributes.get('SendingEnabled', False)
        
        # Check if in sandbox mode
        try:
            # Try to get production access status
            # If we can send to any address, we're out of sandbox
            # This is a heuristic - sandbox mode limits sending to verified addresses only
            print("🔍 Account Status:")
            print(f"   Sending Enabled: {'✅' if sending_enabled else '❌'}")
            
            # Check verified identities count
            identities = ses_client.list_identities()
            verified_count = 0
            for identity in identities.get('Identities', []):
                try:
                    verification = ses_client.get_identity_verification_attributes(
                        Identities=[identity]
                    )
                    status = verification.get('VerificationAttributes', {}).get(
                        identity, {}
                    ).get('VerificationStatus')
                    if status == 'Success':
                        verified_count += 1
                except:
                    pass
            
            print(f"   Verified Identities: {verified_count}")
            
            # Heuristic: If max send rate is very low (like 1), likely in sandbox
            if quota['MaxSendRate'] <= 1:
                print("   ⚠️  Likely in SANDBOX mode (low send rate)")
                print("   💡 Request production access to send to any email address")
            else:
                print("   ✅ Likely in PRODUCTION mode")
            
            print()
        except Exception as e:
            print(f"   ⚠️  Could not determine sandbox status: {e}")
            print()
    except ClientError as e:
        print(f"⚠️  Error checking account attributes: {e}")
        print()
    
    # Check verified identities
    print("🔍 Verified Identities:")
    try:
        identities = ses_client.list_identities()
        verified = []
        
        for identity in identities.get('Identities', []):
            try:
                verification = ses_client.get_identity_verification_attributes(
                    Identities=[identity]
                )
                status = verification.get('VerificationAttributes', {}).get(
                    identity, {}
                ).get('VerificationStatus')
                
                if status == 'Success':
                    verified.append(identity)
                    print(f"   ✅ {identity}")
            except:
                pass
        
        if not verified:
            print("   ❌ No verified identities found")
        
        print()
        
        # Check specific domain/email
        print(f"🔍 Checking specific identities:")
        for identity in [DOMAIN_NAME, SES_FROM_EMAIL]:
            try:
                verification = ses_client.get_identity_verification_attributes(
                    Identities=[identity]
                )
                status = verification.get('VerificationAttributes', {}).get(
                    identity, {}
                ).get('VerificationStatus')
                
                if status == 'Success':
                    print(f"   ✅ {identity} - Verified")
                else:
                    print(f"   ❌ {identity} - Not verified (Status: {status})")
            except ClientError as e:
                print(f"   ⚠️  {identity} - Error checking: {e}")
        
    except ClientError as e:
        print(f"❌ Error listing identities: {e}")
    
    print()
    print("=" * 70)
    print("💡 Tips:")
    print("   - If in sandbox mode, verify recipient emails before sending")
    print("   - Request production access in SES Console to send to any address")
    print("   - Check CloudWatch logs if emails are not received")
    print("=" * 70)

if __name__ == "__main__":
    check_ses_status()

