"""
Email service for sending emails via AWS SES.
Provides functions to send templated and custom emails.
"""

import os
import uuid
import boto3
import hmac
import hashlib
import base64
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from botocore.exceptions import ClientError

# SES configuration from environment variables
SES_REGION = os.environ.get("SES_REGION", "us-east-1")
SES_FROM_EMAIL = os.environ.get("SES_FROM_EMAIL", "noreply@repwarrior.net")
SES_FROM_NAME = os.environ.get("SES_FROM_NAME", "Consistency Tracker")

# Initialize SES client
ses_client = boto3.client("ses", region_name=SES_REGION)


def send_email(
    to_addresses: List[str],
    subject: str,
    html_body: str,
    text_body: str = None,
    from_email: str = None,
    from_name: str = None,
    reply_to: List[str] = None,
) -> dict:
    """
    Send an email via AWS SES.
    
    Args:
        to_addresses: List of recipient email addresses
        subject: Email subject line
        html_body: HTML content of the email
        text_body: Plain text content (optional, defaults to HTML stripped)
        from_email: From email address (defaults to SES_FROM_EMAIL)
        from_name: From display name (defaults to SES_FROM_NAME)
        reply_to: List of reply-to email addresses (optional)
    
    Returns:
        dict with 'message_id' if successful, None on error
    
    Raises:
        ClientError: If SES send fails
    """
    if not to_addresses:
        raise ValueError("At least one recipient email address is required")
    
    from_email = from_email or SES_FROM_EMAIL
    from_name = from_name or SES_FROM_NAME
    from_address = f"{from_name} <{from_email}>"
    
    # Prepare destination
    destination = {
        "ToAddresses": to_addresses,
    }
    
    # Prepare message
    message = {
        "Subject": {"Data": subject, "Charset": "UTF-8"},
        "Body": {
            "Html": {"Data": html_body, "Charset": "UTF-8"},
        },
    }
    
    # Add text body if provided
    if text_body:
        message["Body"]["Text"] = {"Data": text_body, "Charset": "UTF-8"}
    
    # Prepare email parameters
    email_params = {
        "Source": from_address,
        "Destination": destination,
        "Message": message,
    }
    
    # Add reply-to if provided
    if reply_to:
        email_params["ReplyToAddresses"] = reply_to
    
    try:
        response = ses_client.send_email(**email_params)
        message_id = response.get("MessageId")
        print(f"Email sent successfully. MessageId: {message_id}")
        return {"message_id": message_id, "success": True}
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        print(f"Error sending email: {error_code} - {error_message}")
        raise


def send_templated_email(
    to_addresses: List[str],
    template_data: dict,
    from_email: str = None,
    from_name: str = None,
    reply_to: List[str] = None,
) -> dict:
    """
    Send an email using a template from email_templates module.
    
    Args:
        to_addresses: List of recipient email addresses
        template_data: Dictionary with 'html', 'text', and 'subject' keys
        from_email: From email address (optional)
        from_name: From display name (optional)
        reply_to: List of reply-to email addresses (optional)
    
    Returns:
        dict with 'message_id' if successful
    
    Raises:
        ValueError: If template_data is missing required keys
        ClientError: If SES send fails
    """
    if "subject" not in template_data:
        raise ValueError("template_data must include 'subject'")
    if "html" not in template_data:
        raise ValueError("template_data must include 'html'")
    
    return send_email(
        to_addresses=to_addresses,
        subject=template_data["subject"],
        html_body=template_data["html"],
        text_body=template_data.get("text"),
        from_email=from_email,
        from_name=from_name,
        reply_to=reply_to,
    )


