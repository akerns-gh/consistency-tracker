"""
DNS Stack - Route 53 Configuration

Creates Route 53 DNS records for the domain using an existing hosted zone.
The hosted zone must already exist and be specified by ID to prevent duplicate zones.
"""

from aws_cdk import (
    Stack,
    CfnOutput,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_certificatemanager as acm,
)
from constructs import Construct
from stacks.storage_stack import StorageStack


class DnsStack(Stack):
    """Stack containing Route 53 DNS configuration."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        domain_name: str,
        hosted_zone_id: str,
        storage_stack: StorageStack = None,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.domain_name = domain_name
        self.storage_stack = storage_stack

        # Use the existing hosted zone by ID to prevent duplicate zones
        # This ensures we always reference the correct, authoritative hosted zone
        self.hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
            self,
            "HostedZone",
            hosted_zone_id=hosted_zone_id,
            zone_name=domain_name,
        )

        # Request ACM certificate for the domain
        # Since this stack is now deployed to us-east-1, we can create the certificate here
        # CloudFront requires certificates to be in us-east-1, so this works perfectly
        self.certificate = acm.Certificate(
            self,
            "DomainCertificate",
            domain_name=domain_name,
            subject_alternative_names=[f"*.{domain_name}"],  # Wildcard for subdomains
            validation=acm.CertificateValidation.from_dns(self.hosted_zone),
        )

        # Outputs
        CfnOutput(
            self,
            "HostedZoneId",
            value=self.hosted_zone.hosted_zone_id,
            description="Route 53 Hosted Zone ID",
            export_name="ConsistencyTracker-HostedZoneId",
        )

        CfnOutput(
            self,
            "CertificateArn",
            value=self.certificate.certificate_arn,
            description="ACM Certificate ARN",
            export_name="ConsistencyTracker-CertificateArn",
        )

    def add_route53_records(self, storage_stack: StorageStack):
        """Add Route 53 records pointing to CloudFront distributions"""
        if not storage_stack:
            return
            
        # A record for root domain pointing to CloudFront
        root_record = route53.ARecord(
            self,
            "RootARecord",
            zone=self.hosted_zone,
            record_name=self.domain_name,
            target=route53.RecordTarget.from_alias(
                targets.CloudFrontTarget(storage_stack.frontend_distribution)
            ),
        )

        # A record for www subdomain (optional)
        www_record = route53.ARecord(
            self,
            "WwwARecord",
            zone=self.hosted_zone,
            record_name=f"www.{self.domain_name}",
            target=route53.RecordTarget.from_alias(
                targets.CloudFrontTarget(storage_stack.frontend_distribution)
            ),
        )

        # A record for content subdomain (for content images)
        content_record = route53.ARecord(
            self,
            "ContentARecord",
            zone=self.hosted_zone,
            record_name=f"content.{self.domain_name}",
            target=route53.RecordTarget.from_alias(
                targets.CloudFrontTarget(storage_stack.content_distribution)
            ),
        )
        
        CfnOutput(
            self,
            "RootDomainRecord",
            value=root_record.domain_name,
            description="Root domain A record",
        )

        CfnOutput(
            self,
            "ContentDomainRecord",
            value=content_record.domain_name,
            description="Content subdomain A record",
        )
