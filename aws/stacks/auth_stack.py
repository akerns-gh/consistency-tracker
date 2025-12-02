"""
Authentication Stack - Cognito User Pool for Admin Authentication

Creates Cognito User Pool with custom password policy and admin user group.
"""

from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_cognito as cognito,
)
from constructs import Construct


class AuthStack(Stack):
    """Stack containing Cognito User Pool for admin/coach authentication."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Cognito User Pool
        self.user_pool = cognito.UserPool(
            self,
            "AdminUserPool",
            user_pool_name="ConsistencyTracker-AdminPool",
            self_sign_up_enabled=False,  # Admins are created by other admins
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=12,  # Minimum 12 characters
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=False,  # Not required per requirements
                temp_password_validity=Duration.days(7),
            ),
            # Email verification
            user_verification=cognito.UserVerificationConfig(
                email_style=cognito.VerificationEmailStyle.LINK,
            ),
            # Password history (prevents reuse of last 3 passwords)
            # Note: Cognito doesn't support exact "no repeating characters" rule
            # This would need to be enforced via a Lambda trigger if required
            sign_in_case_sensitive=False,
        )

        # Add password history policy
        # Cognito supports password history via a Lambda trigger
        # For now, we'll configure the user pool with standard settings
        # Custom password validation (no repeating chars) can be added in Phase 2

        # App Client for web application
        self.user_pool_client = self.user_pool.add_client(
            "WebAppClient",
            user_pool_client_name="ConsistencyTracker-WebClient",
            generate_secret=False,  # Public client (web app)
            auth_flows=cognito.AuthFlow(
                user_password=True,  # Username/password flow
                admin_user_password=True,  # Admin-initiated auth
            ),
            access_token_validity=Duration.hours(1),  # 1 hour access token
            refresh_token_validity=Duration.days(30),  # 30 day refresh token
            id_token_validity=Duration.hours(1),  # 1 hour ID token
            prevent_user_existence_errors=True,  # Security: don't reveal if user exists
        )

        # Admin User Group
        # This group identifies users with admin privileges
        self.admin_group = cognito.CfnUserGroup(
            self,
            "AdminGroup",
            user_pool_id=self.user_pool.user_pool_id,
            group_name="Admins",
            description="Administrators with full access to the Consistency Tracker",
            precedence=1,  # Lower number = higher precedence
        )

        # Outputs
        CfnOutput(
            self,
            "UserPoolId",
            value=self.user_pool.user_pool_id,
            description="Cognito User Pool ID",
            export_name="ConsistencyTracker-UserPoolId",
        )

        CfnOutput(
            self,
            "UserPoolClientId",
            value=self.user_pool_client.user_pool_client_id,
            description="Cognito User Pool Client ID",
            export_name="ConsistencyTracker-UserPoolClientId",
        )

        CfnOutput(
            self,
            "UserPoolArn",
            value=self.user_pool.user_pool_arn,
            description="Cognito User Pool ARN",
            export_name="ConsistencyTracker-UserPoolArn",
        )

