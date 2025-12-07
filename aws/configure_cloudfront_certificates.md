# CloudFront Certificate Configuration Guide

> **When to use this guide**: Use this document when you need to configure or verify CloudFront certificates and custom domain aliases. This is a focused, step-by-step guide with current status information. For complete deployment documentation, see [DEPLOYMENT_README.md](DEPLOYMENT_README.md).

## Current Status

**Route 53 Records**: ✅ All configured correctly
- `repwarrior.net` → Frontend distribution
- `www.repwarrior.net` → Frontend distribution  
- `content.repwarrior.net` → Content distribution

**CloudFront Distributions**: ✅ Certificates and aliases configured
- Frontend (E11CYNQ91MDSZR): Aliases configured, certificate attached
- Content (E1986A93DSMC7O): Alias configured, certificate attached

## Certificate ARN

```
arn:aws:acm:us-east-1:707406431671:certificate/98d1bf1b-dfd3-45bb-82aa-176aedd2babe
```

## Configuration Steps

### Step 1: Configure Frontend Distribution (E11CYNQ91MDSZR)

1. Go to **AWS Console → CloudFront**
2. Click on distribution **E11CYNQ91MDSZR**
3. Click **Edit** (top right)
4. Scroll to **Settings** section
5. Under **Alternate domain names (CNAMEs)**:
   - Click **Add item**
   - Add: `repwarrior.net`
   - Click **Add item** again
   - Add: `www.repwarrior.net`
6. Under **Custom SSL certificate**:
   - Select **Custom SSL certificate (example.com)**
   - Choose: `repwarrior.net` (or paste ARN: `arn:aws:acm:us-east-1:707406431671:certificate/98d1bf1b-dfd3-45bb-82aa-176aedd2babe`)
7. Click **Save changes** at the bottom
8. Wait 10-15 minutes for deployment

### Step 2: Configure Content Distribution (E1986A93DSMC7O)

1. In CloudFront console, click on distribution **E1986A93DSMC7O**
2. Click **Edit**
3. Scroll to **Settings** section
4. Under **Alternate domain names (CNAMEs)**:
   - Click **Add item**
   - Add: `content.repwarrior.net`
5. Under **Custom SSL certificate**:
   - Select **Custom SSL certificate (example.com)**
   - Choose: `repwarrior.net` (same certificate as frontend)
6. Click **Save changes**
7. Wait 10-15 minutes for deployment

### Step 3: Verify Configuration

After both distributions deploy, run the verification script:

```bash
/tmp/verify-config.sh
```

**What the script checks:**
- CloudFront distribution aliases (custom domain names)
- SSL certificate ARNs attached to distributions
- Distribution status (enabled/disabled)
- Route 53 A records pointing to CloudFront distributions

**Expected output when fully configured:**
```json
Frontend Distribution (E11CYNQ91MDSZR):
{
    "Aliases": ["repwarrior.net", "www.repwarrior.net"],
    "Certificate": "arn:aws:acm:us-east-1:707406431671:certificate/98d1bf1b-dfd3-45bb-82aa-176aedd2babe",
    "Status": true
}

Content Distribution (E1986A93DSMC7O):
{
    "Aliases": ["content.repwarrior.net"],
    "Certificate": "arn:aws:acm:us-east-1:707406431671:certificate/98d1bf1b-dfd3-45bb-82aa-176aedd2babe",
    "Status": true
}

=== Verification Summary ===
✅ Frontend distribution: Configured
✅ Content distribution: Configured
```

### Step 4: Test HTTPS Access

```bash
# Test root domain
curl -I https://repwarrior.net

# Test www subdomain
curl -I https://www.repwarrior.net

# Test content subdomain
curl -I https://content.repwarrior.net
```

**Expected Results:**
- All domains should return valid SSL certificates (no certificate errors)
- Frontend domains (`repwarrior.net`, `www.repwarrior.net`) may return `403 Access Denied` until frontend files are uploaded to S3 (this is expected - infrastructure is correctly configured)
- Content domain (`content.repwarrior.net`) may return bucket listing (XML) if bucket is empty, or `200 OK` if files exist

**Note**: The `403 Access Denied` error on frontend domains is **not a configuration issue**. It indicates the S3 bucket is empty and needs frontend files uploaded. The infrastructure (CloudFront, certificates, DNS) is working correctly.