def send_bulk_email(
    destinations: List[dict],
    subject: str,
    html_body: str,
    text_body: str = None,
    from_email: str = None,
    from_name: str = None,
) -> dict:
    """
    Send bulk emails to multiple recipients (each can have different content).
    
    Args:
        destinations: List of dicts with 'ToAddresses' and optional 'TemplateData'
        subject: Email subject line
        html_body: HTML content template (can use {name} placeholders)
        text_body: Plain text content template (optional)
        from_email: From email address (optional)
        from_name: From display name (optional)
    
    Returns:
        dict with 'message_id' if successful
    
    Note: For simple bulk sends, use send_email with multiple ToAddresses.
    This function is for when you need different content per recipient.
    """
    from_email = from_email or SES_FROM_EMAIL
    from_name = from_name or SES_FROM_NAME
    from_address = f"{from_name} <{from_email}>"
    
    # Prepare message template
    message_template = {
        "Subject": {"Data": subject, "Charset": "UTF-8"},
        "Body": {
            "Html": {"Data": html_body, "Charset": "UTF-8"},
        },
    }
    
    if text_body:
        message_template["Body"]["Text"] = {"Data": text_body, "Charset": "UTF-8"}
    
    # Prepare destinations for send_bulk_templated_email format
    # Note: SES send_bulk_templated_email requires templates, so we'll use send_email in a loop
    # For better performance with many recipients, consider using SES templates
    results = []
    for dest in destinations:
        to_addresses = dest.get("ToAddresses", [])
        if not to_addresses:
            continue
        
        # Customize message if TemplateData provided
        html = html_body
        text = text_body
        if "TemplateData" in dest:
            template_data = dest["TemplateData"]
            html = html.format(**template_data)
            if text:
                text = text.format(**template_data)
        
        try:
            result = send_email(
                to_addresses=to_addresses,
                subject=subject,
                html_body=html,
                text_body=text,
                from_email=from_email,
                from_name=from_name,
            )
            results.append(result)
        except Exception as e:
            print(f"Error sending email to {to_addresses}: {e}")
            results.append({"success": False, "error": str(e)})
    
    return {"results": results, "total": len(results)}


def validate_email_address(email: str) -> bool:
    """
    Basic email validation.
    
    Args:
        email: Email address to validate
    
    Returns:
        True if email format is valid, False otherwise
    """
    import re
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_email_addresses(emails: List[str]) -> tuple[List[str], List[str]]:
    """
    Validate a list of email addresses.
    
    Args:
        emails: List of email addresses to validate
    
    Returns:
        Tuple of (valid_emails, invalid_emails)
    """
    valid = []
    invalid = []
    for email in emails:
        if validate_email_address(email):
            valid.append(email)
        else:
            invalid.append(email)
    return valid, invalid


