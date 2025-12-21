# Scripts

This directory contains utility scripts for managing the Consistency Tracker application.

## Deployment Order

These scripts should be run in the following order for a complete deployment:

1. **Infrastructure Deployment** (not in this directory):
   ```bash
   ./aws/deploy.sh
   ```
   Deploys all CDK stacks (Database, Auth, API, DNS, Storage)
   - Also runs post-deploy configuration automatically (CloudFront certs/aliases + API custom domain)

2. **Admin User Creation** (not in this directory):
   ```bash
   python aws/create_admin_user.py
   ```
   Creates the first admin user in Cognito

3. **Frontend Deployment**:
   ```bash
   ./scripts/deploy-frontend.sh
   ```
   Builds and deploys the React application to S3 and CloudFront

4. **Seed Data from CSV** (optional):
   ```bash
   python aws/seed_from_csv.py \
    --clubs data/clubs.csv \
    --teams data/teams.csv \
    --players data/players.csv \
    --activities data/activities.csv \
    --content-pages data/content_pages.csv
   ```

5. **IP Allowlisting** (optional):
   ```bash
   ./scripts/update-waf-ip-allowlist.sh
   ```
   Restricts access to specific IP addresses

See [aws/DEPLOYMENT_README.md](../aws/DEPLOYMENT_README.md) for complete deployment instructions.

## deploy-frontend.sh

Builds and deploys the frontend application to S3 and CloudFront.

### What it does:

1. **Builds the React application** - Runs `npm run build` in the `app` directory
2. **Uploads to S3** - Syncs the `dist/` folder to the S3 bucket
3. **Invalidates CloudFront cache** - Creates a cache invalidation to serve new files immediately
4. **Verifies origin configuration** - Checks that CloudFront is using the correct S3 origin

### Prerequisites:

- AWS CLI installed and configured
- Node.js and npm installed
- Project dependencies installed (`npm install` in `app/` directory)

### Usage:

```bash
./scripts/deploy-frontend.sh
```

### Configuration:

The script uses these default values (defined at the top of the script):
- **S3 Bucket**: `consistency-tracker-frontend-us-east-1`
- **CloudFront Distribution ID**: `E11CYNQ91MDSZR`

To change these, edit the configuration variables at the top of the script.

## update-waf-ip-allowlist.sh

**Note**: The WAF is configured to only allow IP addresses from the United States by default. This script provides additional IP allowlisting that works alongside the geographic restriction. Use this script if you need to:
- Allow specific IPs outside the US
- Add an additional layer of IP-based access control
- Temporarily allow access from non-US IPs

Automatically updates the AWS WAF IP allowlist with your current IP addresses (both IPv4 and IPv6).

### What it does:

1. **Detects your current IP addresses** - Automatically detects your IPv4 and IPv6 addresses
2. **Creates/updates IP sets** - Creates or updates AWS WAF IP sets for both IPv4 and IPv6
3. **Updates Web ACL** - Updates the WAF Web ACL to allow traffic from your IPs
4. **Enforces IP restriction** - Sets default action to "Block" so only your IPs can access the site

### Prerequisites:

- AWS CLI installed and configured with appropriate credentials
- `jq` installed (`brew install jq` on macOS)
- `curl` installed (usually pre-installed)

### Usage:

```bash
./scripts/update-waf-ip-allowlist.sh
```

### Configuration:

The script uses the following default values (defined at the top of the script):

- **Web ACL Name**: `CloudFrontWebACL-vqZX7V0FN6hP`
- **IPv4 IP Set Name**: `Allowlist`
- **IPv6 IP Set Name**: `AllowlistIPv6`
- **Region**: `us-east-1` (required for CloudFront WAF)
- **Scope**: `CLOUDFRONT`

To change these, edit the configuration variables at the top of the script.

### How it works:

1. The script detects your current IPv4 and IPv6 addresses using `ifconfig.me`
2. It checks if IP sets exist, and creates or updates them accordingly
3. It fetches the current Web ACL configuration
4. It updates the "Allowlist" rule to include both IP sets using an OR statement
5. It sets the Allowlist rule to priority 0 (highest priority)
6. It sets the default action to "Block" to enforce IP restriction

### Important Notes:

- **Propagation Time**: WAF rule changes can take 2-3 minutes to propagate globally
- **IP Changes**: If your IP address changes (e.g., you're on a different network), run this script again
- **Lockout Risk**: If you change the default action to "Block" before adding your IP to the allowlist, you may lock yourself out. This script adds your IP first, then sets the default to Block.

### Troubleshooting:

- **"Web ACL not found"**: Check that the Web ACL name matches your actual Web ACL name
- **"jq not found"**: Install jq: `brew install jq` (macOS) or `apt-get install jq` (Linux)
- **"AWS CLI not installed"**: Install AWS CLI and configure credentials
- **403 errors after running**: Wait 2-3 minutes for WAF changes to propagate

