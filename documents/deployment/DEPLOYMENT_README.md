# CDK Infrastructure Setup

This directory contains the AWS CDK infrastructure code for the Consistency Tracker application.

## Prerequisites

1. **AWS CLI configured**: `aws configure`
2. **CDK CLI installed**: `npm install -g aws-cdk`
3. **CDK bootstrapped**: `cdk bootstrap aws://707406431671/us-east-1`
4. **Python 3.9+** installed
5. **Python virtual environment** (recommended)

## Setup

### 1. Create Virtual Environment

```bash
cd aws
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: The requirements specify `aws-cdk-lib>=2.223.0` (latest version). If you have an existing virtual environment, upgrade dependencies with:
```bash
pip install --upgrade -r requirements.txt
```

### 3. Verify CDK Installation

```bash
cdk --version
```

### 4. Bootstrap CDK (if not already done)

```bash
cdk bootstrap aws://707406431671/us-east-1
```

## Complete Deployment Order

For a fresh deployment, follow these steps in order:

### Step 1: Deploy Infrastructure (CDK Stacks)

Deploy all AWS infrastructure using the automated script:

```bash
./aws/deploy.sh
```

Or manually:
```bash
cdk deploy --all
```

**Stack deployment order** (handled automatically by the script):
1. `ConsistencyTracker-Database` - DynamoDB tables
2. `ConsistencyTracker-Auth` - Cognito User Pool
3. `ConsistencyTracker-SES` - SES email configuration
4. `ConsistencyTracker-API` - API Gateway & Lambda functions
5. `ConsistencyTracker-DNS` - Route 53 & ACM certificates
6. `ConsistencyTracker-Storage` - S3 buckets & CloudFront distributions

**Note**: The DNS stack must deploy before Storage because Storage imports the certificate ARN from DNS.

### Step 2: Configure CloudFront Certificates (Manual)

After infrastructure deployment, configure CloudFront distributions with SSL certificates:

See [configure_cloudfront_certificates.md](configure_cloudfront_certificates.md) for detailed steps.

**Update (Automated):**
These steps are now automated by `aws/post_deploy_configure_domains.py` and are run automatically at the end of `./aws/deploy.sh`:

- CloudFront aliases + ACM cert attachment (frontend + content)
- API Gateway custom domain + Route53 alias (TLS **1.2**)

You can also run it manually (safe/idempotent):

```bash
python aws/post_deploy_configure_domains.py --wait
```

### Step 3: Configure SES Email (Optional but Recommended)

After deployment, configure SES for email delivery:

1. **Verify your domain in SES** (see [SES_SETUP.md](SES_SETUP.md) for detailed steps)
2. **Configure Cognito to use SES** for password reset emails
3. **Request production access** if you need to send to unverified addresses

See [SES_SETUP.md](SES_SETUP.md) for complete SES configuration instructions.

**Note**: The application will work without SES, but email notifications (invitations, confirmations) will not be sent.

### Step 4: Create Admin User

Create the first admin user in Cognito:

```bash
python aws/create_admin_user.py
```

Or via AWS Console:
1. Go to AWS Console → Cognito → User Pools
2. Select "ConsistencyTracker-AdminPool"
3. Create a new user
4. Add user to "club-admins" group

### Step 4: Deploy Frontend Application

Build and deploy the React frontend:

```bash
./scripts/deploy-frontend.sh
```

This script:
- Builds the React app (`npm run build`)
- Uploads files to S3
- Invalidates CloudFront cache
- Verifies CloudFront origin configuration

**Manual alternative:**
```bash
cd app
npm run build
aws s3 sync dist/ s3://consistency-tracker-frontend-us-east-1/ --delete
aws cloudfront create-invalidation --distribution-id E11CYNQ91MDSZR --paths "/*"
```

### Step 5: Configure IP Allowlisting (Optional)

If you want to restrict access to specific IP addresses:

```bash
./aws/scripts/update-waf-ip-allowlist.sh
```

**When to run:**
- After initial deployment to restrict access
- When your IP address changes
- To update the allowlist with new IPs

**Note**: This sets WAF default action to "Block", so only your IPs can access the site.

### Step 6: Security Configuration

Before deploying to production, ensure security measures are properly configured:

1. **Set EMAIL_VERIFICATION_SECRET**: 
   ```bash
   # Generate a secure random secret
   openssl rand -hex 32
   
   # Set as CDK context or environment variable
   cdk deploy --context email_verification_secret=<generated_secret>
   ```

2. **Review Security Settings**: See [SECURITY.md](../SECURITY.md) for comprehensive security documentation

3. **Configure CloudWatch Alarms**: Set up alarms for security events (see SECURITY.md)

4. **Enable MFA**: Ensure AWS account has MFA enabled

### Step 7: Post-Deployment Setup

1. **Verify CloudFront origin configuration (optional):**
   ```bash
   aws cloudfront get-distribution-config --id E11CYNQ91MDSZR --output json | \
     jq '.DistributionConfig.Origins.Items[0] | {DomainName, S3OriginConfig}'
   ```
   Should use `s3.amazonaws.com` endpoint (not `s3-website-us-east-1.amazonaws.com`)

2. **Create initial team data** (via admin dashboard):
   - Default activities
   - Activity configurations
   - Content categories
   - Navigation menu structure

3. **Set up monitoring:**
4. **(Optional) Seed data from CSV** (separate script):

```bash
python aws/seed_from_csv.py \
  --clubs data/clubs.csv \
  --teams data/teams.csv \
  --players data/players.csv \
  --activities data/activities.csv \
  --content-pages data/content_pages.csv
