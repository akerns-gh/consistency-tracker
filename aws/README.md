# CDK Infrastructure Setup

This directory contains the AWS CDK infrastructure code for the Consistency Tracker application.

## Prerequisites

1. **AWS CLI configured**: `aws configure`
2. **CDK CLI installed**: `npm install -g aws-cdk`
3. **CDK bootstrapped**: `cdk bootstrap aws://707406431671/us-east-2`
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

### 3. Verify CDK Installation

```bash
cdk --version
```

### 4. Bootstrap CDK (if not already done)

```bash
cdk bootstrap aws://707406431671/us-east-2
```

## Quick Deployment

### One-Command Deployment

The easiest way to deploy Phase 1 infrastructure:

```bash
python aws/deploy.py
```

This script will:
1. Check prerequisites (AWS CLI, CDK, Python)
2. Set up Python virtual environment (if needed)
3. Install dependencies
4. Bootstrap CDK (if needed)
5. Synthesize CDK templates
6. Deploy Phase 1 stacks (Database and Auth)
7. Verify deployment

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
- Region: `us-east-2`

## After Deployment

### Create First Admin User

After deploying the AuthStack, create the first admin user:

1. Go to AWS Console → Cognito → User Pools
2. Select "ConsistencyTracker-AdminPool"
3. Create a new user
4. Add the user to the "Admins" group

Or use AWS CLI:
```bash
aws cognito-idp admin-create-user \
  --user-pool-id <USER_POOL_ID> \
  --username admin@example.com \
  --user-attributes Name=email,Value=admin@example.com \
  --temporary-password <TEMP_PASSWORD> \
  --message-action SUPPRESS

aws cognito-idp admin-add-user-to-group \
  --user-pool-id <USER_POOL_ID> \
  --username admin@example.com \
  --group-name Admins
```

### Verify Tables

Check that all DynamoDB tables were created:
- ConsistencyTracker-Players
- ConsistencyTracker-Activities
- ConsistencyTracker-Tracking
- ConsistencyTracker-Reflections
- ConsistencyTracker-ContentPages
- ConsistencyTracker-Teams

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

All DynamoDB tables have point-in-time recovery enabled for data protection.

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

