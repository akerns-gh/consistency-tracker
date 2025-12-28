# SES Email Setup Guide

This guide covers setting up AWS SES (Simple Email Service) for sending application emails using a verified Proton Mail custom domain.

## Overview

The application uses AWS SES to send automated emails for:
- Password reset requests (via Cognito)
- User invitations (admin/coach/player accounts)
- Club creation confirmations
- Team creation confirmations
- Player invitations (with unique access links)

## Architecture

- **AWS SES**: Handles email delivery
- **Proton Mail Custom Domain**: Verified in SES as the "From" address
- **Lambda Functions**: Send emails via SES API
- **Cognito**: Configured to use SES for password reset emails

## Deployment

The SES stack is automatically deployed with the other CDK stacks:

```bash
cd aws
cdk deploy ConsistencyTracker-SES
# Or deploy all stacks:
cdk deploy --all
```

## Post-Deployment Configuration

### Step 1: Verify Domain in SES

1. Go to **AWS Console → SES → Verified identities**
2. Click **Create identity**
3. Select **Domain**
4. Enter your Proton Mail custom domain (e.g., `yourdomain.com`)
5. Click **Create identity**

### Step 2: Add DNS Records

SES will provide DNS records that need to be added to your domain's DNS provider (Route 53 or Proton Mail DNS):

1. **DKIM Records** (3 CNAME records for email authentication)
2. **Verification Record** (TXT record for domain verification)

**For Route 53:**
- Go to Route 53 → Hosted zones → your domain
- Add the records provided by SES

**For Proton Mail DNS:**
- Go to Proton Mail → Settings → Domain → DNS records
- Add the records provided by SES

### Step 3: Wait for Verification

- Domain verification typically takes 15-30 minutes after DNS records are added
- Check status in SES Console → Verified identities
- Status will change from "Pending verification" to "Verified"

### Step 4: Configure Cognito to Use SES

1. Go to **AWS Console → Cognito → User Pools → ConsistencyTracker-AdminPool**
2. Click **Messaging** tab
3. Under **Email configuration**:
   - Select **Send email through Amazon SES**
   - Choose your verified domain/email identity
   - Set **From email address**: `noreply@yourdomain.com` (or your preferred address)
   - Set **From sender name**: `Consistency Tracker`
4. Click **Save changes**

### Step 5: Request Production Access (if in Sandbox)

SES starts in **sandbox mode**, which only allows sending to verified email addresses.

To send to any email address:

1. Go to **AWS Console → SES → Account dashboard**
2. Click **Request production access**
3. Fill out the form:
   - **Mail type**: Transactional
   - **Website URL**: `https://repwarrior.net`
   - **Use case description**: "Sending transactional emails for a youth sports consistency tracking application (password resets, user invitations, notifications)"
   - **Expected sending volume**: Estimate based on your user base
4. Submit request
5. AWS typically approves within 24-48 hours

**Note**: While in sandbox mode, you can still test by verifying test email addresses in SES Console.

## Testing

### Test Email Sending

1. **Verify a test email address** (if in sandbox):
   - Go to SES → Verified identities
   - Click **Create identity** → **Email address**
   - Enter a test email and verify it

2. **Test via application**:
   - Create a new club (should send confirmation email)
   - Create a new team (should send confirmation email)
   - Create a new player (should send invitation email if email provided)
   - Invite a player (should send invitation email)

3. **Check CloudWatch Logs**:
   - Go to CloudWatch → Log groups
   - Find `/aws/lambda/ConsistencyTracker-API-AdminAppFunction`
   - Look for email sending logs

### Troubleshooting

**Emails not sending:**
- Check SES is out of sandbox mode (or recipient is verified)
- Verify domain is verified in SES
- Check CloudWatch logs for errors
- Verify IAM permissions (Lambda should have `ses:SendEmail` permission)

**Cognito password reset emails not working:**
- Verify Cognito is configured to use SES (Step 4 above)
- Check SES domain is verified
- Verify the "From" email address is verified in SES

**Domain verification failing:**
- Ensure DNS records are correctly added
- Wait 15-30 minutes for DNS propagation
- Check DNS record values match exactly what SES provided
- Verify DNS records are in the correct format (CNAME for DKIM, TXT for verification)

## Email Templates

The application includes HTML email templates for:
- Password reset
- User invitation (with temporary password)
- Club creation confirmation
- Team creation confirmation
- Player invitation (with temporary password)

Templates are located in `aws/lambda/shared/email_templates.py` and can be customized as needed.

## Configuration

Email configuration is set via environment variables in Lambda functions:
- `SES_REGION`: AWS region for SES (default: us-east-1)
- `SES_FROM_EMAIL`: Verified email address (e.g., noreply@yourdomain.com)
- `SES_FROM_NAME`: Display name for emails (default: "Consistency Tracker")
- `FRONTEND_URL`: Frontend URL for email links (default: https://repwarrior.net)

These are automatically set by the CDK stack based on your domain configuration.

## Cost

- **SES Pricing**: $0.10 per 1,000 emails
- **Free Tier**: First 62,000 emails per month free (if using EC2/Lambda)
- **Typical Usage**: < 1,000 emails/month = effectively free

## Security

- Only verified domains/emails can be used as "From" addresses
- IAM roles use least privilege (only `ses:SendEmail` and `ses:SendRawEmail`)
- Email addresses are validated before sending
- All email sending is logged in CloudWatch

## Related Files

- `aws/stacks/ses_stack.py` - SES infrastructure stack
- `aws/lambda/shared/email_service.py` - Email sending utility
- `aws/lambda/shared/email_templates.py` - HTML email templates
- `aws/lambda/admin_app.py` - Email sending in admin endpoints