```
   - CloudWatch dashboards
   - SNS alerts
   - AWS Budget alerts

### Summary: Quick Reference

```bash
# 1. Deploy infrastructure
./aws/deploy.sh

# 2. Configure CloudFront certificates (manual - see configure_cloudfront_certificates.md)

# 3. Create admin user
python aws/create_admin_user.py

# 4. Deploy frontend
./scripts/deploy-frontend.sh

# 5. Configure IP allowlisting (optional)
./aws/scripts/update-waf-ip-allowlist.sh
```

## Quick Deployment

### One-Command Deployment

The easiest way to deploy Phase 1 infrastructure:

**Option 1: Using bash script (recommended)**
```bash
./aws/deploy.sh
```

**Option 2: Using Python script directly**
```bash
python aws/deploy.py
```

Both scripts will:
1. Check prerequisites (AWS CLI, CDK, Python)
2. Set up Python virtual environment (if needed)
3. Install dependencies
4. Bootstrap CDK (if needed)
5. Synthesize CDK templates
6. Deploy Phase 1 stacks (Database and Auth)
7. Verify deployment

The bash script (`deploy.sh`) automatically handles venv setup and activation, making it the simplest option.

### Manual Deployment

If you prefer to deploy manually:

#### Synthesize CloudFormation Templates

```bash
cdk synth
```

This generates CloudFormation templates without deploying.

### View Differences

```bash
cdk diff
```

Shows what changes will be made to the deployed stacks.

### Deploy Stacks

**Using the deployment script (recommended):**
```bash
python deploy.py
```

**Manual deployment:**
```bash
# Deploy all stacks
cdk deploy --all

# Deploy specific stack
cdk deploy ConsistencyTracker-Database
cdk deploy ConsistencyTracker-Auth
```

### Destroy Stacks

```bash
# Destroy all stacks
cdk destroy --all

