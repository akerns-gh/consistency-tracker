# CloudFront Certificate Configuration Guide

> **When to use this guide**: Use this document when you need to configure or verify CloudFront certificates and custom domain aliases. This is a focused, step-by-step guide with current status information. For complete deployment documentation, see [DEPLOYMENT_README.md](DEPLOYMENT_README.md).

## Current Status

**Route 53 Records**: ✅ All configured correctly
- `repwarrior.net` → Frontend distribution
- `www.repwarrior.net` → Frontend distribution  
- `content.repwarrior.net` → Content distribution

**CloudFront Distributions**: ❌ Missing certificates and aliases
- Frontend (E11CYNQ91MDSZR): No aliases, no certificate
- Content (E1986A93DSMC7O): No aliases, no certificate

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

After both distributions deploy, run:

```bash
/tmp/verify-config.sh
```

Expected output:
- Frontend: Should show aliases `["repwarrior.net", "www.repwarrior.net"]` and certificate ARN
- Content: Should show alias `["content.repwarrior.net"]` and certificate ARN

### Step 4: Test HTTPS Access

```bash
# Test root domain
curl -I https://repwarrior.net

# Test www subdomain
curl -I https://www.repwarrior.net

# Test content subdomain
curl -I https://content.repwarrior.net
```

All should return `200 OK` or redirects with valid SSL certificates.


