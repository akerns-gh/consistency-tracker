#!/bin/bash

# Script to build and deploy the frontend application to S3 and CloudFront
# This script will:
# 1. Build the React application
# 2. Upload files to S3
# 3. Invalidate CloudFront cache

set -euo pipefail

# Configuration
S3_BUCKET="consistency-tracker-frontend-us-east-1"
CLOUDFRONT_DISTRIBUTION_ID="E2YTNOXL25MKBG"
AWS_REGION="us-east-1"
AUTH_STACK_NAME="ConsistencyTracker-Auth"
API_STACK_NAME="ConsistencyTracker-API"
API_CUSTOM_DOMAIN="https://api.repwarrior.net"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -d "app" ]; then
    log_error "This script must be run from the project root directory (where 'app' folder exists)"
    exit 1
fi

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    log_error "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    log_error "npm is not installed. Please install Node.js and npm first."
    exit 1
fi

# Get Cognito configuration from CloudFormation stack
log_info "Fetching Cognito configuration from CloudFormation stack..."
COGNITO_USER_POOL_ID=$(aws cloudformation describe-stacks \
    --stack-name "$AUTH_STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
    --output text)

COGNITO_USER_POOL_CLIENT_ID=$(aws cloudformation describe-stacks \
    --stack-name "$AUTH_STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' \
    --output text)

if [ -z "$COGNITO_USER_POOL_ID" ] || [ "$COGNITO_USER_POOL_ID" == "None" ]; then
    log_error "Failed to get Cognito User Pool ID from stack: $AUTH_STACK_NAME"
    exit 1
fi

if [ -z "$COGNITO_USER_POOL_CLIENT_ID" ] || [ "$COGNITO_USER_POOL_CLIENT_ID" == "None" ]; then
    log_error "Failed to get Cognito User Pool Client ID from stack: $AUTH_STACK_NAME"
    exit 1
fi

log_info "✅ Cognito User Pool ID: $COGNITO_USER_POOL_ID"
log_info "✅ Cognito Client ID: $COGNITO_USER_POOL_CLIENT_ID"

# Use custom domain URL (configured manually)
log_info "Using API Gateway custom domain URL..."
API_ENDPOINT="$API_CUSTOM_DOMAIN"
log_info "✅ API Gateway Endpoint: $API_ENDPOINT"

# Export environment variables for Vite build
export VITE_COGNITO_USER_POOL_ID="$COGNITO_USER_POOL_ID"
export VITE_COGNITO_USER_POOL_CLIENT_ID="$COGNITO_USER_POOL_CLIENT_ID"
export VITE_API_URL="$API_ENDPOINT"

# Build the application
log_info "Building React application..."
cd app

if [ ! -f "package.json" ]; then
    log_error "package.json not found in app directory"
    exit 1
fi

npm run build

if [ ! -d "dist" ]; then
    log_error "Build failed - dist directory not found"
    exit 1
fi

log_info "Build completed successfully"

# Upload to S3
log_info "Uploading files to S3 bucket: $S3_BUCKET"
aws s3 sync dist/ "s3://${S3_BUCKET}/" --delete

if [ $? -ne 0 ]; then
    log_error "Failed to upload files to S3"
    exit 1
fi

log_info "Files uploaded successfully"

# List uploaded files
log_info "Uploaded files:"
aws s3 ls "s3://${S3_BUCKET}/" --recursive | head -10

# Invalidate CloudFront cache
log_info "Creating CloudFront cache invalidation..."
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" \
    --paths "/*" \
    --output json | jq -r '.Invalidation.Id')

if [ -z "$INVALIDATION_ID" ] || [ "$INVALIDATION_ID" == "null" ]; then
    log_error "Failed to create CloudFront invalidation"
    exit 1
fi

log_info "CloudFront invalidation created: $INVALIDATION_ID"
log_warn "Cache invalidation takes 1-2 minutes to complete"
log_info "You can check status with:"
log_info "  aws cloudfront get-invalidation --distribution-id $CLOUDFRONT_DISTRIBUTION_ID --id $INVALIDATION_ID"

# Verify CloudFront origin configuration
log_info "Verifying CloudFront origin configuration..."
ORIGIN_DOMAIN=$(aws cloudfront get-distribution-config \
    --id "$CLOUDFRONT_DISTRIBUTION_ID" \
    --output json | jq -r '.DistributionConfig.Origins.Items[0].DomainName')

if [[ "$ORIGIN_DOMAIN" == *"s3-website"* ]]; then
    log_warn "⚠️  CloudFront is using S3 website endpoint (incorrect)"
    log_warn "   Domain: $ORIGIN_DOMAIN"
    log_warn "   This should be: ${S3_BUCKET}.s3.amazonaws.com"
    log_warn "   The distribution may need to be updated via CDK:"
    log_warn "   cdk deploy ConsistencyTracker-Storage"
else
    log_info "✅ CloudFront origin configuration is correct"
    log_info "   Domain: $ORIGIN_DOMAIN"
fi

log_info ""
log_info "Deployment complete!"
log_info "The site should be accessible at https://repwarrior.net after cache invalidation completes."

