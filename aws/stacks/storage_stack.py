"""
Storage Stack - S3 Buckets and CloudFront Distribution

Creates S3 buckets for frontend hosting and content images, with CloudFront distributions.
"""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    Token,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_certificatemanager as acm,
    aws_iam as iam,
    aws_wafv2 as wafv2,
)
from constructs import Construct

# Import for Token checking
try:
    from aws_cdk import Token as cdk_token
except ImportError:
    cdk_token = None


class StorageStack(Stack):
    """Stack containing S3 buckets and CloudFront distribution."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        domain_name: str = None,
        certificate = None,  # ACM Certificate object (preferred) or ARN string
        certificate_arn = None,  # Deprecated: use certificate parameter instead
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.domain_name = domain_name
        self._certificate = certificate
        # Support legacy certificate_arn parameter
        if certificate_arn and not certificate:
            self._certificate_arn = certificate_arn
        else:
            self._certificate_arn = None

        # S3 bucket for React frontend hosting
        # Note: Do NOT use website configuration - use REST endpoint with OAI instead
        self.frontend_bucket = s3.Bucket(
            self,
            "FrontendBucket",
            bucket_name="consistency-tracker-frontend-us-east-1",
            # Removed website_index_document and website_error_document
            # CloudFront will handle routing with error responses configured below
            public_read_access=False,  # Private bucket, accessed via CloudFront
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,  # Retain on stack deletion
            auto_delete_objects=False,  # Don't auto-delete on stack deletion
            versioned=True,  # Enable versioning for rollback capability
        )

        # S3 bucket for content images
        self.content_images_bucket = s3.Bucket(
            self,
            "ContentImagesBucket",
            bucket_name="consistency-tracker-content-images-us-east-1",
            public_read_access=False,  # Private bucket, accessed via CloudFront
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
            auto_delete_objects=False,
            cors=[
                s3.CorsRule(
                    # Restrict CORS to specific domains for security
                    allowed_origins=[
                        f"https://{self.domain_name}",
                        f"https://www.{self.domain_name}",
                    ] if self.domain_name else ["*"],
                    allowed_methods=[s3.HttpMethods.GET, s3.HttpMethods.PUT],
                    allowed_headers=["*"],
                    max_age=300,
                )
            ],
        )

        # Origin Access Identity for CloudFront to access S3
        frontend_oai = cloudfront.OriginAccessIdentity(
            self,
            "FrontendOAI",
            comment="OAI for frontend bucket access",
        )

        content_oai = cloudfront.OriginAccessIdentity(
            self,
            "ContentOAI",
            comment="OAI for content images bucket access",
        )

        # Grant CloudFront read access to buckets
        self.frontend_bucket.grant_read(frontend_oai)
        self.content_images_bucket.grant_read(content_oai)
        self.content_images_bucket.grant_put(iam.ServicePrincipal("lambda.amazonaws.com"))

        # Create WAF WebACL for CloudFront protection
        # Note: WAF for CloudFront must be created in us-east-1 region
        web_acl = wafv2.CfnWebACL(
            self,
            "CloudFrontWebACL",
            scope="CLOUDFRONT",  # Required for CloudFront
            default_action=wafv2.CfnWebACL.DefaultActionProperty(
                block=wafv2.CfnWebACL.BlockActionProperty(
                    custom_response=wafv2.CfnWebACL.CustomResponseProperty(
                        response_code=403,
                        custom_response_body_key="access-denied"
                    )
                )
            ),
            custom_response_bodies={
                "access-denied": wafv2.CfnWebACL.CustomResponseBodyProperty(
                    content_type="TEXT_HTML",
                    content='''<!DOCTYPE html>
<html>
<head>
    <title>Access Denied</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            text-align: center;
            padding: 50px 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #d32f2f;
            margin-bottom: 20px;
            font-size: 28px;
        }
        p {
            color: #666;
            line-height: 1.6;
            margin-bottom: 15px;
        }
        .icon {
            font-size: 64px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">🚫</div>
        <h1>Access Denied</h1>
        <p>Access to this site is restricted to IP addresses originating from the United States.</p>
        <p>If you believe this is an error, please contact the administrator.</p>
    </div>
</body>
</html>'''
                ),
                "rate-limit-exceeded": wafv2.CfnWebACL.CustomResponseBodyProperty(
                    content_type="TEXT_HTML",
                    content='''<!DOCTYPE html>
<html>
<head>
    <title>Rate Limit Exceeded</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            text-align: center;
            padding: 50px 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #f57c00;
            margin-bottom: 20px;
            font-size: 28px;
        }
        p {
            color: #666;
            line-height: 1.6;
            margin-bottom: 15px;
        }
        .icon {
            font-size: 64px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">⏱️</div>
        <h1>Rate Limit Exceeded</h1>
        <p>You have made too many requests. Please try again later.</p>
    </div>
</body>
</html>'''
                )
            },
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name="ConsistencyTrackerWebACL",
                sampled_requests_enabled=True,
            ),
            # WAF rules in priority order (lower number = higher priority)
            rules=[
                # Geographic restriction: Only allow US IP addresses
                wafv2.CfnWebACL.RuleProperty(
                    name="USOnlyGeoMatch",
                    priority=0,
                    statement=wafv2.CfnWebACL.StatementProperty(
                        geo_match_statement=wafv2.CfnWebACL.GeoMatchStatementProperty(
                            country_codes=["US"]  # Only allow US IP addresses
                        )
                    ),
                    action=wafv2.CfnWebACL.RuleActionProperty(
                        allow={}  # Allow requests from US
                    ),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name="USOnlyGeoMatch",
                        sampled_requests_enabled=True,
                    ),
                ),
                # Rate limiting rule to prevent DDoS
                wafv2.CfnWebACL.RuleProperty(
                    name="RateLimitRule",
                    priority=1,
                    statement=wafv2.CfnWebACL.StatementProperty(
                        rate_based_statement=wafv2.CfnWebACL.RateBasedStatementProperty(
                            limit=2000,  # Max 2000 requests per 5 minutes per IP
                            aggregate_key_type="IP",
                        )
                    ),
                    action=wafv2.CfnWebACL.RuleActionProperty(
                        block=wafv2.CfnWebACL.BlockActionProperty(
                            custom_response=wafv2.CfnWebACL.CustomResponseProperty(
                                response_code=429,
                                custom_response_body_key="rate-limit-exceeded"
                            )
                        )
                    ),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name="RateLimitRule",
                        sampled_requests_enabled=True,
                    ),
                ),
                # AWS Managed Rule: Common Rule Set (protects against common exploits)
                wafv2.CfnWebACL.RuleProperty(
                    name="AWSManagedRulesCommonRuleSet",
                    priority=2,
                    override_action=wafv2.CfnWebACL.OverrideActionProperty(
                        none={}
                    ),
                    statement=wafv2.CfnWebACL.StatementProperty(
                        managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                            name="AWSManagedRulesCommonRuleSet",
                            vendor_name="AWS",
                        )
                    ),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name="CommonRuleSet",
                        sampled_requests_enabled=True,
                    ),
                ),
            ],
        )

        # Create Response Headers Policy with HSTS and security headers
        # This forces browsers to always use HTTPS and adds security headers
        response_headers_policy = cloudfront.ResponseHeadersPolicy(
            self,
            "SecurityHeadersPolicy",
            security_headers_behavior=cloudfront.ResponseSecurityHeadersBehavior(
                strict_transport_security=cloudfront.ResponseHeadersStrictTransportSecurity(
                    access_control_max_age=Duration.seconds(31536000),  # 1 year
                    include_subdomains=True,
                    preload=True,
                    override=True,
                ),
                content_type_options=cloudfront.ResponseHeadersContentTypeOptions(
                    override=True,
                ),
                frame_options=cloudfront.ResponseHeadersFrameOptions(
                    frame_option=cloudfront.HeadersFrameOption.DENY,
                    override=True,
                ),
                referrer_policy=cloudfront.ResponseHeadersReferrerPolicy(
                    referrer_policy=cloudfront.HeadersReferrerPolicy.STRICT_ORIGIN_WHEN_CROSS_ORIGIN,
                    override=True,
                ),
                xss_protection=cloudfront.ResponseHeadersXSSProtection(
                    protection=True,
                    mode_block=True,
                    override=True,
                ),
            ),
        )

        # Configure CloudFront viewer certificate
        # Prefer certificate object over ARN string to avoid CDK synthesis issues
        viewer_certificate = None
        domain_names = None
        if self.domain_name:
            cert_to_use = None
            if self._certificate:
                # Use certificate object directly (preferred)
                cert_to_use = self._certificate
            elif self._certificate_arn:
                # Fallback to ARN string (legacy support)
                cert_to_use = acm.Certificate.from_certificate_arn(
                    self, "ImportedCertificate", self._certificate_arn
                )
            
            if cert_to_use:
                viewer_certificate = cloudfront.ViewerCertificate.from_acm_certificate(
                    cert_to_use,
                    aliases=[self.domain_name, f"www.{self.domain_name}"],
                )
                domain_names = [self.domain_name, f"www.{self.domain_name}"]

        # CloudFront distribution for frontend
        distribution_props = {
            "default_behavior": cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    self.frontend_bucket,
                    origin_access_identity=frontend_oai,
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD,
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD,
                compress=True,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                response_headers_policy=response_headers_policy,
            ),
            "default_root_object": "index.html",
            "error_responses": [
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(5),
                ),
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(5),
                ),
            ],
            "price_class": cloudfront.PriceClass.PRICE_CLASS_100,  # US, Canada, Europe
            "comment": "CloudFront distribution for Consistency Tracker frontend",
        }
        
        # Only add certificate and domain_names if they're configured
        if domain_names and viewer_certificate:
            distribution_props["domain_names"] = domain_names
            distribution_props["certificate"] = viewer_certificate
        
        # Add WAF WebACL to distribution
        distribution_props["web_acl_id"] = web_acl.attr_arn
            
        self.frontend_distribution = cloudfront.Distribution(
            self,
            "FrontendDistribution",
            **distribution_props
        )

        # Configure CloudFront viewer certificate for content distribution
        content_viewer_certificate = None
        content_domain_names = None
        if self.domain_name:
            cert_to_use = None
            if self._certificate:
                # Use certificate object directly (preferred)
                cert_to_use = self._certificate
            elif self._certificate_arn:
                # Fallback to ARN string (legacy support)
                cert_to_use = acm.Certificate.from_certificate_arn(
                    self, "ImportedContentCertificate", self._certificate_arn
                )
            
            if cert_to_use:
                content_viewer_certificate = cloudfront.ViewerCertificate.from_acm_certificate(
                    cert_to_use,
                    aliases=[f"content.{self.domain_name}"],
                )
                content_domain_names = [f"content.{self.domain_name}"]

        # CloudFront distribution for content images
        content_distribution_props = {
            "default_behavior": cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    self.content_images_bucket,
                    origin_access_identity=content_oai,
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD,
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD,
                compress=True,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                response_headers_policy=response_headers_policy,
            ),
            "price_class": cloudfront.PriceClass.PRICE_CLASS_100,
            "comment": "CloudFront distribution for Consistency Tracker content images",
        }
        
        # Only add certificate and domain_names if they're configured
        if content_domain_names and content_viewer_certificate:
            content_distribution_props["domain_names"] = content_domain_names
            content_distribution_props["certificate"] = content_viewer_certificate
        
        # Add WAF WebACL to content distribution
        content_distribution_props["web_acl_id"] = web_acl.attr_arn
            
        self.content_distribution = cloudfront.Distribution(
            self,
            "ContentDistribution",
            **content_distribution_props
        )

        # Outputs
        CfnOutput(
            self,
            "FrontendBucketName",
            value=self.frontend_bucket.bucket_name,
            description="S3 bucket name for frontend",
            export_name="ConsistencyTracker-FrontendBucket",
        )

        CfnOutput(
            self,
            "ContentImagesBucketName",
            value=self.content_images_bucket.bucket_name,
            description="S3 bucket name for content images",
            export_name="ConsistencyTracker-ContentImagesBucket",
        )

        CfnOutput(
            self,
            "FrontendDistributionId",
            value=self.frontend_distribution.distribution_id,
            description="CloudFront distribution ID for frontend",
            export_name="ConsistencyTracker-FrontendDistributionId",
        )

        CfnOutput(
            self,
            "FrontendDistributionDomainName",
            value=self.frontend_distribution.distribution_domain_name,
            description="CloudFront distribution domain name for frontend",
            export_name="ConsistencyTracker-FrontendDistributionDomain",
        )

        CfnOutput(
            self,
            "ContentDistributionDomainName",
            value=self.content_distribution.distribution_domain_name,
            description="CloudFront distribution domain name for content images",
            export_name="ConsistencyTracker-ContentDistributionDomain",
        )