# Destroy specific stack
cdk destroy ConsistencyTracker-Database
```

**Warning**: DynamoDB tables are set to `RETAIN` on deletion, so they won't be automatically deleted. You'll need to delete them manually from the AWS Console if needed.

## Data Protection & Safety

### Deployment Script Safety

The deployment scripts (`deploy.sh` and `deploy.py`) are designed with data protection as a priority:

✅ **Safe Operations:**
- **Only deploys/updates** - Never destroys or deletes resources
- **No destroy commands** - Scripts do not include `cdk destroy`
- **Error handling** - Failures cause rollback, not deletion
- **Existing resource preservation** - Updates preserve all existing data

### DynamoDB Table Protection

All 6 DynamoDB tables are configured with `RemovalPolicy.RETAIN`:

```python
removal_policy=RemovalPolicy.RETAIN  # Retain on stack deletion
```

**What this means:**
- ✅ Tables are **NOT deleted** if the stack is deleted
- ✅ Data **persists** even if you run `cdk destroy`
- ✅ Tables must be **manually deleted** from AWS Console if needed
- ✅ Your data is **protected from accidental deletion**

**Protected Tables:**
- ConsistencyTracker-Players
- ConsistencyTracker-Activities
- ConsistencyTracker-Tracking
- ConsistencyTracker-Reflections
- ConsistencyTracker-ContentPages
- ConsistencyTracker-Teams

### What Happens on Errors

**Deployment Failures:**
- If deployment fails: CDK rolls back **new** resources only
- Existing resources remain **unchanged**
- Your data is **never deleted** on errors

**Stack Update Failures:**
- If stack update fails: Existing resources remain **unchanged**
- No data loss occurs
- You can retry the deployment

**Synthesis Failures:**
- If template synthesis fails: **Nothing is deployed**
- No changes are made to AWS
- Safe to fix and retry

### Additional Safety Features

1. **Point-in-Time Recovery**: All DynamoDB tables have point-in-time recovery enabled for additional data protection
2. **Deployment Verification**: Scripts verify existing resources and confirm data protection before deployment
3. **Clear Messaging**: Scripts display clear safety messages about data protection

### Manual Destruction (If Needed)

If you need to destroy infrastructure (not recommended for production):

```bash
# This will delete stacks but RETAIN DynamoDB tables
cdk destroy ConsistencyTracker-Database
cdk destroy ConsistencyTracker-Auth
```

**Important Notes:**
- DynamoDB tables will **remain** (due to RETAIN policy)
- You must **manually delete** tables from AWS Console if needed
- **All data in tables will be preserved** until manually deleted
- Cognito User Pool will be deleted (users can be exported first)

### Best Practices

1. ✅ **Use deployment scripts** - They're designed to be safe
2. ✅ **Never run `cdk destroy`** in production without careful consideration
3. ✅ **Backup important data** - Use DynamoDB exports if needed
4. ✅ **Test in dev environment** - Verify changes before production
5. ✅ **Review CloudFormation changes** - Use `cdk diff` before deploying

## Stack Structure

### Phase 1 (Current)

- **DatabaseStack**: All DynamoDB tables
  - Player table
  - Activity table
  - Tracking table
  - Reflection table
  - ContentPages table
  - Team/Config table

- **AuthStack**: Cognito User Pool
  - User pool for admin authentication
  - App client for web application
  - Admin user group
  - Custom password policy (12 chars min)

### Phase 2 (Placeholders)

- **ApiStack**: API Gateway and Lambda functions
- **StorageStack**: S3 buckets and CloudFront
- **DnsStack**: Route 53 configuration

## Configuration

The domain name and region are configured in `app.py`:
- Domain: `repwarrior.net`
- Region: `us-east-1`

## CloudFront Certificate Configuration

**Important**: There is a known CDK synthesis bug when using ACM certificates with CloudFront Distribution. The certificate must be added manually via AWS Console after the initial deployment.

> **📋 Quick Reference Guide**: For a focused step-by-step guide with current configuration status, see **[configure_cloudfront_certificates.md](configure_cloudfront_certificates.md)**. Use this guide when:
> - You need to configure certificates after initial deployment
> - You want to verify current certificate/alias status
> - You're troubleshooting certificate configuration issues
> - You need a quick checklist format

### Manual Certificate Configuration via AWS Console

After deploying all stacks, follow these steps to add the certificate to your CloudFront distributions:

**Note**: The detailed guide in [configure_cloudfront_certificates.md](configure_cloudfront_certificates.md) provides a more focused walkthrough with current status information.

#### Step 1: Get Certificate ARN

The certificate ARN is available from the DNS stack output:

```bash
aws cloudformation describe-stacks \
  --stack-name ConsistencyTracker-DNS \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`CertificateArn`].OutputValue' \
  --output text
