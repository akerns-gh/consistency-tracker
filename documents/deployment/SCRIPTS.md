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
   python scripts/utilities/configure_ip_restriction.py
   ```
   Restricts access to specific IP addresses for complete lockdown (API Gateway + CloudFront)

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
./aws/scripts/update-waf-ip-allowlist.sh
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

## configure_ip_restriction.py

**Recommended**: This is the preferred script for IP restrictions. It provides a complete solution for locking down both API Gateway and CloudFront WAFs.

A comprehensive Python script for configuring IP allowlist restrictions on both API Gateway and CloudFront WAFs. This script provides complete lockdown capabilities with an interactive menu and undo functionality.

### Key Features

- ✅ **Complete Lockdown**: Applies IP restrictions to both API Gateway WAF and CloudFront WAF simultaneously
- ✅ **Interactive Menu**: User-friendly menu for configuring or removing restrictions
- ✅ **IPv4 and IPv6 Support**: Handles both IPv4 and IPv6 addresses
- ✅ **Auto-Detect IP**: Automatically detects your current public IP address
- ✅ **Undo Capability**: Easily remove IP restrictions and restore default access
- ✅ **Preserves Existing Rules**: Does not modify existing WAF rules (only adds/updates IPAllowlist rule)
- ✅ **Retry Logic**: Automatically retries on transient AWS WAF errors
- ✅ **Propagation Timer**: Built-in timer to track WAF propagation time
- ✅ **Flexible Configuration**: Can target API Gateway only, CloudFront only, or both

### What It Does

When configuring IP restrictions:
1. Creates or updates IP sets with allowed IP addresses (separate sets for IPv4 and IPv6)
2. Adds an `IPAllowlist` rule to the Web ACL(s) at the highest available priority
3. Sets default action to `Block` (restrictive mode - only allowlisted IPs can access)
4. Preserves all existing WAF rules exactly as they are
5. Includes custom response bodies (required for CloudFront WAF)

When removing IP restrictions:
1. Removes the `IPAllowlist` rule from the Web ACL(s)
2. Sets default action back to `Allow` (open access)
3. Optionally deletes IP sets (or keeps them for reuse)
4. Preserves all existing WAF rules

### Prerequisites

- Python 3.9+ (Python 3.10+ recommended)
- AWS CLI installed and configured with appropriate credentials
- `boto3` Python library (install with `pip install boto3`)
- AWS permissions to manage WAFv2 resources

### Usage

#### Interactive Mode (Recommended)

Run the script without arguments to access the interactive menu:

```bash
python scripts/utilities/configure_ip_restriction.py
```

The interactive menu provides:
1. **Configure IP restrictions (lockdown)** - Prompts for IPv4 and IPv6 addresses
2. **Remove IP restrictions (undo lockdown)** - Removes restrictions and restores access
3. **Exit**

#### Command-Line Mode

**Auto-detect current IP:**
```bash
python scripts/utilities/configure_ip_restriction.py --auto-detect-ip
```

**Specify IP addresses:**
```bash
python scripts/utilities/configure_ip_restriction.py --ips "203.0.113.1/32,198.51.100.1/32"
```

**Only restrict API Gateway (not CloudFront):**
```bash
python scripts/utilities/configure_ip_restriction.py --api-only --ips "203.0.113.1/32"
```

**Only restrict CloudFront (not API Gateway):**
```bash
python scripts/utilities/configure_ip_restriction.py --cloudfront-only --ips "203.0.113.1/32"
```

**Remove IP restrictions:**
```bash
python scripts/utilities/configure_ip_restriction.py --remove-restrictions
```

**Remove restrictions and delete IP sets:**
```bash
python scripts/utilities/configure_ip_restriction.py --remove-restrictions --delete-ip-sets
```

### Configuration Options

| Option | Description |
|--------|-------------|
| `--ips` | Comma-separated list of IP addresses in CIDR format |
| `--auto-detect-ip` | Automatically detect and use current public IP address |
| `--api-only` | Only restrict API Gateway WAF (not CloudFront) |
| `--cloudfront-only` | Only restrict CloudFront WAF (not API Gateway) |
| `--remove-restrictions` | Remove IP restrictions (undo lockdown) |
| `--delete-ip-sets` | Delete IP sets when removing restrictions (default: keep for reuse) |
| `--api-web-acl-name` | Name of API Gateway Web ACL (auto-detects if not specified) |
| `--cloudfront-web-acl-name` | Name of CloudFront Web ACL (auto-detects if not specified) |
| `--region` | AWS region for API Gateway (default: us-east-1) |

### How It Works

#### Configuration Flow

1. **IP Address Collection**:
   - Interactive mode: Prompts separately for IPv4 and IPv6 addresses
   - Auto-detect: Detects current public IPv4 address
   - Command-line: Parses comma-separated IP addresses

2. **IP Set Management**:
   - Creates separate IP sets for API Gateway (REGIONAL scope) and CloudFront (CLOUDFRONT scope)
   - Creates separate sets for IPv4 and IPv6 addresses
   - Updates existing IP sets if they already exist

3. **Web ACL Updates**:
   - Finds Web ACLs by name pattern (e.g., `ApiGatewayWebACL-*`, `CloudFrontWebACL-*`)
   - Preserves all existing rules exactly as they are (using deep copy)
   - Adds/updates `IPAllowlist` rule at the highest available priority
   - Sets default action to `Block` for restrictions, `Allow` for removal
   - Includes custom response bodies (required for CloudFront WAF)

4. **Error Handling**:
   - Automatic retry with exponential backoff for transient AWS errors
   - Fresh lock token retrieval on each retry
   - Clear error messages with available Web ACL listings

5. **Propagation Timer**:
   - Starts automatically after configuration completes
   - Counts up showing elapsed time (up to 5 minutes)
   - Helps track when WAF changes should be propagated

#### Priority Handling

The script intelligently handles rule priorities:
- **If priority 0 is available**: IPAllowlist rule is added at priority 0 (highest)
- **If priority 0 is taken**: IPAllowlist rule is added at the next available priority
- **Existing rules**: All existing rules keep their original priorities (no modification)

### Use Cases

1. **Complete Lockdown**: Restrict both frontend and API access to specific IPs
   ```bash
   python scripts/utilities/configure_ip_restriction.py --ips "203.0.113.1/32"
   ```

2. **API-Only Restriction**: Restrict only API access (frontend remains accessible)
   ```bash
   python scripts/utilities/configure_ip_restriction.py --api-only --ips "203.0.113.1/32"
   ```

3. **Temporary Access**: Quickly allow your current IP
   ```bash
   python scripts/utilities/configure_ip_restriction.py --auto-detect-ip
   ```

4. **Remove Restrictions**: Undo lockdown and restore normal access
   ```bash
   python scripts/utilities/configure_ip_restriction.py --remove-restrictions
   ```

5. **Multiple IPs**: Allow multiple IP addresses
   ```bash
   python scripts/utilities/configure_ip_restriction.py --ips "203.0.113.1/32,198.51.100.1/32,2001:db8::1/128"
   ```

### Important Notes

- **Propagation Time**: WAF rule changes take 2-3 minutes to propagate globally. The script includes a built-in timer to track this.
- **Existing Rules**: The script preserves all existing WAF rules (geographic restrictions, rate limits, managed rules, etc.) without modification.
- **IP Set Reuse**: By default, IP sets are kept when removing restrictions, allowing you to quickly re-enable them later.
- **Lockout Prevention**: The script adds your IP to the allowlist before setting default action to Block, preventing lockout.
- **Custom Response Bodies**: CloudFront WAF custom response bodies are automatically preserved during updates.

### Comparison with update-waf-ip-allowlist.sh

| Feature | configure_ip_restriction.py | update-waf-ip-allowlist.sh |
|---------|----------------------------|----------------------------|
| **Scope** | API Gateway + CloudFront | CloudFront only |
| **Interactive Mode** | ✅ Yes | ❌ No |
| **Undo Capability** | ✅ Yes | ❌ No |
| **IPv6 Support** | ✅ Yes | ✅ Yes |
| **Auto-detect IP** | ✅ Yes | ✅ Yes |
| **Preserves Rules** | ✅ Yes (deep copy) | ⚠️ May modify |
| **Retry Logic** | ✅ Yes | ❌ No |
| **Propagation Timer** | ✅ Yes | ❌ No |
| **IP Set Management** | ✅ Separate for each scope | ⚠️ Single scope |

**Recommendation**: Use `configure_ip_restriction.py` for all IP restriction needs. It provides a more comprehensive and user-friendly solution.

### Troubleshooting

- **"Web ACL not found"**: The script will list available Web ACLs. Use `--api-web-acl-name` or `--cloudfront-web-acl-name` to specify explicitly.
- **"WAFUnavailableEntityException"**: The script automatically retries. If it persists, wait a few minutes and try again.
- **"Duplicate priority"**: The script automatically finds the next available priority if priority 0 is taken.
- **"Custom response body not found"**: The script automatically preserves custom response bodies. This error should not occur.
- **403 errors after configuration**: Wait for the propagation timer to complete (2-3 minutes). The timer helps track this.

### Example Output

```
============================================================
WAF IP Restriction Configuration
============================================================

