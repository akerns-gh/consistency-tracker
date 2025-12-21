# True Lacrosse Consistency Tracker

A web-based consistency tracking application for youth lacrosse teams that allows players to track daily habits, view their progress, and compare performance with teammates through a leaderboard.

## Project Overview

This application helps coaches track player consistency across key activities (sleep, hydration, training, etc.) and provides players with a simple interface to log their daily habits and view their progress over time.

## Architecture

- **Frontend**: React.js (static site hosted on S3 + CloudFront)
- **Backend**: Flask applications (Python) running on AWS Lambda via API Gateway
- **Database**: AWS DynamoDB (serverless, on-demand pricing)
- **Authentication**: AWS Cognito (for coaches/admins)
- **Email**: AWS SES (Simple Email Service) with Proton Mail custom domain
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
│       ├── ses_stack.py       # SES email configuration
│       ├── api_stack.py       # API Gateway & Lambda
│       ├── storage_stack.py   # S3 & CloudFront
│       └── dns_stack.py       # Route 53
├── app/                   # React application
├── prototype/             # HTML prototype (Phase 0 - complete)
└── documents/             # Documentation
```

## Prerequisites

- AWS account with administrative access
- Domain: repwarrior.net (configured in Route 53)
- AWS CLI configured: `aws configure`
- CDK CLI installed: `npm install -g aws-cdk`
- Python 3.9+ installed
- Node.js 18+ installed
- CDK bootstrapped: `cdk bootstrap aws://ACCOUNT-ID/us-east-1`

## Getting Started

### Phase 0: HTML Prototype ✅ COMPLETE
The HTML prototype has been completed and validated all requirements.

### Quick Start

The application is fully deployed and operational. See [Deployment Guide](./documents/deployment/DEPLOYMENT_README.md) for detailed setup instructions.

```bash
# Deploy infrastructure
cd aws
./deploy.sh

# Deploy frontend
cd ..
./scripts-frontend/deploy-frontend.sh
```

## Configuration

### Environment Variables
Configuration is managed in `aws/app.py`. Key settings:
- `DOMAIN_NAME=repwarrior.net`
- `AWS_REGION=us-east-1`
- `HOSTED_ZONE_ID` (Route 53 hosted zone)

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

Deploy infrastructure using the automated script:

```bash
cd aws
./deploy.sh
```

This script:
- ✅ Only deploys/updates (never destroys)
- ✅ Protects DynamoDB data with RETAIN policy
- ✅ Handles all setup automatically (CloudFront certs, API domain, email setup)
- ✅ Verifies deployment success

See [Deployment Guide](./documents/deployment/DEPLOYMENT_README.md) for detailed instructions.

### Data Protection

**Important:** All DynamoDB tables are protected with `RETAIN` policy:
- ✅ Tables are **NOT deleted** if stacks are destroyed
- ✅ Data **persists** even if infrastructure is removed
- ✅ Deployment scripts **never destroy** resources
- ✅ Your data is **safe from accidental deletion**

See [Deployment Guide](./documents/deployment/DEPLOYMENT_README.md) for detailed data protection information.

## Documentation

### Deployment & Operations
- [Deployment Guide](./documents/deployment/DEPLOYMENT_README.md) - Complete deployment instructions
- [Deployment Scripts](./documents/deployment/SCRIPTS.md) - Script documentation
- [Seed Data](./documents/deployment/SEED_DATA.md) - Data seeding guide
- [Admin Manual](./documents/operations/ADMIN_MANUAL.md) - Admin user management

### Configuration
- [API Configuration](./documents/configuration/API_CONFIGURATION.md) - API setup and endpoints
- [Email Setup](./documents/email/EMAIL_SETUP.md) - Email domain configuration
- [SES Setup](./documents/email/SES_SETUP.md) - AWS SES configuration
- [Email Quick Start](./documents/email/QUICKSTART.md) - Quick email setup guide

### Development
- [Implementation Plan](./documents/build/implementation-plan.md) - Project phases
- [Phase Documentation](./documents/build/) - Implementation phases
- [Requirements](./documents/requirements/consistency-tracker-requirements.md) - Project requirements
- [Prototype](./documents/PROTOTYPE.md) - HTML prototype documentation

## License

Internal use only - True Lacrosse Consistency Tracker