```

Or use the existing certificate ARN:
```
arn:aws:acm:us-east-1:707406431671:certificate/98d1bf1b-dfd3-45bb-82aa-176aedd2babe
```

#### Step 2: Configure Frontend Distribution

1. Go to **AWS Console → CloudFront**
2. Find the **frontend distribution** - Look for:
   - **Distribution ID**: `E11CYNQ91MDSZR` (or search for description "CloudFront distribution for Consistency Tracker frontend")
   - **Domain name**: `d346yye80fnvlo.cloudfront.net`
   - **Note**: If you see multiple frontend distributions, use the one with ID `E11CYNQ91MDSZR` (check CloudFormation stack outputs to confirm)
3. Click on the distribution ID to open it, then click **Edit**
4. Scroll to **Settings** section
5. Under **Alternate domain names (CNAMEs)**, click **Add item** and add:
   - `repwarrior.net`
   - `www.repwarrior.net`
6. Under **Custom SSL certificate**, select:
   - **Custom SSL certificate (example.com)**
   - Choose the certificate: `repwarrior.net` (or paste the ARN: `arn:aws:acm:us-east-1:707406431671:certificate/98d1bf1b-dfd3-45bb-82aa-176aedd2babe`)
7. Click **Save changes** at the bottom
8. Wait for the distribution to deploy (this takes 10-15 minutes). The status will change from "In Progress" to "Deployed"

#### Step 3: Configure Content Distribution

1. In the same CloudFront console, find the **content distribution** - Look for:
   - **Distribution ID**: `E1986A93DSMC7O` (note: letter O, not zero - or search for description "CloudFront distribution for Consistency Tracker content images")
   - **Domain name**: `d1rt8gejjf42oo.cloudfront.net`
   - **Note**: If you see multiple content distributions, use the one with ID `E1986A93DSMC7O` (check CloudFormation stack outputs to confirm)
2. Click on the distribution ID to open it, then click **Edit**
3. Scroll to **Settings** section
4. Under **Alternate domain names (CNAMEs)**, click **Add item** and add:
   - `content.repwarrior.net`
5. Under **Custom SSL certificate**, select:
   - **Custom SSL certificate (example.com)**
   - Choose the same certificate: `repwarrior.net` (or paste the ARN: `arn:aws:acm:us-east-1:707406431671:certificate/98d1bf1b-dfd3-45bb-82aa-176aedd2babe`)
6. Click **Save changes** at the bottom
7. Wait for the distribution to deploy (10-15 minutes). The status will change from "In Progress" to "Deployed"

**Note**: If you see duplicate distributions (old ones from previous deployments), you can identify the correct ones by checking the CloudFormation stack outputs:
```bash
aws cloudformation describe-stacks --stack-name ConsistencyTracker-Storage --region us-east-1 --query 'Stacks[0].Outputs[?OutputKey==`FrontendDistributionId` || OutputKey==`ContentDistributionDomainName`]'
```

**Current Active Distributions:**
- **Frontend**: `E11CYNQ91MDSZR` (domain: `d346yye80fnvlo.cloudfront.net`)
- **Content**: `E1986A93DSMC7O` (domain: `d1rt8gejjf42oo.cloudfront.net`)

#### Step 4: Verify Configuration

After configuring both distributions, verify everything is set up correctly:

> **💡 Tip**: You can also use the verification script from [configure_cloudfront_certificates.md](configure_cloudfront_certificates.md) which provides a quick status summary.

**Verify CloudFront Distributions:**
```bash
# Check frontend distribution (should show repwarrior.net and www.repwarrior.net)
aws cloudfront get-distribution-config \
  --id E11CYNQ91MDSZR \
  --region us-east-1 \
  --query 'DistributionConfig.{Aliases:Aliases.Items,Certificate:ViewerCertificate.ACMCertificateArn}' \
  --output json

