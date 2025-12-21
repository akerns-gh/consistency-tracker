"""
SES Stack - Simple Email Service Configuration

Creates SES configuration for sending emails via verified Proton Mail domain.
Note: Domain verification must be done manually in AWS Console after deployment.
"""

from aws_cdk import (
    Stack,
    CfnOutput,
    aws_iam as iam,
    aws_ses as ses,
)
from constructs import Construct


class SesStack(Stack):
    """Stack containing SES configuration for email delivery."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        domain_name: str = None,
        from_email: str = None,
        from_name: str = "Consistency Tracker",
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Store configuration
        self.domain_name = domain_name
        self.from_email = from_email or (f"noreply@{domain_name}" if domain_name else "noreply@repwarrior.net")
        self.from_name = from_name

        # Note: SES domain verification must be done manually in AWS Console
        # CDK doesn't have native support for domain verification in SES v2
        # The domain will need to be verified via AWS Console after deployment
        # This stack provides the IAM permissions and configuration

        # Create IAM role for Lambda functions to send emails via SES
        # This role will be assumed by Lambda functions
        self.ses_role = iam.Role(
            self,
            "SesEmailRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="Role for Lambda functions to send emails via SES",
        )

        # Grant SES send permissions
        self.ses_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ses:SendEmail",
                    "ses:SendRawEmail",
                ],
                resources=["*"],  # SES doesn't support resource-level permissions
            )
        )

        # Outputs
        CfnOutput(
            self,
            "SesFromEmail",
            value=self.from_email,
            description="SES 'From' email address",
            export_name="ConsistencyTracker-SesFromEmail",
        )

        CfnOutput(
            self,
            "SesFromName",
            value=self.from_name,
            description="SES 'From' display name",
            export_name="ConsistencyTracker-SesFromName",
        )

        CfnOutput(
            self,
            "SesRegion",
            value=self.region,
            description="SES region",
            export_name="ConsistencyTracker-SesRegion",
        )

        # Note: Domain verification instructions
        CfnOutput(
            self,
            "SesDomainVerificationNote",
            value=f"Verify domain '{domain_name}' in SES Console after deployment. Add DNS records to Route 53.",
            description="SES domain verification instructions",
        )

