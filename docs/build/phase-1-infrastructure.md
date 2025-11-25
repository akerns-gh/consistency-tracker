# Phase 1: Project Foundation & Infrastructure Setup

## Overview
Set up the project structure, AWS CDK infrastructure, and core AWS services (DynamoDB, Cognito). This phase establishes the foundation for the entire application.

**Estimated Time:** 4-6 hours

## 1.1 Project Structure Initialization
- Create root project structure with separate directories for CDK infrastructure and React frontend
- Set up Git repository with `.gitignore` for Python, Node.js, and AWS
- Initialize package.json and Python virtual environment

**Files to create:**
- `cdk/` - AWS CDK infrastructure code
- `frontend/` - React application
- `README.md` - Project overview and setup instructions
- `.gitignore` - Exclude node_modules, __pycache__, .env files, CDK artifacts

## 1.2 AWS CDK Infrastructure Setup
- Initialize CDK app with Python
- Configure `cdk.json` with proper settings
- Set up `requirements.txt` with CDK dependencies
- Create stack structure: `stacks/` directory with separate stack files

**Files to create:**
- `cdk/app.py` - CDK app entry point
- `cdk/cdk.json` - CDK configuration
- `cdk/requirements.txt` - Python dependencies (aws-cdk-lib, constructs, boto3)
- `cdk/stacks/__init__.py`
- `cdk/stacks/database_stack.py` - DynamoDB tables
- `cdk/stacks/auth_stack.py` - Cognito User Pool
- `cdk/stacks/api_stack.py` - API Gateway and Lambda functions
- `cdk/stacks/storage_stack.py` - S3 buckets and CloudFront
- `cdk/stacks/dns_stack.py` - Route 53 configuration

## 1.3 Database Stack (DynamoDB)
- Create all 5 DynamoDB tables with proper schemas:
  - Player table (playerId as partition key)
  - Activity table (activityId as partition key)
  - Tracking table (composite key: playerId#weekId#date)
  - Reflection table (composite key: playerId#weekId)
  - ContentPages table (pageId as partition key, teamId GSI)
- Configure Global Secondary Indexes (GSI) for efficient queries
- Enable point-in-time recovery
- Set on-demand billing mode

**Key implementation:**
- `cdk/stacks/database_stack.py` - Define all tables with proper key schemas and GSIs

## 1.4 Authentication Stack (Cognito)
- Create Cognito User Pool for coach/admin authentication
- Configure password policy (min 8 chars, uppercase, lowercase, number)
- Set up email verification
- Create app client for web application
- Configure JWT token expiration (1 hour access, 30 day refresh)

**Key implementation:**
- `cdk/stacks/auth_stack.py` - Cognito User Pool with proper policies

