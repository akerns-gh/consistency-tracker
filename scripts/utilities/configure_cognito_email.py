#!/usr/bin/env python3
"""
Configure Cognito User Pool to Use SES for Email Delivery

This script configures the Cognito User Pool to use AWS SES for sending
password reset and verification emails instead of Cognito's default email service.

Prerequisites:
1. SES domain/email must be verified in SES Console
2. SES must be out of sandbox mode (or recipient emails must be verified)
"""

import boto3
import sys
from botocore.exceptions import ClientError

# ============================================================================
# CONFIGURATION - Update these values
# ============================================================================

# AWS Configuration
AWS_REGION = "us-east-1"
STACK_NAME = "ConsistencyTracker-Auth"

# Email Configuration (from app.py)
DOMAIN_NAME = "repwarrior.net"
SES_FROM_EMAIL = f"noreply@{DOMAIN_NAME}"  # Must be verified in SES
SES_FROM_NAME = "Consistency Tracker"

# ============================================================================
# Script Logic
# ============================================================================

def get_user_pool_id(cloudformation_client, stack_name, region):
    """Get User Pool ID from CloudFormation stack outputs"""
    try:
        response = cloudformation_client.describe_stacks(
            StackName=stack_name
        )
        
        stacks = response['Stacks']
        if not stacks:
            print(f"❌ Stack '{stack_name}' not found")
            return None
        
        outputs = stacks[0].get('Outputs', [])
        for output in outputs:
            if output['OutputKey'] == 'UserPoolId':
                return output['OutputValue']
        
        print(f"❌ UserPoolId output not found in stack '{stack_name}'")
        return None
        
    except ClientError as e:
        print(f"❌ Error getting stack outputs: {e}")
        return None


def check_ses_identity(ses_client, identity):
    """Check if an SES identity (domain or email) is verified"""
    try:
        response = ses_client.get_identity_verification_attributes(
            Identities=[identity]
        )
        
        attributes = response.get('VerificationAttributes', {})
        if identity in attributes:
            status = attributes[identity].get('VerificationStatus')
            return status == 'Success'
        
        return False
        
    except ClientError as e:
        print(f"⚠️  Error checking SES identity '{identity}': {e}")
        return False


def list_verified_ses_identities(ses_client):
    """List all verified SES identities"""
    try:
        response = ses_client.list_identities()
        identities = response.get('Identities', [])
        
        verified = []
        for identity in identities:
            if check_ses_identity(ses_client, identity):
                verified.append(identity)
        
        return verified
        
    except ClientError as e:
        print(f"⚠️  Error listing SES identities: {e}")
        return []


def get_cognito_email_config(cognito_client, user_pool_id):
    """Get current Cognito email configuration"""
    try:
        response = cognito_client.describe_user_pool(
            UserPoolId=user_pool_id
        )
        
        user_pool = response['UserPool']
        email_config = user_pool.get('EmailConfiguration', {})
        
        return {
            'email_sending_account': email_config.get('EmailSendingAccount', 'COGNITO_DEFAULT'),
            'from_email': email_config.get('From', ''),
            'reply_to_email': email_config.get('ReplyToEmailAddress', ''),
            'source_arn': email_config.get('SourceArn', ''),
            'configuration_set': email_config.get('ConfigurationSet', '')
        }
        
    except ClientError as e:
        print(f"❌ Error getting Cognito email configuration: {e}")
        return None


def get_ses_identity_arn(ses_client, identity, region):
    """Get the ARN for a verified SES identity"""
    try:
        # Get AWS account ID from STS
        sts_client = boto3.client('sts', region_name=region)
        account_id = sts_client.get_caller_identity()['Account']
        
        # Construct SES identity ARN
        # Format: arn:aws:ses:region:account-id:identity/identity-name
        arn = f"arn:aws:ses:{region}:{account_id}:identity/{identity}"
        return arn
        
    except ClientError as e:
        print(f"⚠️  Error getting SES identity ARN: {e}")
        return None


def configure_cognito_email_ses(cognito_client, user_pool_id, from_email, from_name, source_arn):
    """Configure Cognito User Pool to use SES for email delivery"""
    try:
        print(f"📧 Configuring Cognito to use SES...")
        print(f"   From Email: {from_email}")
        print(f"   From Name: {from_name}")
        print(f"   Source ARN: {source_arn}")
        
        # Update User Pool email configuration
        email_config = {
            'EmailSendingAccount': 'DEVELOPER',  # Use SES
            'From': from_email,
            'ReplyToEmailAddress': from_email,
            'SourceArn': source_arn,  # Required for DEVELOPER email sending account
        }
        
        cognito_client.update_user_pool(
            UserPoolId=user_pool_id,
            EmailConfiguration=email_config
        )
        
        print(f"✅ Cognito email configuration updated successfully")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        if error_code == 'InvalidParameterException':
            print(f"❌ Invalid configuration: {error_message}")
            print(f"   Make sure '{from_email}' is verified in SES")
            print(f"   Make sure SourceArn '{source_arn}' is correct")
        else:
            print(f"❌ Error configuring Cognito email: {e}")
        
        return False


