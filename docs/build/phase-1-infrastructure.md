# Phase 1: Project Foundation & Infrastructure Setup

## Overview
Set up the project structure, AWS CDK infrastructure, and core AWS services (DynamoDB, Cognito). This phase establishes the foundation for the entire application.

**Estimated Time:** 4-6 hours

## 1.1 Project Structure Initialization
- Create root project structure with separate directories for CDK infrastructure and React frontend
- Set up Git repository with `.gitignore` for Python, Node.js, and AWS
- Initialize package.json and Python virtual environment

**Files to create:**
- `aws/` - AWS CDK infrastructure code
- `app/` - React application
- `README.md` - Project overview and setup instructions
- `.gitignore` - Exclude node_modules, __pycache__, .env files, CDK artifacts

## 1.2 AWS CDK Infrastructure Setup
- Initialize CDK app with Python
- Configure `cdk.json` with proper settings
- Set up `requirements.txt` with CDK dependencies
- Create stack structure: `stacks/` directory with separate stack files

**Files to create:**
- `aws/app.py` - CDK app entry point
- `aws/cdk.json` - CDK configuration
- `aws/requirements.txt` - Python dependencies (aws-cdk-lib, constructs, boto3)
- `aws/stacks/__init__.py`
- `aws/stacks/database_stack.py` - DynamoDB tables
- `aws/stacks/auth_stack.py` - Cognito User Pool
- `aws/stacks/api_stack.py` - API Gateway and Lambda functions
- `aws/stacks/storage_stack.py` - S3 buckets and CloudFront
- `aws/stacks/dns_stack.py` - Route 53 configuration

## 1.3 Database Stack (DynamoDB)
- Create all 7 DynamoDB tables with proper schemas:
  - Club table (clubId as partition key) - NEW
  - Team table (teamId as partition key, clubId GSI)
  - Player table (playerId as partition key, clubId GSI, teamId GSI)
  - Activity table (activityId as partition key, clubId GSI, teamId GSI)
  - Tracking table (composite key: playerId#weekId#date, clubId GSI, teamId GSI)
  - Reflection table (composite key: playerId#weekId, clubId GSI, teamId GSI)
  - ContentPages table (pageId as partition key, clubId GSI, teamId GSI)
- Configure Global Secondary Indexes (GSI) for efficient queries
- Enable point-in-time recovery
- Set on-demand billing mode

**Key implementation:**
- `aws/stacks/database_stack.py` - Define all tables with proper key schemas and GSIs
- Club table is the foundation for multi-club support
- All tables include clubId for primary data isolation

## 1.4 Authentication Stack (Cognito)
- Create Cognito User Pool for coach/admin authentication
- Configure password policy (min 12 chars, uppercase, lowercase, number)
- Set up email verification
- Create app client for web application
- Configure JWT token expiration (1 hour access, 30 day refresh)
- Create Cognito User Group for administrators (e.g., "Admins")
- Configure group-based role assignment (admin vs regular user)
- Add custom attributes for club and team association:
  - `custom:clubId` (string, mutable) - Primary club association
  - `custom:teamIds` (string, comma-separated, mutable, optional) - Specific teams

**Key implementation:**
- `aws/stacks/auth_stack.py` - Cognito User Pool with proper policies, admin user group, and custom attributes

