#!/usr/bin/env python3
"""
True Lacrosse Consistency Tracker - CDK App Entry Point
"""

import aws_cdk as cdk
from stacks.database_stack import DatabaseStack
from stacks.auth_stack import AuthStack
from stacks.ses_stack import SesStack
from stacks.api_stack import ApiStack
from stacks.storage_stack import StorageStack
from stacks.dns_stack import DnsStack

# Configuration
DOMAIN_NAME = "repwarrior.net"
AWS_REGION = "us-east-1"
HOSTED_ZONE_ID = "Z0224155HV050F02RZE0"  # Route 53 hosted zone ID for repwarrior.net

# Email configuration
SES_FROM_EMAIL = f"noreply@{DOMAIN_NAME}"  # Default from email
SES_CLUB_ADMIN_FROM_EMAIL = f"info@{DOMAIN_NAME}"  # Club admin invitation from email

app = cdk.App()

# Database Stack - Foundation for all data storage
database_stack = DatabaseStack(
    app,
    "ConsistencyTracker-Database",
    env=cdk.Environment(
        account=app.node.try_get_context("account") or None,
        region=AWS_REGION,
    ),
    description="DynamoDB tables for Consistency Tracker",
)

# Auth Stack - Cognito User Pool for admin authentication
auth_stack = AuthStack(
    app,
    "ConsistencyTracker-Auth",
    env=cdk.Environment(
        account=app.node.try_get_context("account") or None,
        region=AWS_REGION,
    ),
    description="Cognito User Pool for admin authentication",
)

# SES Stack - Simple Email Service configuration
ses_stack = SesStack(
    app,
    "ConsistencyTracker-SES",
    domain_name=DOMAIN_NAME,
    from_email=SES_FROM_EMAIL,
    club_admin_from_email=SES_CLUB_ADMIN_FROM_EMAIL,
    from_name="Consistency Tracker",
    env=cdk.Environment(
        account=app.node.try_get_context("account") or None,
        region=AWS_REGION,
    ),
    description="SES configuration for email delivery",
)

# API Stack - API Gateway and Lambda functions (Phase 2)
# Note: Custom domain will be configured after DNS stack creates certificate
# For now, deploy without custom domain to get API working
api_stack = ApiStack(
    app,
    "ConsistencyTracker-API",
    database_stack=database_stack,
    auth_stack=auth_stack,
    ses_stack=ses_stack,
    domain_name=DOMAIN_NAME,  # Pass domain name for CORS configuration
    # certificate_arn will be added after DNS stack creates certificate
    # certificate_arn="arn:aws:acm:us-east-1:707406431671:certificate/98d1bf1b-dfd3-45bb-82aa-176aedd2babe",  # Wildcard cert covers api.repwarrior.net
    env=cdk.Environment(
        account=app.node.try_get_context("account") or None,
        region=AWS_REGION,
    ),
    description="API Gateway and Lambda functions",
)

# DNS Stack - Route 53 configuration (Phase 2)
# Create DNS stack first to get the certificate (certificate doesn't need Storage)
dns_stack = DnsStack(
    app,
    "ConsistencyTracker-DNS",
    domain_name=DOMAIN_NAME,
    hosted_zone_id=HOSTED_ZONE_ID,
    env=cdk.Environment(
        account=app.node.try_get_context("account") or None,
        region=AWS_REGION,
    ),
    description="Route 53 DNS configuration",
)

# Storage Stack - S3 buckets and CloudFront (Phase 2)
# IMPORTANT: There is a known CDK bug (TypeError) when using certificates with CloudFront Distribution
# during synthesis. The certificate configuration is ready in StorageStack, but must be added
# after initial deployment. See DEPLOYMENT_README.md for instructions.
storage_stack = StorageStack(
    app,
    "ConsistencyTracker-Storage",
    domain_name=DOMAIN_NAME,
    # certificate_arn will be added manually via AWS Console after deployment
    # See DEPLOYMENT_README.md for manual certificate configuration instructions
    # certificate_arn="arn:aws:acm:us-east-1:707406431671:certificate/98d1bf1b-dfd3-45bb-82aa-176aedd2babe",
    env=cdk.Environment(
        account=app.node.try_get_context("account") or None,
        region=AWS_REGION,
    ),
    description="S3 buckets and CloudFront distribution",
)

# Now add Route 53 records to DNS stack (after Storage and API are created)
dns_stack.add_route53_records(storage_stack, api_stack)

app.synth()