# Check content distribution (should show content.repwarrior.net)
aws cloudfront get-distribution-config \
  --id E1986A93DSMC7O \
  --region us-east-1 \
  --query 'DistributionConfig.{Aliases:Aliases.Items,Certificate:ViewerCertificate.ACMCertificateArn}' \
  --output json
```

**Verify Route 53 Records:**

The DNS stack should have already created Route 53 A records pointing to your CloudFront distributions. Verify they exist:

```bash
aws route53 list-resource-record-sets \
  --hosted-zone-id Z0224155HV050F02RZE0 \
  --query 'ResourceRecordSets[?Type==`A` && (Name==`repwarrior.net.` || Name==`www.repwarrior.net.` || Name==`content.repwarrior.net.`)]' \
  --output table
```

Expected results:
- `repwarrior.net` → `d346yye80fnvlo.cloudfront.net` (frontend)
- `www.repwarrior.net` → `d346yye80fnvlo.cloudfront.net` (frontend)
- `content.repwarrior.net` → `d1rt8gejjf42oo.cloudfront.net` (content)

**Test Domain Access:**
```bash
# Test HTTPS access (should work after distributions deploy)
curl -I https://repwarrior.net
curl -I https://www.repwarrior.net
curl -I https://content.repwarrior.net
```

**Note**: If you see `403 Access Denied` errors when testing the frontend domain (`repwarrior.net` or `www.repwarrior.net`), this is **expected** until frontend files are uploaded to the S3 bucket. The infrastructure (buckets, CloudFront, certificates, DNS) is correctly configured, but the bucket is empty. See the "What's Included in This Deployment" section below for details.

#### Quick Verification Script

For a comprehensive verification of CloudFront configuration, you can use the verification script:

```bash
/tmp/verify-config.sh
```

This script checks:
- CloudFront distribution aliases and certificates
- Route 53 DNS records
- Provides a summary of configuration status

Expected output when fully configured:
```
✅ Frontend distribution: Configured
✅ Content distribution: Configured
```

The script displays detailed information about:
- Distribution aliases (custom domain names)
- SSL certificate ARNs
- Distribution status (enabled/disabled)
- Route 53 A records pointing to CloudFront

If the verification script is not available, you can run the individual verification commands from Step 4 above.

If the Route 53 records don't exist, the DNS stack's `add_route53_records` method should have created them. If needed, you can manually create A records in Route 53 pointing to your CloudFront distribution domain names.

#### Alternative: Using AWS CLI

You can also update distributions via CLI, but this requires getting the distribution ID and creating a new distribution config. The Console method above is simpler and recommended.

## What's Included in This Deployment

This infrastructure deployment phase includes:

✅ **Infrastructure Resources:**
- S3 buckets (frontend and content images)
- CloudFront distributions with WAF protection
- Route 53 DNS records
- ACM SSL/TLS certificates
- API Gateway with Lambda functions
- DynamoDB tables
- Cognito User Pool

✅ **Configuration:**
- Security settings (WAF, CORS, throttling)
- CloudFront Origin Access Identity (OAI)
- Bucket policies and permissions
- Error handling (404/403 → index.html for React routing)

❌ **Not Included (Separate Deployment Steps):**
- **Frontend application files** - The S3 buckets are created but empty. You need to upload your frontend build files separately.
- **Application code updates** - Lambda function code updates are separate from infrastructure deployment.

**Expected Behavior After Infrastructure Deployment:**

- ✅ DNS records resolve correctly
- ✅ HTTPS certificates are configured
- ✅ CloudFront distributions are active
- ⚠️ Frontend domain returns `403 Access Denied` until files are uploaded
- ✅ Content domain may return bucket listing (XML) if bucket is empty

**To Deploy Frontend Files:**

After infrastructure deployment, build and upload your frontend application:

```bash
# Navigate to the app directory
cd app

# Build the React application
npm run build

# Upload to the S3 bucket
aws s3 sync dist/ s3://consistency-tracker-frontend-us-east-1/ --delete

