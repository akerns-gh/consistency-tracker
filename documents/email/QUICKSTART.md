# Quick Start Guide

## Setup in 5 Minutes

### 1. Install Dependencies

```bash
pip install boto3 dnspython --break-system-packages
```

### 2. Collect Proton DNS Values

1. Go to https://mail.proton.me
2. Settings → Domain names → Add domain
3. Copy the DNS values (see README.md for details)

### 3. Configure

```bash
# Copy config template
cp config.template.json config.json

# Edit with your values
nano config.json
```

Fill in:
- `domain`: Your domain (e.g., "example.com")
- `aws_region`: AWS region (e.g., "us-east-1")
- `proton.verification`: From Proton's "Verify" tab
- `proton.dkim[0-2]`: From Proton's "DKIM" tab (3 values)
- `proton.dmarc`: From Proton's "DMARC" tab

### 4. Run Setup

```bash
python3 email_domain_setup.py
```

Wait for it to complete (2-5 minutes).

### 5. Verify in Proton

1. Go back to Proton setup wizard
2. Click "Next" through all tabs
3. Wait for green checkmarks (5-60 minutes)

### 6. Test

**Receive email:**
```bash
# Send yourself a test
echo "Test" | mail -s "Test" you@yourdomain.com
```

**Send via SES:**
```bash
python3 send_test_email.py noreply@mail.yourdomain.com you@gmail.com us-east-1
```

**Verify authentication:**
```bash
python3 verify_email_setup.py yourdomain.com us-east-1
```

## Common Issues

### "AWS credentials not found"
```bash
aws configure
# Enter your AWS Access Key ID and Secret
```

### "No hosted zone found"
Create one in Route 53 first, or the script will tell you.

### "SES in sandbox mode"
Request production access in SES Console → Account dashboard.

### "DNS not propagating"
Wait 30-60 minutes, then run verify script again.

## Files Overview

- `email_domain_setup.py` - Main automation script
- `verify_email_setup.py` - Check configuration status
- `send_test_email.py` - Send test emails via SES
- `config.template.json` - Configuration template
- `README.md` - Full documentation
- `requirements.txt` - Python dependencies

## Next Steps

1. ✅ Create email addresses in Proton Mail
2. ✅ Request SES production access (if needed)
3. ✅ Set up CloudWatch alarms for SES
4. ✅ Configure your application to use SES
5. ✅ Test email sending/receiving thoroughly

## Getting Help

- Check README.md for detailed documentation
- Use verify script to diagnose issues
- Check AWS SES Console for sending statistics
- Review Route 53 for DNS records

Happy emailing! 📧
