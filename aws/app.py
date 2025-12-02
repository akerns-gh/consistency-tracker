#!/usr/bin/env python3
"""
True Lacrosse Consistency Tracker - CDK App Entry Point
"""

import aws_cdk as cdk
from stacks.database_stack import DatabaseStack
from stacks.auth_stack import AuthStack
from stacks.api_stack import ApiStack
from stacks.storage_stack import StorageStack
from stacks.dns_stack import DnsStack

# Configuration
DOMAIN_NAME = "repwarrior.net"
AWS_REGION = "us-east-2"

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

# API Stack - API Gateway and Lambda functions (Phase 2)
api_stack = ApiStack(
    app,
    "ConsistencyTracker-API",
    database_stack=database_stack,
    auth_stack=auth_stack,
    env=cdk.Environment(
        account=app.node.try_get_context("account") or None,
        region=AWS_REGION,
    ),
    description="API Gateway and Lambda functions",
)

# Storage Stack - S3 buckets and CloudFront (Phase 2)
storage_stack = StorageStack(
    app,
    "ConsistencyTracker-Storage",
    env=cdk.Environment(
        account=app.node.try_get_context("account") or None,
        region=AWS_REGION,
    ),
    description="S3 buckets and CloudFront distribution",
)

# DNS Stack - Route 53 configuration (Phase 2)
dns_stack = DnsStack(
    app,
    "ConsistencyTracker-DNS",
    domain_name=DOMAIN_NAME,
    storage_stack=storage_stack,
    env=cdk.Environment(
        account=app.node.try_get_context("account") or None,
        region=AWS_REGION,
    ),
    description="Route 53 DNS configuration",
)

app.synth()

