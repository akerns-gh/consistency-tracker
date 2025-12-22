#!/usr/bin/env python3
"""
Test Email Sender
Send test emails via Amazon SES to verify configuration.
"""

import boto3
import sys
from botocore.exceptions import ClientError


def send_test_email(
    region: str,
    from_email: str,
    to_email: str,
    subject: str = "Test Email from SES",
    body: str = "This is a test email sent via Amazon SES."
):
    """
    Send a test email via Amazon SES.
    
    Args:
        region: AWS region (e.g., 'us-east-1')
        from_email: Sender email address
        to_email: Recipient email address
        subject: Email subject
        body: Email body text
    """
    
    ses_client = boto3.client('ses', region_name=region)
    
    try:
        print(f"\n📧 Sending test email...")
        print(f"   From: {from_email}")
        print(f"   To: {to_email}")
        print(f"   Subject: {subject}")
        
        response = ses_client.send_email(
            Source=from_email,
            Destination={
                'ToAddresses': [to_email]
            },
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': body,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        
        message_id = response['MessageId']
        print(f"\n✅ Email sent successfully!")
        print(f"   Message ID: {message_id}")
        print(f"\n💡 Check your inbox (and spam folder) for the test email.")
        print(f"💡 You can also check SES sending statistics in AWS Console.")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        
        print(f"\n❌ Error sending email:")
        print(f"   Error code: {error_code}")
        print(f"   Message: {error_msg}")
        
        if error_code == 'MessageRejected':
            if 'Email address is not verified' in error_msg:
                print(f"\n💡 Your SES account is in sandbox mode.")
                print(f"   You can only send to verified email addresses.")
                print(f"   Solutions:")
                print(f"   1. Verify the recipient address in SES Console")
                print(f"   2. Request production access (SES → Account dashboard)")
            elif 'not verified' in error_msg.lower():
                print(f"\n💡 The sender address/domain is not verified.")
                print(f"   Verify your domain in SES Console first.")
        
        return False


def send_html_email(
    region: str,
    from_email: str,
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str = None
):
    """Send an HTML test email."""
    
    ses_client = boto3.client('ses', region_name=region)
    
    body_dict = {'Html': {'Data': html_body, 'Charset': 'UTF-8'}}
    
    if text_body:
        body_dict['Text'] = {'Data': text_body, 'Charset': 'UTF-8'}
    
    try:
        response = ses_client.send_email(
            Source=from_email,
            Destination={'ToAddresses': [to_email]},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': body_dict
            }
        )
        
        print(f"✅ HTML email sent! Message ID: {response['MessageId']}")
        return True
        
    except ClientError as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Main execution."""
    
    if len(sys.argv) < 4:
        print("="*70)
        print("📧 SES Test Email Sender")
        print("="*70)
        print("\nUsage:")
        print("  python3 send_test_email.py <from> <to> <region> [subject]")
        print("\nExamples:")
        print("  python3 send_test_email.py noreply@mail.example.com you@gmail.com us-east-1")
        print("  python3 send_test_email.py admin@example.com test@example.com us-west-2 'Hello'")
        print("\n💡 Tip: Use mail-tester.com to check your email authentication:")
        print("  python3 send_test_email.py noreply@mail.example.com test-xyz@mail-tester.com us-east-1")
        print("="*70)
        sys.exit(1)
    
    from_email = sys.argv[1]
    to_email = sys.argv[2]
    region = sys.argv[3]
    subject = sys.argv[4] if len(sys.argv) > 4 else "Test Email from Amazon SES"
    
    # Simple text email
    text_body = f"""
Hello!

This is a test email sent via Amazon SES to verify your email configuration.

Configuration details:
- Sender: {from_email}
- Recipient: {to_email}
- AWS Region: {region}

If you received this email:
✅ Your SES domain is verified
✅ Your DNS records are configured correctly
✅ Email authentication (SPF, DKIM) is working

To test authentication quality, send an email to:
https://www.mail-tester.com/ (they'll give you a unique address)

Best regards,
Your Email Automation Script
    """.strip()
    
    send_test_email(
        region=region,
        from_email=from_email,
        to_email=to_email,
        subject=subject,
        body=text_body
    )


if __name__ == '__main__':
    main()
