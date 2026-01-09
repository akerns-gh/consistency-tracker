"""
DNS Stack - Route 53 Configuration

Creates Route 53 DNS records for the domain using an existing hosted zone.
The hosted zone must already exist and be specified by ID to prevent duplicate zones.
"""

import json
from pathlib import Path
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

        # Set up ProtonMail DNS records from config file
        # This ensures email DNS records persist across deployments
        self._setup_protonmail_dns()

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

    def _load_email_config(self) -> dict:
        """Load email configuration from config.json file."""
        # Try to find config.json relative to this file
        script_dir = Path(__file__).parent.parent
        config_path = script_dir / "email_tools" / "config.json"
        
        if not config_path.exists():
            # Fallback: try to find it in the current directory
            config_path = Path("email_tools") / "config.json"
            if not config_path.exists():
                print(f"⚠️  Warning: Email config file not found at {config_path}")
                print("   ProtonMail DNS records will not be created.")
                return None
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  Warning: Could not load email config: {e}")
            print("   ProtonMail DNS records will not be created.")
            return None

    def _setup_protonmail_dns(self):
        """Set up ProtonMail DNS records (MX, TXT, DKIM, DMARC) from config file."""
        config = self._load_email_config()
        if not config or 'proton' not in config:
            return
        
        proton_config = config.get('proton', {})
        
        # 1. MX records for incoming mail
        if 'mx' in proton_config:
            mx_records = []
            for mx_value in proton_config['mx']:
                # MX records are in format "priority server"
                parts = mx_value.split(' ', 1)
                if len(parts) == 2:
                    priority = int(parts[0])
                    server = parts[1]
                    mx_records.append(route53.MxRecordValue(
                        priority=priority,
                        host_name=server
                    ))
            
            if mx_records:
                route53.MxRecord(
                    self,
                    "ProtonMailMXRecord",
                    zone=self.hosted_zone,
                    record_name=self.domain_name,
                    values=mx_records,
                )
        
        # 2. TXT record combining ProtonMail verification and SPF
        txt_values = []
        if 'verification' in proton_config:
            txt_values.append(proton_config['verification'])
        if 'spf' in proton_config:
            txt_values.append(proton_config['spf'])
        
        if txt_values:
            route53.TxtRecord(
                self,
                "ProtonMailTXTRecord",
                zone=self.hosted_zone,
                record_name=self.domain_name,
                values=txt_values,
            )
        
        # 3. DKIM CNAME records
        if 'dkim' in proton_config:
            for i, dkim in enumerate(proton_config['dkim']):
                host = dkim.get('host', '')
                value = dkim.get('value', '')
                if host and value:
                    # Ensure value ends with dot for CNAME
                    if not value.endswith('.'):
                        value = f"{value}."
                    
                    route53.CnameRecord(
                        self,
                        f"ProtonMailDKIM{i+1}",
                        zone=self.hosted_zone,
                        record_name=f"{host}.{self.domain_name}",
                        domain_name=value,
                    )
        
        # 4. DMARC TXT record
        if 'dmarc' in proton_config:
            route53.TxtRecord(
                self,
                "ProtonMailDMARCRecord",
                zone=self.hosted_zone,
                record_name=f"_dmarc.{self.domain_name}",
                values=[proton_config['dmarc']],
            )

    def add_route53_records(self, storage_stack: StorageStack, api_stack=None):
        """Add Route 53 records pointing to CloudFront distributions and API Gateway"""
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
        
        # A record for api subdomain pointing to API Gateway custom domain
        if api_stack and api_stack.custom_domain:
            # For REST API Gateway, use ApiGatewayDomain target
            api_record = route53.ARecord(
                self,
                "ApiARecord",
                zone=self.hosted_zone,
                record_name=f"api.{self.domain_name}",
                target=route53.RecordTarget.from_alias(
                    targets.ApiGatewayDomain(api_stack.custom_domain)
                ),
            )
            
            CfnOutput(
                self,
                "ApiDomainRecord",
                value=api_record.domain_name,
                description="API subdomain A record",
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