# Invalidate CloudFront cache to serve new files immediately
aws cloudfront create-invalidation \
  --distribution-id E11CYNQ91MDSZR \
  --paths "/*"
```

**Important Notes:**
- The build output directory is `app/dist/` (not `build/`)
- CloudFront cache invalidation takes 1-2 minutes to complete
- After invalidation, the site will serve the new files immediately

**Verify CloudFront Origin Configuration:**

After deploying, verify that CloudFront is using the correct S3 origin with OAI:

```bash
aws cloudfront get-distribution-config --id E11CYNQ91MDSZR --output json | \
  jq '.DistributionConfig.Origins.Items[0] | {DomainName, S3OriginConfig, OriginAccessIdentity}'
```

The origin should use:
- **DomainName**: `consistency-tracker-frontend-us-east-1.s3.amazonaws.com` (NOT `s3-website-us-east-1.amazonaws.com`)
- **S3OriginConfig**: Should be present (not null)
- **OriginAccessIdentity**: Should reference the OAI (e.g., `origin-access-identity/cloudfront/E2FNHISS0EYDX0`)

If the origin is using the website endpoint (`s3-website-us-east-1.amazonaws.com`), the distribution needs to be updated. See troubleshooting section below.

## Security Configuration

The infrastructure includes several security measures that are automatically configured:

### CORS Restrictions

- **API Gateway**: CORS is restricted to `https://repwarrior.net` and `https://www.repwarrior.net` only
- **S3 Buckets**: CORS is restricted to the same domains for image uploads
- This prevents unauthorized cross-origin requests

### API Gateway Throttling

- **Rate Limit**: 1,000 requests per second per account
- **Burst Limit**: 2,000 requests per burst
- This prevents API abuse and DDoS attacks

### CloudFront WAF (Web Application Firewall)

- **Geographic Restriction**: Only allows IP addresses from the United States
- **Rate Limiting**: Blocks IPs exceeding 2,000 requests per 5 minutes
- **AWS Managed Rules**: Common Rule Set protects against common exploits (SQL injection, XSS, etc.)
- **CloudWatch Metrics**: All WAF events are logged for monitoring
- **Custom Error Pages**: Blocked requests receive user-friendly error messages
- Applied to both frontend and content distributions
- **IP Allowlisting** (Optional): Additional IP allowlisting can be configured using the provided script (works alongside geo-blocking)

### S3 Bucket Security

- **Private Buckets**: All S3 buckets are private with public access blocked
- **CloudFront OAI**: Only CloudFront can access S3 buckets via Origin Access Identity
- **No Direct Access**: Direct S3 URLs are blocked

### API Authentication

- **Admin Endpoints**: Protected by Cognito User Pool authentication
- **Player Endpoints**: Public (by design for player access)
- **IAM Roles**: Lambda functions use least-privilege IAM roles

### Clean Up Old Distributions

If you have old CloudFront distributions from previous deployments, you can safely delete them after verifying the new ones are working:

**Identify Old Distributions:**
```bash
# List all distributions and identify which are old
aws cloudfront list-distributions \
  --query 'DistributionList.Items[?contains(Comment, `Consistency Tracker`)].{Id:Id,Domain:DomainName,Comment:Comment,Status:Status}' \
  --output table
```

**Current Active Distributions (DO NOT DELETE):**
- `E11CYNQ91MDSZR` - Frontend (d346yye80fnvlo.cloudfront.net)
- `E1986A93DSMC7O` - Content (d1rt8gejjf42oo.cloudfront.net)

**Old Distributions (Safe to Delete):**
- `E1DD2PQWY0P8ES` - Old frontend (djg551w466uwn.cloudfront.net)
- `E17RBWRSIUG3PC` - Old content (d1i5t1dkk2vdm1.cloudfront.net)

**To Delete Old Distributions:**

1. **Disable the distribution** (required before deletion):
   - Go to CloudFront console
   - Select the old distribution
   - Click **Disable** and wait 15-20 minutes for it to be disabled

2. **Delete the distribution**:
   - Once disabled, click **Delete**
   - Confirm deletion

