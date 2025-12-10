# True Lacrosse Consistency Tracker

A web-based consistency tracking application for youth lacrosse teams that allows players to track daily habits, view their progress, and compare performance with teammates through a leaderboard.

## Project Overview

This application helps coaches track player consistency across key activities (sleep, hydration, training, etc.) and provides players with a simple interface to log their daily habits and view their progress over time.

## Architecture

- **Frontend**: React.js (static site hosted on S3 + CloudFront)
- **Backend**: AWS Lambda functions (Python) via API Gateway
- **Database**: AWS DynamoDB (serverless, on-demand pricing)
- **Authentication**: AWS Cognito (for coaches/admins)
- **Infrastructure**: AWS CDK (Python)
- **Domain**: repwarrior.net (Route 53)

## Project Structure

```
consistency-tracker/
├── aws/                    # AWS CDK infrastructure code
│   ├── app.py             # CDK app entry point
│   ├── cdk.json           # CDK configuration
│   ├── requirements.txt   # Python dependencies
│   └── stacks/           # CDK stack definitions
│       ├── database_stack.py  # DynamoDB tables
│       ├── auth_stack.py      # Cognito User Pool
│       ├── api_stack.py       # API Gateway & Lambda
│       ├── storage_stack.py   # S3 & CloudFront
│       └── dns_stack.py       # Route 53
├── app/              # React application (Phase 3)
├── prototype/             # HTML prototype (Phase 0 - complete)
└── docs/                  # Documentation
```

## Prerequisites

- AWS account with administrative access
- Domain: repwarrior.net (configured in Route 53)
- AWS CLI configured: `aws configure`
- CDK CLI installed: `npm install -g aws-cdk`
- Python 3.9+ installed
- Node.js 18+ installed
- CDK bootstrapped: `cdk bootstrap aws://ACCOUNT-ID/us-east-2`

## Getting Started

### Phase 0: HTML Prototype ✅ COMPLETE
The HTML prototype has been completed and validated all requirements.

### Phase 1: Infrastructure Setup (Current)
Set up AWS CDK infrastructure, DynamoDB tables, and Cognito authentication.

```bash
# Set up Python virtual environment
cd aws
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Synthesize CloudFormation templates
cdk synth

# Deploy stacks
cdk deploy --all
```

### Phase 2: Backend API Development
Develop Lambda functions and API Gateway endpoints.

### Phase 3: Frontend Foundation
Build React application and player-facing features.

### Phase 4: Admin Dashboard
Implement admin dashboard and authentication flows.

### Phase 5: Content Management
Build content management system with WYSIWYG editor.

### Phase 6: Testing, Polish & Deployment
Final testing, optimization, and production deployment.

## Configuration

### Environment Variables
Create a `.env` file in the `aws/` directory (not committed to git):
- `DOMAIN_NAME=repwarrior.net`
- `AWS_REGION=us-east-2`
- `AWS_ACCOUNT_ID=707406431671`

### Multi-Tenant Architecture
The application supports multiple teams. Each team has:
- Isolated data (players, activities, content)
- Team-specific configuration
- Team-scoped admin access

All DynamoDB tables include `teamId` for data isolation, with Global Secondary Indexes (GSI) for efficient team-based queries.

## Development

### CDK Development
```bash
cd aws
source .venv/bin/activate
cdk synth          # Generate CloudFormation templates
cdk diff           # Show differences
cdk deploy         # Deploy changes
cdk destroy        # Tear down infrastructure
```

### Frontend Development
```bash
cd app
npm install
npm start          # Development server
npm run build      # Production build
```

## Deployment

### Quick Deployment

Deploy Phase 1 infrastructure using the automated script:

```bash
./aws/deploy.sh
```

This script:
- ✅ Only deploys/updates (never destroys)
- ✅ Protects DynamoDB data with RETAIN policy
- ✅ Handles all setup automatically
- ✅ Verifies deployment success

### Manual Deployment

1. Deploy infrastructure: `cdk deploy --all`
2. Create initial admin user in Cognito User Pool (via AWS Console)
3. Deploy frontend: `./scripts/deploy-frontend.sh`
   - This script builds the app, uploads to S3, and invalidates CloudFront cache
   - Alternatively: `cd app && npm run build && aws s3 sync dist/ s3://consistency-tracker-frontend-us-east-1/ --delete`
4. Configure DNS in Route 53 (if not already done)

### Data Protection

**Important:** All DynamoDB tables are protected with `RETAIN` policy:
- ✅ Tables are **NOT deleted** if stacks are destroyed
- ✅ Data **persists** even if infrastructure is removed
- ✅ Deployment scripts **never destroy** resources
- ✅ Your data is **safe from accidental deletion**

See [aws/DEPLOYMENT_README.md](./aws/DEPLOYMENT_README.md) for detailed data protection information.

## Documentation

- [Implementation Plan](./docs/build/implementation-plan.md)
- [Phase 0: Prototype](./docs/build/phase-0-prototype.md) ✅
- [Phase 1: Infrastructure](./docs/build/phase-1-infrastructure.md) (Current)
- [Phase 2: Backend](./docs/build/phase-2-backend.md)
- [Phase 3: Frontend](./docs/build/phase-3-frontend.md)
- [Phase 4: Admin](./docs/build/phase-4-admin.md)
- [Phase 5: Content](./docs/build/phase-5-content.md)
- [Phase 6: Deployment](./docs/build/phase-6-deployment.md)
- [Requirements](./docs/requirements/consistency-tracker-requirements.md)

## License

Internal use only - True Lacrosse Consistency Tracker

