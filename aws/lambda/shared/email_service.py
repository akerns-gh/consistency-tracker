"""
Email service for sending emails via AWS SES.
Provides functions to send templated and custom emails.
"""

import os
import boto3
from typing import List, Optional
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