**Note**: CloudFront distributions must be disabled before deletion, which takes 15-20 minutes. You can disable multiple distributions at once, then delete them all after they're disabled.

## After Deployment

### WAF Geographic Restriction

The WAF is configured to only allow IP addresses from the United States. This is enforced by a GeoMatch rule with the highest priority (0).

**What this means:**
- ✅ IPs from the US are allowed
- ❌ IPs from outside the US are blocked with a custom error page
- The error page explains that access is restricted to US IPs

**To verify geographic restriction:**
```bash
# Check WAF rules
aws wafv2 get-web-acl \
  --scope CLOUDFRONT \
  --region us-east-1 \
  --name "CloudFrontWebACL-vqZX7V0FN6hP" \
  --id "e67a2f34-b2c8-497b-aa10-67ee0a9d0e4d" \
  --output json | jq '.WebACL.Rules[] | select(.Name == "USOnlyGeoMatch")'
```

**To modify allowed countries:**
Update the `country_codes` array in `aws/stacks/storage_stack.py` in the `USOnlyGeoMatch` rule, then redeploy:
```bash
cdk deploy ConsistencyTracker-Storage
```

### Configure IP Allowlisting (Optional - Additional Layer)

If you want to add additional IP-based restrictions on top of geographic blocking, you can use the provided script:

```bash
python scripts/utilities/configure_ip_restriction.py
```

**Recommended**: This Python script provides a comprehensive solution for IP restrictions with interactive mode, undo capability, and support for both API Gateway and CloudFront WAFs.

**Use cases:**
- Complete lockdown: Restrict both frontend and API access to specific IPs
- Allow specific IPs outside the US (if needed)
- Add an additional layer of IP-based access control
- Temporarily allow access from non-US IPs
- API-only or CloudFront-only restrictions

**Key features:**
- ✅ Interactive menu for easy configuration
- ✅ Auto-detect current IP address
- ✅ IPv4 and IPv6 support
- ✅ Undo capability to remove restrictions
- ✅ Preserves existing WAF rules
- ✅ Built-in propagation timer
- ✅ Automatic retry on transient errors

**Quick start:**
```bash
# Interactive mode (recommended)
python scripts/utilities/configure_ip_restriction.py

# Auto-detect and use current IP
python scripts/utilities/configure_ip_restriction.py --auto-detect-ip

# Remove restrictions
python scripts/utilities/configure_ip_restriction.py --remove-restrictions
```