def verify_email_identity(email: str) -> dict:
    """
    Verify an email address in SES by sending a verification email.
    
    This initiates the verification process. The recipient must click
    the verification link in the email to complete verification.
    
    Args:
        email: Email address to verify
    
    Returns:
        dict with 'success' and optional 'message' or 'error'
    
    Note: If the email is already verified, this will still succeed
    (SES returns success for already-verified addresses).
    """
    if not validate_email_address(email):
        return {
            "success": False,
            "error": "Invalid email address format"
        }
    
    try:
        response = ses_client.verify_email_identity(EmailAddress=email)
        print(f"Verification email sent to {email}")
        return {
            "success": True,
            "message": f"Verification email sent to {email}. The recipient must click the verification link to complete verification.",
            "email": email
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        
        # If email is already verified, that's fine
        if error_code == "AlreadyExistsException":
            print(f"Email {email} is already verified in SES")
            return {
                "success": True,
                "message": "Email address is already verified",
                "email": email,
                "already_verified": True
            }
        
        print(f"Error verifying email {email}: {error_code} - {error_message}")
        return {
            "success": False,
            "error": f"{error_code}: {error_message}",
            "email": email
        }
    except Exception as e:
        print(f"Unexpected error verifying email {email}: {e}")
        return {
            "success": False,
            "error": str(e),
            "email": email
        }


def _get_verification_secret() -> str:
    """Get the secret key for signing verification tokens."""
    secret = os.environ.get("EMAIL_VERIFICATION_SECRET")
    if not secret:
        raise ValueError("EMAIL_VERIFICATION_SECRET environment variable is not set")
    return secret


def _generate_signed_token(email: str, expires_at: int) -> Tuple[str, str]:
    """
    Generate an HMAC-signed token for email verification.
    
    Args:
        email: Email address to verify
        expires_at: Unix timestamp when token expires
    
    Returns:
        Tuple of (token, token_id) where token is the signed token string
    """
    token_id = str(uuid.uuid4())
    issued_at = int(datetime.utcnow().timestamp())
    
    # Create payload
    payload = {
        "email": email,
        "exp": expires_at,
        "iat": issued_at,
        "jti": token_id
    }
    
    # Serialize payload (sorted keys for consistency)
    payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    
    # Sign with HMAC-SHA256
    secret = _get_verification_secret()
    signature = hmac.new(
        secret.encode('utf-8'),
        payload_json.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Encode payload as base64url (URL-safe)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode('utf-8')).decode('utf-8').rstrip('=')
    
    # Token format: base64(payload).signature
    token = f"{payload_b64}.{signature}"
    
    return token, token_id


def _validate_token_signature(token: str) -> dict:
    """
    Validate token signature and extract payload.
    
    Args:
        token: Signed token string
    
    Returns:
        dict with 'valid' (bool), 'payload' (if valid), and 'error' (if invalid)
    """
    try:
        # Split token into payload and signature
        parts = token.split('.')
        if len(parts) != 2:
            return {"valid": False, "error": "Invalid token format"}
        
        payload_b64, signature = parts
        
        # Decode payload (add padding if needed)
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += '=' * padding
        
        payload_json = base64.urlsafe_b64decode(payload_b64).decode('utf-8')
        payload = json.loads(payload_json)
        
        # Verify signature
        secret = _get_verification_secret()
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Use constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(signature, expected_signature):
            return {"valid": False, "error": "Invalid token signature"}
        
        # Check expiration
        current_time = int(datetime.utcnow().timestamp())
        if current_time > payload.get("exp", 0):
            return {"valid": False, "error": "Token expired"}
        
        return {"valid": True, "payload": payload}
        
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as e:
        return {"valid": False, "error": f"Invalid token: {str(e)}"}
    except Exception as e:
        return {"valid": False, "error": f"Token validation error: {str(e)}"}


def generate_email_verification_token(email: str, frontend_url: str = None) -> dict:
    """
    Generate a verification token and store it in DynamoDB.
    
    Args:
        email: Email address to verify
        frontend_url: Frontend URL for verification link (defaults to FRONTEND_URL env var)
    
    Returns:
        dict with 'token', 'verification_url', 'email', and 'expires_at'
    """
    from shared.db_utils import EMAIL_VERIFICATION_TABLE, get_table
    
    if not validate_email_address(email):
        return {
            "success": False,
            "error": "Invalid email address format"
        }
    
    # Calculate expiration (1 hour from now)
    expires_at = int((datetime.utcnow() + timedelta(hours=1)).timestamp())
    
    # Generate signed token
    try:
        token, token_id = _generate_signed_token(email, expires_at)
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "email": email
        }
    
    # Get frontend URL
    frontend_url = frontend_url or os.environ.get("FRONTEND_URL", "https://repwarrior.net")
    verification_url = f"{frontend_url}/verify-email?token={token}"
    
    try:
        table = get_table(EMAIL_VERIFICATION_TABLE)
        table.put_item(
            Item={
                "token": token,
                "tokenId": token_id,  # Store token ID for lookup
                "email": email,
                "status": "pending",
                "createdAt": datetime.utcnow().isoformat() + "Z",
                "expiresAt": expires_at,
            }
        )
        print(f"Generated signed verification token for {email}")
        return {
            "success": True,
            "token": token,
            "verification_url": verification_url,
            "email": email,
            "expires_at": expires_at
        }
    except Exception as e:
        print(f"Error generating verification token for {email}: {e}")
        return {
            "success": False,
            "error": str(e),
            "email": email
        }