def main():
    print("=" * 70)
    print("📧 CONFIGURE COGNITO TO USE SES FOR EMAIL DELIVERY")
    print("=" * 70)
    print(f"\n📋 Configuration:")
    print(f"   Region: {AWS_REGION}")
    print(f"   Stack: {STACK_NAME}")
    print(f"   Domain: {DOMAIN_NAME}")
    print(f"   From Email: {SES_FROM_EMAIL}")
    print(f"   From Name: {SES_FROM_NAME}")
    print()
    
    # Initialize AWS clients
    cf_client = boto3.client('cloudformation', region_name=AWS_REGION)
    cognito_client = boto3.client('cognito-idp', region_name=AWS_REGION)
    ses_client = boto3.client('ses', region_name=AWS_REGION)
    
    # Step 1: Get User Pool ID
    print("🔍 Step 1: Getting User Pool ID from CloudFormation stack...")
    user_pool_id = get_user_pool_id(cf_client, STACK_NAME, AWS_REGION)
    
    if not user_pool_id:
        print("❌ Failed to get User Pool ID")
        sys.exit(1)
    
    print(f"✅ User Pool ID: {user_pool_id}")
    
    # Step 2: Check current email configuration
    print(f"\n📧 Step 2: Checking current Cognito email configuration...")
    current_config = get_cognito_email_config(cognito_client, user_pool_id)
    
    if current_config:
        print(f"   Current Email Sending Account: {current_config['email_sending_account']}")
        print(f"   Current From Email: {current_config['from_email'] or '(not set)'}")
        
        if current_config['email_sending_account'] == 'DEVELOPER':
            print(f"\n✅ Cognito is already configured to use SES!")
            if current_config['from_email'] == SES_FROM_EMAIL:
                print(f"✅ From email is already set to '{SES_FROM_EMAIL}'")
                print(f"\n💡 Configuration is already correct. No changes needed.")
                return 0
            else:
                print(f"⚠️  From email is set to '{current_config['from_email']}', will update to '{SES_FROM_EMAIL}'")
    
    # Step 3: Verify SES identity
    print(f"\n🔍 Step 3: Verifying SES identity...")
    
    # Check if domain is verified
    domain_verified = check_ses_identity(ses_client, DOMAIN_NAME)
    email_verified = check_ses_identity(ses_client, SES_FROM_EMAIL)
    
    if domain_verified:
        print(f"✅ Domain '{DOMAIN_NAME}' is verified in SES")
        ses_identity = DOMAIN_NAME
    elif email_verified:
        print(f"✅ Email '{SES_FROM_EMAIL}' is verified in SES")
        ses_identity = SES_FROM_EMAIL
    else:
        print(f"❌ Neither domain '{DOMAIN_NAME}' nor email '{SES_FROM_EMAIL}' is verified in SES")
        print(f"\n📝 Please verify your domain or email in SES Console:")
        print(f"   1. Go to AWS Console → SES → Verified identities")
        print(f"   2. Create identity for domain '{DOMAIN_NAME}' or email '{SES_FROM_EMAIL}'")
        print(f"   3. Add DNS records if verifying domain")
        print(f"   4. Wait for verification (15-30 minutes)")
        print(f"   5. Re-run this script")
        
        # List verified identities for reference
        verified = list_verified_ses_identities(ses_client)
        if verified:
            print(f"\n💡 Currently verified SES identities:")
            for identity in verified:
                print(f"   - {identity}")
        else:
            print(f"\n⚠️  No verified SES identities found")
        
        sys.exit(1)
    
    # Step 4: Get SES identity ARN
    print(f"\n🔍 Step 4: Getting SES identity ARN...")
    source_arn = get_ses_identity_arn(ses_client, ses_identity, AWS_REGION)
    
    if not source_arn:
        print("❌ Failed to get SES identity ARN")
        sys.exit(1)
    
    print(f"✅ SES Identity ARN: {source_arn}")
    
    # Step 5: Configure Cognito to use SES
    print(f"\n⚙️  Step 5: Configuring Cognito User Pool to use SES...")
    success = configure_cognito_email_ses(
        cognito_client,
        user_pool_id,
        SES_FROM_EMAIL,
        SES_FROM_NAME,
        source_arn
    )
    
    if not success:
        print("❌ Failed to configure Cognito email")
        sys.exit(1)
    
    # Step 6: Verify configuration
    print(f"\n✅ Step 6: Verifying configuration...")
    updated_config = get_cognito_email_config(cognito_client, user_pool_id)
    
    if updated_config and updated_config['email_sending_account'] == 'DEVELOPER':
        print(f"✅ Cognito is now configured to use SES")
        print(f"   From Email: {updated_config['from_email']}")
    else:
        print(f"⚠️  Configuration may not have been applied correctly")
        print(f"   Please check the Cognito Console manually")
    
    # Success summary
    print("\n" + "=" * 70)
    print("🎉 Cognito email configuration completed successfully!")
    print("\n📝 Configuration Summary:")
    print(f"   Email Sending Account: SES (DEVELOPER)")
    print(f"   From Email: {SES_FROM_EMAIL}")
    print(f"   From Name: {SES_FROM_NAME}")
    print(f"   SES Identity: {ses_identity}")
    print("\n💡 Next Steps:")
    print(f"   1. Test password reset functionality")
    print(f"   2. Check CloudWatch logs if emails are not received")
    print(f"   3. Verify SES is out of sandbox mode (or recipient emails are verified)")
    print("\n⚠️  Note: If SES is in sandbox mode, you can only send to verified email addresses.")
    print("   Request production access in SES Console to send to any email address.")


if __name__ == "__main__":
    main()