What would you like to do?

  1. Configure IP restrictions (lockdown)
  2. Remove IP restrictions (undo lockdown)
  3. Exit

Enter your choice (1-3): 1
ℹ️  Interactive mode: Please enter allowed IP addresses

Enter allowed IPv4 addresses (one per line, or comma-separated)
Format: IP address in CIDR format (e.g., 203.0.113.1/32)
Press Enter on empty line when done, or 'q' to quit

IPv4> 203.0.113.1/32
IPv4> 

Enter allowed IPv6 addresses (optional, one per line, or comma-separated)
Format: IP address in CIDR format (e.g., 2001:db8::1/128)
Press Enter on empty line to skip, or 'q' to quit

IPv6> 

============================================================
✅ Configuration Summary
============================================================

Allowed IP addresses:
  ✅ IPv4: 203.0.113.1/32

WAF Configuration:
  ✅ Configured API Gateway WAF (REGIONAL scope)
  ✅ Configured CloudFront WAF (CLOUDFRONT scope)

Settings:
  ✅ Default action: Block
  ✅ Allowlist rule priority: 0 (highest)

⚠️  Note: WAF rule changes may take 2-3 minutes to propagate.

ℹ️  Starting propagation timer...
Press Ctrl+C to stop the timer and exit

⏱️  Elapsed time: 1m 23s
```