def check_cognito_email_verified(user_pool_id: str, email: str) -> dict:
    """
    Check if a Cognito user's email is already verified.
    
    Args:
        user_pool_id: Cognito User Pool ID
        email: Email address (used as username)
    
    Returns:
        dict with 'verified' (bool), 'exists' (bool), and optional 'error'
    """
    if not user_pool_id:
        return {
            "verified": False,
            "exists": False,
            "error": "User pool ID is required"
        }
    
    try:
        cognito_client = boto3.client("cognito-idp", region_name=os.environ.get("COGNITO_REGION", "us-east-1"))
        response = cognito_client.admin_get_user(
            UserPoolId=user_pool_id,
            Username=email
        )
        
        # Check email_verified attribute
        attributes = {attr['Name']: attr['Value'] for attr in response.get('UserAttributes', [])}
        email_verified = attributes.get('email_verified', 'false').lower() == 'true'
        
        return {
            "verified": email_verified,
            "exists": True
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == "UserNotFoundException":
            return {
                "verified": False,
                "exists": False
            }
        return {
            "verified": False,
            "exists": False,
            "error": f"{error_code}: {e.response.get('Error', {}).get('Message', str(e))}"
        }
    except Exception as e:
        return {
            "verified": False,
            "exists": False,
            "error": str(e)
        }


def invalidate_pending_tokens(email: str) -> dict:
    """
    Invalidate all pending verification tokens for an email address.
    
    Args:
        email: Email address
    
    Returns:
        dict with 'success' and 'count' of invalidated tokens
    """
    from shared.db_utils import EMAIL_VERIFICATION_TABLE, get_table
    
    try:
        table = get_table(EMAIL_VERIFICATION_TABLE)
        
        # Query by email using GSI
        response = table.query(
            IndexName="email-index",
            KeyConditionExpression="email = :email",
            FilterExpression="#status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":email": email, ":status": "pending"}
        )
        
        items = response.get("Items", [])
        count = 0
        
        # Mark all pending tokens as used
        for item in items:
            token = item.get("token")
            if token:
                try:
                    table.update_item(
                        Key={"token": token},
                        UpdateExpression="SET #status = :status",
                        ExpressionAttributeNames={"#status": "status"},
                        ExpressionAttributeValues={":status": "used"}
                    )
                    count += 1
                except Exception as e:
                    print(f"Error invalidating token {token}: {e}")
        
        return {
            "success": True,
            "count": count
        }
    except Exception as e:
        print(f"Error invalidating pending tokens for {email}: {e}")
        return {
            "success": False,
            "error": str(e),
            "count": 0
        }


def resend_verification_token(email: str, user_pool_id: str = None, frontend_url: str = None) -> dict:
    """
    Resend verification email for an email address.
    
    Args:
        email: Email address to resend verification for
        user_pool_id: Cognito User Pool ID (optional)
        frontend_url: Frontend URL (optional)
    
    Returns:
        dict with 'success' and optional 'error' or 'message'
    """
    from shared.db_utils import RESEND_TRACKING_TABLE, get_table
    from datetime import datetime, timedelta
    
    if not validate_email_address(email):
        return {
            "success": False,
            "error": "Invalid email address format"
        }
    
    # Check rate limiting (max 1 request per 5 minutes per email)
    try:
        table = get_table(RESEND_TRACKING_TABLE)
        response = table.get_item(Key={"email": email})
        
        if "Item" in response:
            item = response["Item"]
            last_resend = item.get("lastResendTimestamp", 0)
            current_time = int(datetime.utcnow().timestamp())
            time_since_last = current_time - last_resend
            min_interval = 300  # 5 minutes
            
            if time_since_last < min_interval:
                remaining = min_interval - time_since_last
                return {
                    "success": False,
                    "error": f"Please wait {remaining // 60 + 1} minutes before requesting another verification email."
                }
    except Exception as e:
        print(f"Error checking resend rate limit for {email}: {e}")
        # Continue anyway - don't block on rate limit check error
    
    # Check if email is already verified
    if not user_pool_id:
        user_pool_id = os.environ.get("COGNITO_USER_POOL_ID")
    
    if user_pool_id:
        verification_status = check_cognito_email_verified(user_pool_id, email)
        if verification_status.get("verified"):
            # Email already verified - return generic success (don't reveal status)
            return {
                "success": True,
                "message": "If this email address is registered and not yet verified, a verification email has been sent."
            }
        # If user doesn't exist, we'll still send the email (don't reveal if user exists)
    
    # Invalidate old pending tokens
    invalidate_pending_tokens(email)
    
    # Generate new token
    token_result = generate_email_verification_token(email, frontend_url)
    if not token_result.get("success"):
        return {
            "success": False,
            "error": token_result.get("error", "Failed to generate verification token")
        }
    
    # Send verification email
    verification_url = token_result.get("verification_url")
    from shared.email_templates import get_email_verification_template
    template = get_email_verification_template(email, verification_url, email.split("@")[0])
    
    try:
        send_templated_email([email], template)
        
        # Record resend timestamp
        try:
            current_time = int(datetime.utcnow().timestamp())
            expires_at = current_time + 300  # TTL: 5 minutes
            table.put_item(
                Item={
                    "email": email,
                    "lastResendTimestamp": current_time,
                    "expiresAt": expires_at
                }
            )
        except Exception as e:
            print(f"Error recording resend timestamp for {email}: {e}")
        
        return {
            "success": True,
            "message": "If this email address is registered and not yet verified, a verification email has been sent."
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to send verification email: {str(e)}"
        }


def verify_cognito_email(user_pool_id: str, email: str) -> dict:
    """
    Update Cognito user's email_verified attribute to true.
    
    Args:
        user_pool_id: Cognito User Pool ID
        email: Email address (used as username)
    
    Returns:
        dict with 'success' and optional 'error'
    """
    if not user_pool_id:
        return {
            "success": False,
            "error": "User pool ID is required"
        }
    
    try:
        cognito_client = boto3.client("cognito-idp", region_name=os.environ.get("COGNITO_REGION", "us-east-2"))
        cognito_client.admin_update_user_attributes(
            UserPoolId=user_pool_id,
            Username=email,
            UserAttributes=[
                {'Name': 'email_verified', 'Value': 'true'}
            ]
        )
        print(f"Updated Cognito email_verified for {email}")
        return {
            "success": True,
            "email": email
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        print(f"Error updating Cognito email verification for {email}: {error_code} - {error_message}")
        return {
            "success": False,
            "error": f"{error_code}: {error_message}",
            "email": email
        }
    except Exception as e:
        print(f"Unexpected error updating Cognito email verification for {email}: {e}")
        return {
            "success": False,
            "error": str(e),
            "email": email
        }


def validate_and_verify_email(token: str, user_pool_id: str = None) -> dict:
    """
    Validate a verification token and verify email in both SES and Cognito.
    
    Args:
        token: Verification token
        user_pool_id: Cognito User Pool ID (optional, will use env var if not provided)
    
    Returns:
        dict with 'success', 'email', and optional 'error' or 'message'
    """
    from shared.db_utils import EMAIL_VERIFICATION_TABLE, get_table
    
    if not token:
        return {
            "success": False,
            "error": "Token is required"
        }
    
    # First validate token signature
    validation_result = _validate_token_signature(token)
    if not validation_result.get("valid"):
        return {
            "success": False,
            "error": validation_result.get("error", "Invalid token")
        }
    
    payload = validation_result.get("payload")
    token_id = payload.get("jti")
    email_from_token = payload.get("email")
    
    try:
        table = get_table(EMAIL_VERIFICATION_TABLE)
        response = table.get_item(Key={"token": token})
        
        if "Item" not in response:
            return {
                "success": False,
                "error": "Invalid verification token"
            }
        
        item = response["Item"]
        email = item.get("email")
        status = item.get("status", "pending")
        expires_at = item.get("expiresAt")
        
        # Verify email from token matches email in database
        if email_from_token != email:
            return {
                "success": False,
                "error": "Token email mismatch"
            }
        
        # Check if token is already used
        if status == "used":
            return {
                "success": False,
                "error": "This verification link has already been used"
            }
        
        # Expiration already checked in signature validation, but double-check
        if expires_at:
            current_time = int(datetime.utcnow().timestamp())
            if current_time > expires_at:
                return {
                    "success": False,
                    "error": "This verification link has expired"
                }
        
        # Verify email in SES
        ses_result = verify_email_identity(email)
        if not ses_result.get("success"):
            return {
                "success": False,
                "error": f"Failed to verify email in SES: {ses_result.get('error', 'Unknown error')}",
                "email": email
            }
        
        # Update Cognito email verification
        if not user_pool_id:
            user_pool_id = os.environ.get("COGNITO_USER_POOL_ID")
        
        cognito_result = verify_cognito_email(user_pool_id, email)
        if not cognito_result.get("success"):
            # SES verification succeeded but Cognito update failed
            # Still mark token as used to prevent retry
            table.update_item(
                Key={"token": token},
                UpdateExpression="SET #status = :status",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={":status": "used"}
            )
            return {
                "success": False,
                "error": f"Email verified in SES but failed to update Cognito: {cognito_result.get('error', 'Unknown error')}",
                "email": email
            }
        
        # Mark token as used
        table.update_item(
            Key={"token": token},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": "used"}
        )
        
        print(f"Email verification completed successfully for {email}")
        return {
            "success": True,
            "email": email,
            "message": "Email verified successfully"
        }
        
    except Exception as e:
        print(f"Error validating verification token: {e}")
        return {
            "success": False,
            "error": str(e)
        }

