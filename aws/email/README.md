# Email Domain Setup Automation

Automates the configuration of dual email setup:
- **Proton Mail** for receiving email and personal sending
- **Amazon SES** for application email sending

## Prerequisites

1. **AWS Account** with Route 53 hosted zone for your domain
2. **AWS CLI configured** with credentials that have permissions for:
   - Route 53 (read/write DNS records)
   - SES (verify domains, configure DKIM)
3. **Python 3.7+** installed
4. **Proton Mail account** with a paid plan (required for custom domains)

## Installation

```bash
# Install boto3
pip install boto3 --break-system-packages

# Or using a virtual environment
python3 -m venv venv
source venv/bin/activate
pip install boto3
```

## Setup Process

### Step 1: Collect Proton Mail DNS Values

**You MUST do this manually** (Proton doesn't have a public API):

1. Log into Proton Mail: https://mail.proton.me
2. Go to **Settings → All Settings → Domain names**
3. Click **Add domain**
4. Enter your domain and click **Next**
5. Go through each tab and **copy down these values**:

   **Verify Tab:**
   - Copy the TXT record value (e.g., `protonmail-verification=abc123...`)

   **DKIM Tab (3 records):**
   - Record 1: `protonmail._domainkey` → Copy the CNAME value
   - Record 2: `protonmail2._domainkey` → Copy the CNAME value
   - Record 3: `protonmail3._domainkey` → Copy the CNAME value

   **DMARC Tab:**
   - Copy the TXT record value (e.g., `v=DMARC1; p=quarantine...`)

**Keep the Proton tab open** - you'll verify later!

### Step 2: Configure the Script

**Option A: Edit config file (recommended):**

```bash
# Copy the template
cp config.template.json config.json

# Edit with your values
nano config.json
```

Fill in:
- Your domain name
- AWS region (e.g., us-east-1, us-west-2)
- Proton DNS values from Step 1

**Option B: Edit script directly:**

Edit `email_domain_setup.py` and update the values at the top of `main()`:
- `DOMAIN`
- `AWS_REGION`
- `PROTON_VALUES`

### Step 3: Run the Script

```bash
# Make executable
chmod +x email_domain_setup.py

# Run it
python3 email_domain_setup.py
```

The script will:
1. ✅ Find your Route 53 hosted zone
2. ✅ Create Proton Mail DNS records (MX, TXT, CNAME)
3. ✅ Verify domain in SES
4. ✅ Enable SES DKIM (auto-creates DNS records)
5. ✅ Set up custom MAIL FROM domain for SES
6. ✅ Check verification status

### Step 4: Verify in Proton Mail

1. Go back to your Proton setup tab
2. Click through each tab and click **Next**:
   - Verify → MX → SPF → DKIM → DMARC
3. Wait for green checkmarks (5-60 minutes)

### Step 5: Create Email Addresses

**In Proton Mail:**
1. Go to **Settings → Identity and addresses**
2. Click **Add address**
3. Create your email addresses (e.g., adam@yourdomain.com)

**Enable Catch-all (optional):**
1. **Settings → Domain names → Your domain**
2. Enable **Catch-all address**

### Step 6: Request SES Production Access

By default, SES is in "sandbox mode" (can only send to verified addresses).

1. Go to **SES Console → Account dashboard**
2. Click **Request production access**
3. Fill out the form (usually approved in 24 hours)

## Testing

### Test 1: Receiving Email

```bash
# Send test email to your domain
echo "Test email" | mail -s "Test" adam@yourdomain.com
```

Should arrive in Proton inbox.

### Test 2: Send via Proton

Send an email from Proton Mail to Gmail and check:
- Arrives (not in spam)
- SPF/DKIM/DMARC pass (view email headers)

### Test 3: Send via SES

Use the AWS CLI to send a test:

```bash
aws ses send-email \
  --region us-east-1 \
  --from noreply@mail.yourdomain.com \
  --to your-email@gmail.com \
  --subject "SES Test" \
  --text "This is a test from SES"
```

### Test 4: Email Authentication

Send to https://www.mail-tester.com:

```bash
# They'll give you a unique address like test-xxxxx@mail-tester.com
aws ses send-email \
  --region us-east-1 \
  --from noreply@mail.yourdomain.com \
  --to test-xxxxx@mail-tester.com \
  --subject "Mail Tester" \
  --text "Testing authentication"
```

Should score 9/10 or 10/10.

## Application Integration

### Python (boto3)

```python
import boto3

ses = boto3.client('ses', region_name='us-east-1')

response = ses.send_email(
    Source='noreply@mail.yourdomain.com',
    Destination={'ToAddresses': ['user@example.com']},
    Message={
        'Subject': {'Data': 'Hello'},
        'Body': {'Text': {'Data': 'This is a test email'}}
    }
)
```

### SMTP

```python
import smtplib
from email.mime.text import MIMEText

# Create SMTP credentials in SES console first
msg = MIMEText('This is a test')
msg['Subject'] = 'Test Email'
msg['From'] = 'noreply@mail.yourdomain.com'
msg['To'] = 'user@example.com'

server = smtplib.SMTP('email-smtp.us-east-1.amazonaws.com', 587)
server.starttls()
server.login('SMTP_USERNAME', 'SMTP_PASSWORD')
server.send_message(msg)
server.quit()
```

## Troubleshooting

### DNS Records Not Propagating

```bash
# Check DNS propagation
dig MX yourdomain.com
dig TXT yourdomain.com
dig CNAME protonmail._domainkey.yourdomain.com

# Or use online tools
# https://mxtoolbox.com/SuperTool.aspx
# https://dnschecker.org
```

### SES Still in Sandbox

- Request production access in SES Console
- Can only send to verified addresses until approved

### Proton Verification Failing

- Wait 30-60 minutes for DNS propagation
- Check Route 53 records match Proton exactly
- No typos in CNAME values

### Emails Going to Spam

- Check SPF/DKIM/DMARC are all passing
- Use https://www.mail-tester.com for detailed report
- Warm up your domain (start with low volume)

## DNS Record Summary

After running the script, you should have:

### Root Domain (yourdomain.com)

| Type | Name | Value | Purpose |
|------|------|-------|---------|
| TXT | @ | protonmail-verification=... | Proton verification |
| TXT | @ | v=spf1 include:_spf.protonmail.ch mx ~all | Proton SPF |
| MX | @ | 10 mail.protonmail.ch | Proton incoming mail |
| MX | @ | 20 mailsec.protonmail.ch | Proton backup |
| CNAME | protonmail._domainkey | xxx.proton.ch. | Proton DKIM 1 |
| CNAME | protonmail2._domainkey | xxx.proton.ch. | Proton DKIM 2 |
| CNAME | protonmail3._domainkey | xxx.proton.ch. | Proton DKIM 3 |
| CNAME | abc._domainkey | abc.dkim.amazonses.com | SES DKIM 1 |
| CNAME | def._domainkey | def.dkim.amazonses.com | SES DKIM 2 |
| CNAME | ghi._domainkey | ghi.dkim.amazonses.com | SES DKIM 3 |
| TXT | _dmarc | v=DMARC1; p=quarantine... | DMARC policy |

### Subdomain (mail.yourdomain.com)

| Type | Name | Value | Purpose |
|------|------|-------|---------|
| MX | mail | 10 feedback-smtp.us-east-1.amazonses.com | SES bounce handling |
| TXT | mail | v=spf1 include:amazonses.com ~all | SES SPF |

## Advanced Features

### Add More Domains

Run the script again with a different domain:

```python
setup = EmailDomainSetup(domain='anotherdomain.com', region='us-east-1')
```

### Custom MAIL FROM Subdomain

Change the subdomain name:

```python
MAIL_SUBDOMAIN = 'bounce'  # Instead of 'mail'
```

### Multiple AWS Regions

Set up SES in multiple regions for redundancy:

```python
for region in ['us-east-1', 'us-west-2', 'eu-west-1']:
    setup = EmailDomainSetup(domain=DOMAIN, region=region)
    setup.setup_ses_domain()
```

## Security Best Practices

1. **Enable MFA** on AWS account
2. **Use IAM roles** with least privilege
3. **Enable SES event notifications** (bounces, complaints)
4. **Set up CloudWatch alarms** for sending limits
5. **Enable DMARC reporting** and monitor it
6. **Use SES configuration sets** for tracking
7. **Rotate SMTP credentials** regularly

## Cost Estimate

- **Route 53 Hosted Zone:** $0.50/month
- **Route 53 Queries:** ~$0.40/month per million queries
- **SES:** $0.10 per 1,000 emails sent (first 62,000 free with EC2)
- **Proton Mail:** Varies by plan ($4-30/month)

## Support

- **AWS SES:** https://docs.aws.amazon.com/ses/
- **Route 53:** https://docs.aws.amazon.com/route53/
- **Proton Mail:** https://proton.me/support

## License

This script is provided as-is for educational and automation purposes.
