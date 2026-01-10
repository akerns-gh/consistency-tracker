#!/usr/bin/env python3
"""
Diagnose Email Delivery Issues

This script performs a comprehensive check of email delivery configuration
and provides specific recommendations.
"""

import boto3
import sys
from botocore.exceptions import ClientError

AWS_REGION = "us-east-1"
STACK_NAME = "ConsistencyTracker-Auth"
DOMAIN_NAME = "repwarrior.net"
SES_FROM_EMAIL = f"noreply@{DOMAIN_NAME}"

def get_user_pool_id(cf_client, stack_name):
    """Get User Pool ID from CloudFormation"""
    try:
        response = cf_client.describe_stacks(StackName=stack_name)
        outputs = response['Stacks'][0].get('Outputs', [])
        for output in outputs:
            if output['OutputKey'] == 'UserPoolId':
                return output['OutputValue']
        return None
    except:
        return None

def diagnose_email_issue():
    """Comprehensive email delivery diagnosis"""
    print("=" * 70)
    print("🔍 EMAIL DELIVERY DIAGNOSIS")
    print("=" * 70)
    print()
    
    issues = []
    warnings = []
    
    # Initialize clients
    ses_client = boto3.client('ses', region_name=AWS_REGION)
    cognito_client = boto3.client('cognito-idp', region_name=AWS_REGION)
    cf_client = boto3.client('cloudformation', region_name=AWS_REGION)
    
    # 1. Check SES Account Status
    print("1️⃣  Checking SES Account Status...")
    try:
        # Check sending enabled (v1 API)
        try:
            sending_enabled = ses_client.get_account_sending_enabled()
            if not sending_enabled.get('SendingEnabled', False):
                issues.append("❌ SES sending is DISABLED")
                print("   ❌ SES sending is DISABLED")
                print("   💡 Fix: Go to AWS Console → SES → Account dashboard → Enable sending")
            else:
                print("   ✅ SES sending is enabled")
        except:
            # Try v2 API
            try:
                sesv2_client = boto3.client('sesv2', region_name=AWS_REGION)
                account_attributes = sesv2_client.get_account()
                sending_enabled = account_attributes.get('SendEnabled', False)
                if not sending_enabled:
                    issues.append("❌ SES sending is DISABLED")
                    print("   ❌ SES sending is DISABLED")
                else:
                    print("   ✅ SES sending is enabled")
            except:
                print("   ⚠️  Could not check sending status")
        
        # Check sandbox mode
        quota = ses_client.get_send_quota()
        if quota['MaxSendRate'] <= 1:
            warnings.append("⚠️  SES is in SANDBOX mode - can only send to verified emails")
            print("   ⚠️  SES is in SANDBOX mode")
            print("   💡 Recipient email must be verified in SES")
        else:
            print("   ✅ SES appears to be in production mode")
        
        print()
    except Exception as e:
        print(f"   ❌ Error checking SES: {e}")
        print()
    
    # 2. Check SES Identity Verification
    print("2️⃣  Checking SES Identity Verification...")
    try:
        # Check domain
        domain_verified = False
        try:
            verification = ses_client.get_identity_verification_attributes(
                Identities=[DOMAIN_NAME]
            )
            status = verification.get('VerificationAttributes', {}).get(
                DOMAIN_NAME, {}
            ).get('VerificationStatus')
            if status == 'Success':
                domain_verified = True
                print(f"   ✅ Domain '{DOMAIN_NAME}' is verified")
            else:
                issues.append(f"❌ Domain '{DOMAIN_NAME}' is not verified")
                print(f"   ❌ Domain '{DOMAIN_NAME}' is not verified (Status: {status})")
        except Exception as e:
            print(f"   ⚠️  Error checking domain: {e}")
        
        # Check email
        email_verified = False
        try:
            verification = ses_client.get_identity_verification_attributes(
                Identities=[SES_FROM_EMAIL]
            )
            status = verification.get('VerificationAttributes', {}).get(
                SES_FROM_EMAIL, {}
            ).get('VerificationStatus')
            if status == 'Success':
                email_verified = True
                print(f"   ✅ Email '{SES_FROM_EMAIL}' is verified")
            else:
                if not domain_verified:
                    warnings.append(f"⚠️  Email '{SES_FROM_EMAIL}' not verified (but domain is)")
                print(f"   ℹ️  Email '{SES_FROM_EMAIL}' not individually verified (OK if domain is verified)")
        except Exception as e:
            print(f"   ⚠️  Error checking email: {e}")
        
        if not domain_verified and not email_verified:
            issues.append("❌ No verified SES identity found")
        
        print()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print()
    
    # 3. Check Cognito Configuration
    print("3️⃣  Checking Cognito Email Configuration...")
    try:
        user_pool_id = get_user_pool_id(cf_client, STACK_NAME)
        if not user_pool_id:
            issues.append("❌ Could not get User Pool ID")
            print("   ❌ Could not get User Pool ID")
        else:
            print(f"   ✅ User Pool ID: {user_pool_id}")
            
            # Get email config
            response = cognito_client.describe_user_pool(UserPoolId=user_pool_id)
            email_config = response['UserPool'].get('EmailConfiguration', {})
            
            email_account = email_config.get('EmailSendingAccount', 'COGNITO_DEFAULT')
            from_email = email_config.get('From', '')
            source_arn = email_config.get('SourceArn', '')
            
            if email_account == 'DEVELOPER':
                print("   ✅ Cognito is configured to use SES (DEVELOPER)")
            else:
                issues.append("❌ Cognito is not configured to use SES")
                print(f"   ❌ Cognito email account: {email_account} (should be DEVELOPER)")
            
            if from_email:
                print(f"   ✅ From email: {from_email}")
            else:
                warnings.append("⚠️  From email not set in Cognito")
                print("   ⚠️  From email not set")
            
            if source_arn:
                print(f"   ✅ Source ARN: {source_arn}")
            else:
                if email_account == 'DEVELOPER':
                    issues.append("❌ Source ARN not set (required for DEVELOPER)")
                    print("   ❌ Source ARN not set (required for DEVELOPER)")
        
        print()
    except Exception as e:
        print(f"   ❌ Error checking Cognito: {e}")
        print()
    
    # Summary
    print("=" * 70)
    print("📋 SUMMARY")
    print("=" * 70)
    print()
    
    if issues:
        print("❌ CRITICAL ISSUES (must fix):")
        for issue in issues:
            print(f"   {issue}")
        print()
    
    if warnings:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"   {warning}")
        print()
    
    if not issues and not warnings:
        print("✅ All checks passed! Configuration looks good.")
        print()
        print("💡 If emails still not received:")
        print("   1. Verify recipient email is verified in SES (if in sandbox)")
        print("   2. Check spam/junk folder")
        print("   3. Check CloudWatch logs for errors")
        print("   4. Try requesting production access in SES")
    else:
        print("💡 RECOMMENDED ACTIONS:")
        if "SES sending is DISABLED" in str(issues):
            print("   1. Enable SES sending:")
            print("      - Go to AWS Console → SES → Account dashboard")
            print("      - Click 'Edit' in Account-level sending limits")
            print("      - Enable sending")
        if "SANDBOX" in str(warnings):
            print("   2. Verify recipient email in SES (if in sandbox mode)")
            print("      - Go to AWS Console → SES → Verified identities")
            print("      - Create identity → Email address")
            print("      - Enter recipient email and verify")
        if "not configured to use SES" in str(issues):
            print("   3. Run: python3 aws/configure_cognito_email.py")
    
    print("=" * 70)

if __name__ == "__main__":
    diagnose_email_issue()

