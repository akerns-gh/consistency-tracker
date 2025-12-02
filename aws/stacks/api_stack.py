"""
API Stack - API Gateway and Lambda Functions

Placeholder for Phase 2 implementation.
Will contain API Gateway REST API and Lambda functions for all endpoints.
"""

from aws_cdk import Stack
from constructs import Construct
from stacks.database_stack import DatabaseStack
from stacks.auth_stack import AuthStack


class ApiStack(Stack):
    """Stack containing API Gateway and Lambda functions."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        database_stack: DatabaseStack,
        auth_stack: AuthStack,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Store references for Phase 2 implementation
        self.database_stack = database_stack
        self.auth_stack = auth_stack

        # TODO: Phase 2 - Implement API Gateway and Lambda functions
        # - REST API Gateway
        # - Lambda functions for player endpoints
        # - Lambda functions for admin endpoints
        # - Cognito authorizer for admin endpoints
        # - CORS configuration
        # - IAM roles and permissions