For complete documentation, see [SCRIPTS.md](./SCRIPTS.md#configure_ip_restrictionpy).

**Legacy script** (CloudFront only):
```bash
./aws/scripts/update-waf-ip-allowlist.sh
```
4. Set the default action to "Block" to enforce IP restriction

**Important Notes:**
- WAF rule changes take 2-3 minutes to propagate globally
- The script preserves existing WAF rules (geo-blocking, rate limiting, managed rules)
- Geographic restriction is the primary access control; IP allowlisting is additional
- See `documents/deployment/SCRIPTS.md` for detailed documentation

### Create First Admin User

After deploying the AuthStack, create the first admin user:

**Option 1: Using Python script (recommended)**
```bash
# Edit configuration at top of script first
python aws/create_admin_user.py
```

The script will:
1. Automatically get the User Pool ID from CloudFormation stack
2. Create the admin user with your configured email and password
3. Add the user to the Admins group
4. Handle errors gracefully (e.g., user already exists)

**Option 2: Using AWS Console**
1. Go to AWS Console → Cognito → User Pools
2. Select "ConsistencyTracker-AdminPool"
3. Create a new user
4. Add the user to the "Admins" group

**Option 3: Using AWS CLI**
```bash
# First, get the User Pool ID
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name ConsistencyTracker-Auth \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

# Create the admin user
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username admin@example.com \
  --user-attributes Name=email,Value=admin@example.com \
  --temporary-password <TEMP_PASSWORD> \
  --message-action SUPPRESS \
  --region us-east-2

# Add to Admins group
aws cognito-idp admin-add-user-to-group \
  --user-pool-id $USER_POOL_ID \
  --username admin@example.com \
  --group-name club-admins \
  --region us-east-2
```

**Note**: The admin user creation script only needs to be run once (or when creating additional admin users). It does NOT need to be run on every deployment.

### Verify Tables

Check that all DynamoDB tables were created:
- ConsistencyTracker-Players
- ConsistencyTracker-Activities
- ConsistencyTracker-Tracking
- ConsistencyTracker-Reflections
- ConsistencyTracker-ContentPages
- ConsistencyTracker-Teams
- ConsistencyTracker-Coaches
- ConsistencyTracker-ClubAdmins

## Notes

### Password Policy

The Cognito User Pool is configured with:
- Minimum 12 characters
- Requires uppercase, lowercase, and numbers
- Password history (prevents reuse)

**Note**: The "no repeating characters" requirement cannot be enforced directly by Cognito. This would require a Lambda trigger (can be added in Phase 2).

### Multi-Tenant Support

All tables include `teamId` for multi-tenant isolation:
- Each table has a GSI on `teamId` for efficient team-based queries
- Data is isolated per team
- Team configuration stored in Team/Config table

### Point-in-Time Recovery

All DynamoDB tables have point-in-time recovery enabled for additional data protection:
- Enables point-in-time restore to any second within the last 35 days
- Protects against accidental writes or deletes
- Works in conjunction with RETAIN policy for comprehensive data protection
- No additional cost (included with DynamoDB on-demand pricing)

## Troubleshooting

### CDK Bootstrap Error

If you get an authentication error, verify your AWS credentials:
```bash
aws sts get-caller-identity
```

### Import Errors

Make sure you're in the virtual environment and dependencies are installed:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Stack Deployment Errors

Check CloudFormation console for detailed error messages. Common issues:
- Insufficient IAM permissions
- Resource name conflicts
- Region-specific service availability

### CloudFront 403 Errors After Frontend Deployment

If you see `403 Forbidden` errors even after uploading frontend files:

1. **Check CloudFront Origin Configuration:**
   ```bash
   aws cloudfront get-distribution-config --id E11CYNQ91MDSZR --output json | \
     jq '.DistributionConfig.Origins.Items[0]'
   ```

2. **Verify Origin Uses S3 Endpoint (Not Website Endpoint):**
   - ✅ Correct: `consistency-tracker-frontend-us-east-1.s3.amazonaws.com`
   - ❌ Wrong: `consistency-tracker-frontend-us-east-1.s3-website-us-east-1.amazonaws.com`

3. **If Using Website Endpoint, Update Distribution:**
   The origin should use `S3OriginConfig` with `OriginAccessIdentity`, not `CustomOriginConfig`.
   
   This can happen if the distribution was manually modified or if there was a CDK synthesis issue. The CDK code correctly configures `origins.S3Origin` with OAI, so redeploying the Storage stack should fix it:
   ```bash
   cdk deploy ConsistencyTracker-Storage
   ```

4. **Verify S3 Bucket Policy:**
   ```bash
   aws s3api get-bucket-policy --bucket consistency-tracker-frontend-us-east-1 --output json | jq -r '.Policy' | jq '.'
   ```
   The policy should allow the CloudFront OAI to access the bucket.

5. **Check WAF Configuration:**
   If IP allowlisting is enabled, ensure your IP is in the allowlist:
   ```bash
   ./aws/scripts/update-waf-ip-allowlist.sh
   ```

### Frontend Files Not Updating

If changes to frontend files aren't appearing:

1. **Rebuild the application:**
   ```bash
   cd app
   npm run build
   ```

2. **Re-upload to S3:**
   ```bash
   aws s3 sync dist/ s3://consistency-tracker-frontend-us-east-1/ --delete
   ```

3. **Invalidate CloudFront cache:**
   ```bash
   aws cloudfront create-invalidation --distribution-id E11CYNQ91MDSZR --paths "/*"
   ```

4. **Wait for invalidation to complete** (1-2 minutes), then hard refresh your browser.

