"""
API Stack - API Gateway and Lambda Functions

Creates REST API Gateway with all Lambda functions for player and admin endpoints.
"""

import os
from pathlib import Path
from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_iam as iam,
    aws_logs as logs,
    aws_certificatemanager as acm,
)
from aws_cdk.aws_apigateway import CfnGatewayResponse
from constructs import Construct
from stacks.database_stack import DatabaseStack
from stacks.auth_stack import AuthStack
from stacks.ses_stack import SesStack


class ApiStack(Stack):
    """Stack containing API Gateway and Lambda functions."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        database_stack: DatabaseStack,
        auth_stack: AuthStack,
        ses_stack: SesStack = None,
        domain_name: str = None,
        certificate_arn: str = None,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Store domain name for CORS configuration
        self.domain_name = domain_name

        # Store references
        self.database_stack = database_stack
        self.auth_stack = auth_stack
        self.ses_stack = ses_stack
        self.certificate_arn = certificate_arn

        # Get Lambda code directory
        lambda_dir = Path(__file__).parent.parent / "lambda"

        # Create Lambda layer for shared dependencies
        layer = self._create_lambda_layer(lambda_dir)


        # Create Lambda function for player Flask app
        player_function = self._create_player_function(
            lambda_dir, layer, ses_stack
        )

        # Create Lambda function for admin Flask app
        admin_function = self._create_admin_function(
            lambda_dir, layer, ses_stack
        )

        # Create API Gateway REST API
        api = self._create_api_gateway(auth_stack)

        # Add Gateway Responses with CORS headers for all error responses
        self._add_gateway_responses(api)

        # Create Cognito authorizer (shared between admin and player endpoints)
        authorizer = self._create_cognito_authorizer(api, auth_stack)

        # Configure player endpoints (with optional Cognito auth) - proxy all to player Flask app
        self._configure_player_endpoints(api, player_function, authorizer)

        # Configure admin endpoints (with Cognito auth) - proxy all to admin Flask app
        self._configure_admin_endpoints(api, admin_function, authorizer)

        # Create custom domain for api.repwarrior.net if certificate is provided
        self.custom_domain = None
        if certificate_arn and domain_name:
            self.custom_domain = self._create_custom_domain(api, domain_name, certificate_arn)
        
        # Output API endpoint
        CfnOutput(
            self,
            "ApiEndpoint",
            value=api.url,
            description="API Gateway endpoint URL",
            export_name="ConsistencyTracker-ApiEndpoint",
        )
        
        # Output custom domain if created
        if self.custom_domain:
            CfnOutput(
                self,
                "ApiCustomDomainUrl",
                value=f"https://api.{domain_name}",
                description="API Gateway custom domain URL",
                export_name="ConsistencyTracker-ApiCustomDomain",
            )

    def _create_lambda_layer(self, lambda_dir: Path) -> lambda_.LayerVersion:
        """Create Lambda layer with Python dependencies."""
        layer_dir = lambda_dir / "layer" / "python"
        
        return lambda_.LayerVersion(
            self,
            "SharedLayer",
            code=lambda_.Code.from_asset(str(layer_dir)),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
            description="Shared dependencies (boto3, bleach, python-jose, flask, serverless-wsgi)",
        )

    def _create_player_function(
        self,
        lambda_dir: Path,
        layer: lambda_.LayerVersion,
        ses_stack: SesStack = None,
    ) -> lambda_.Function:
        """Create Lambda function for player Flask app."""
        # Environment variables
        env_vars = {
            "PLAYER_TABLE": self.database_stack.player_table.table_name,
            "ACTIVITY_TABLE": self.database_stack.activity_table.table_name,
            "TRACKING_TABLE": self.database_stack.tracking_table.table_name,
            "REFLECTION_TABLE": self.database_stack.reflection_table.table_name,
            "CONTENT_PAGES_TABLE": self.database_stack.content_pages_table.table_name,
            "TEAM_TABLE": self.database_stack.team_table.table_name,
            "CLUB_TABLE": self.database_stack.club_table.table_name,
            "COGNITO_USER_POOL_ID": self.auth_stack.user_pool.user_pool_id,
            "COGNITO_REGION": self.region,
            "STRIP_STAGE_PATH": "yes",  # Strip /prod from paths when using direct API Gateway URL
        }
        
        # Add SES environment variables if SES stack is provided
        if ses_stack:
            env_vars["SES_REGION"] = ses_stack.region
            env_vars["SES_FROM_EMAIL"] = ses_stack.from_email
            env_vars["SES_CLUB_ADMIN_FROM_EMAIL"] = ses_stack.club_admin_from_email
            env_vars["SES_FROM_NAME"] = ses_stack.from_name
        
        # Add frontend URL for email links
        env_vars["FRONTEND_URL"] = f"https://{self.domain_name}" if self.domain_name else "https://repwarrior.net"

        # IAM role for player function
        player_role = iam.Role(
            self,
            "PlayerLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
        )

        # Grant DynamoDB read/write permissions
        self.database_stack.player_table.grant_read_data(player_role)
        self.database_stack.activity_table.grant_read_data(player_role)
        self.database_stack.tracking_table.grant_read_write_data(player_role)
        self.database_stack.reflection_table.grant_read_write_data(player_role)
        self.database_stack.content_pages_table.grant_read_data(player_role)
        self.database_stack.team_table.grant_read_data(player_role)
        self.database_stack.club_table.grant_read_data(player_role)
        
        # Grant SES permissions if SES stack is provided
        if ses_stack:
            player_role.add_to_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "ses:SendEmail",
                        "ses:SendRawEmail",
                    ],
                    resources=["*"],
                )
            )

        # Create single Lambda function for player Flask app
        player_function = lambda_.Function(
            self,
            "PlayerAppFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="player_app.lambda_handler",
            code=lambda_.Code.from_asset(
                str(lambda_dir),
                exclude=["**/admin/**", "**/layer/**", "**/__pycache__/**", "**/legacy/**"],
            ),
            layers=[layer],
            environment=env_vars,
            role=player_role,
            timeout=Duration.seconds(30),
            memory_size=512,  # Increased for Flask app
            description="Flask application for player endpoints - v3",
            log_retention=logs.RetentionDays.ONE_WEEK,
        )

        return player_function

    def _create_admin_function(
        self,
        lambda_dir: Path,
        layer: lambda_.LayerVersion,
        ses_stack: SesStack = None,
    ) -> lambda_.Function:
        """Create Lambda function for admin Flask app."""
        # Environment variables
        env_vars = {
            "PLAYER_TABLE": self.database_stack.player_table.table_name,
            "ACTIVITY_TABLE": self.database_stack.activity_table.table_name,
            "TRACKING_TABLE": self.database_stack.tracking_table.table_name,
            "REFLECTION_TABLE": self.database_stack.reflection_table.table_name,
            "CONTENT_PAGES_TABLE": self.database_stack.content_pages_table.table_name,
            "TEAM_TABLE": self.database_stack.team_table.table_name,
            "CLUB_TABLE": self.database_stack.club_table.table_name,
            "COGNITO_USER_POOL_ID": self.auth_stack.user_pool.user_pool_id,
            "COGNITO_REGION": self.region,
            "CONTENT_IMAGES_BUCKET": "consistency-tracker-content-images",  # Will be set from storage stack
            "STRIP_STAGE_PATH": "yes",  # Strip /prod from paths when using direct API Gateway URL
        }
        
        # Add SES environment variables if SES stack is provided
        if ses_stack:
            env_vars["SES_REGION"] = ses_stack.region
            env_vars["SES_FROM_EMAIL"] = ses_stack.from_email
            env_vars["SES_CLUB_ADMIN_FROM_EMAIL"] = ses_stack.club_admin_from_email
            env_vars["SES_FROM_NAME"] = ses_stack.from_name
        
        # Add frontend URL for email links
        env_vars["FRONTEND_URL"] = f"https://{self.domain_name}" if self.domain_name else "https://repwarrior.net"

        # IAM role for admin function
        admin_role = iam.Role(
            self,
            "AdminLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
        )

        # Grant full DynamoDB permissions
        self.database_stack.player_table.grant_read_write_data(admin_role)
        self.database_stack.activity_table.grant_read_write_data(admin_role)
        self.database_stack.tracking_table.grant_read_write_data(admin_role)
        self.database_stack.reflection_table.grant_read_write_data(admin_role)
        self.database_stack.content_pages_table.grant_read_write_data(admin_role)
        self.database_stack.team_table.grant_read_write_data(admin_role)
        self.database_stack.club_table.grant_read_write_data(admin_role)

        # Grant S3 permissions for image upload
        admin_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["s3:PutObject", "s3:GetObject"],
                resources=["arn:aws:s3:::consistency-tracker-content-images/*"],
            )
        )

        # Grant Cognito permissions for group creation and management
        admin_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cognito-idp:CreateGroup",
                    "cognito-idp:DescribeUserPool",
                    "cognito-idp:GetGroup",
                    "cognito-idp:AdminAddUserToGroup",
                    "cognito-idp:AdminCreateUser",
                ],
                resources=[self.auth_stack.user_pool.user_pool_arn],
            )
        )
        
        # Grant SES permissions if SES stack is provided
        if ses_stack:
            admin_role.add_to_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "ses:SendEmail",
                        "ses:SendRawEmail",
                        "ses:VerifyEmailIdentity",
                    ],
                    resources=["*"],
                )
            )

        # Create single Lambda function for admin Flask app
        admin_function = lambda_.Function(
            self,
            "AdminAppFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="admin_app.lambda_handler",
            code=lambda_.Code.from_asset(
                str(lambda_dir),
                exclude=["**/layer/**", "**/__pycache__/**"],
            ),
            layers=[layer],
            environment=env_vars,
            role=admin_role,
            timeout=Duration.seconds(30),
            memory_size=512,  # Increased for Flask app
            description="Flask application for admin endpoints",
            log_retention=logs.RetentionDays.ONE_WEEK,
        )

        return admin_function

    def _create_api_gateway(self, auth_stack: AuthStack) -> apigateway.RestApi:
        """Create REST API Gateway with security configurations."""
        # Use domain name from constructor or context
        domain_name = self.domain_name or self.node.try_get_context("domain_name") or "repwarrior.net"
        
        api = apigateway.RestApi(
            self,
            "ConsistencyTrackerApi",
            rest_api_name="Consistency Tracker API",
            description="API for Consistency Tracker application",
            default_cors_preflight_options=apigateway.CorsOptions(
                # Restrict CORS to specific domains for security
                allow_origins=[
                    f"https://{domain_name}",
                    f"https://www.{domain_name}",
                ],
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=[
                    "Content-Type",
                    "Authorization",
                    "X-Amz-Date",
                    "X-Api-Key",
                    "X-Amz-Security-Token",
                ],
                max_age=Duration.seconds(86400),
            ),
            deploy_options=apigateway.StageOptions(
                stage_name="prod",
                logging_level=apigateway.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
                # Add throttling to prevent abuse
                throttling_rate_limit=1000,  # Requests per second
                throttling_burst_limit=2000,  # Burst capacity
            ),
        )

        return api

    def _add_gateway_responses(self, api: apigateway.RestApi) -> None:
        """Add Gateway Responses with CORS headers for all error responses."""
        domain_name = self.domain_name or self.node.try_get_context("domain_name") or "repwarrior.net"
        
        # Get the API Gateway REST API ID
        rest_api_id = api.rest_api_id
        
        # CORS headers to add to all error responses
        # Note: Gateway Responses can't dynamically match origins, so we use the primary domain
        # Flask app will handle dynamic origin matching for Lambda-level errors
        cors_headers = {
            "gatewayresponse.header.Access-Control-Allow-Origin": f"'https://{domain_name}'",
            "gatewayresponse.header.Access-Control-Allow-Headers": "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'",
            "gatewayresponse.header.Access-Control-Allow-Methods": "'GET,POST,PUT,DELETE,OPTIONS,PATCH'",
            "gatewayresponse.header.Access-Control-Allow-Credentials": "'true'",
        }
        
        # Add CORS headers to common error responses using CfnGatewayResponse
        # Note: response_type determines the status code, no need for status_code parameter
        error_types = [
            "DEFAULT_4XX",
            "DEFAULT_5XX",
            "UNAUTHORIZED",
            "ACCESS_DENIED",
            "EXPIRED_TOKEN",
            "INVALID_SIGNATURE",
            "MISSING_AUTHENTICATION_TOKEN",
        ]
        
        for error_type in error_types:
            CfnGatewayResponse(
                self,
                f"{error_type}Response",
                rest_api_id=rest_api_id,
                response_type=error_type,
                response_parameters=cors_headers,
            )

    def _create_cognito_authorizer(
        self, api: apigateway.RestApi, auth_stack: AuthStack
    ) -> apigateway.CognitoUserPoolsAuthorizer:
        """Create Cognito authorizer for admin endpoints."""
        authorizer = apigateway.CognitoUserPoolsAuthorizer(
            self,
            "CognitoAuthorizer",
            cognito_user_pools=[auth_stack.user_pool],
            identity_source=apigateway.IdentitySource.header("Authorization"),
        )

        return authorizer

    def _configure_player_endpoints(
        self, api: apigateway.RestApi, player_function: lambda_.Function, authorizer: apigateway.CognitoUserPoolsAuthorizer
    ) -> None:
        """Configure player endpoints (with Cognito authentication) - proxy all to Flask app."""
        # Create proxy integration for player Flask app
        player_integration = apigateway.LambdaIntegration(
            player_function,
            proxy=True,  # Proxy all requests to Flask app
        )
        
        # Configure player routes with Cognito authorizer
        # All /player/* routes require authentication at API Gateway level
        # Flask will handle JWT validation and unique link validation
        player_resource = api.root.add_resource("player")
        # Add direct route for /player (exact match) - WITH authorizer
        # Add both ANY and GET explicitly to ensure browser requests work
        # ANY includes OPTIONS for CORS preflight
        player_resource.add_method("ANY", player_integration, authorizer=authorizer)
        player_resource.add_method("GET", player_integration, authorizer=authorizer)
        # Add catch-all that matches everything under /player/*
        player_proxy = player_resource.add_resource("{proxy+}")
        player_proxy.add_method("ANY", player_integration, authorizer=authorizer)
        player_proxy.add_method("GET", player_integration, authorizer=authorizer)
        
        # For leaderboard and content, we need to handle them separately
        # since they might have existing specific routes
        # We'll add them as catch-all but Flask will route correctly
        leaderboard_resource = api.root.add_resource("leaderboard")
        leaderboard_proxy = leaderboard_resource.add_resource("{proxy+}")
        leaderboard_proxy.add_method("ANY", player_integration, authorizer=authorizer)
        
        content_resource = api.root.add_resource("content")
        content_proxy = content_resource.add_resource("{proxy+}")
        content_proxy.add_method("ANY", player_integration, authorizer=authorizer)

    def _configure_admin_endpoints(
        self,
        api: apigateway.RestApi,
        admin_function: lambda_.Function,
        authorizer: apigateway.CognitoUserPoolsAuthorizer,
    ) -> None:
        """Configure admin endpoints (with Cognito authentication) - proxy all to Flask app."""
        # Create proxy integration for admin Flask app
        admin_integration = apigateway.LambdaIntegration(
            admin_function,
            proxy=True,  # Proxy all requests to Flask app
        )
        
        # Proxy /admin/* to admin Flask app with Cognito authorizer
        admin_resource = api.root.add_resource("admin")
        admin_resource.add_resource("{proxy+}").add_method(
            "ANY",
            admin_integration,
            authorizer=authorizer,
        )
    
    def _create_custom_domain(
        self, api: apigateway.RestApi, domain_name: str, certificate_arn: str
    ) -> apigateway.DomainName:
        """Create custom domain for API Gateway."""
        # Import the certificate
        certificate = acm.Certificate.from_certificate_arn(
            self,
            "ApiCertificate",
            certificate_arn=certificate_arn,
        )
        
        # Create custom domain for REST API Gateway
        # Note: REST API Gateway uses regional endpoints
        custom_domain = apigateway.DomainName(
            self,
            "ApiCustomDomain",
            domain_name=f"api.{domain_name}",
            certificate=certificate,
            security_policy=apigateway.SecurityPolicy.TLS_1_2,
            endpoint_type=apigateway.EndpointType.REGIONAL,  # REST API uses regional endpoints
        )
        
        # Create base path mapping to the API
        # Note: For REST API Gateway, we need to specify the stage
        custom_domain.add_base_path_mapping(
            api,
            base_path="",  # Empty base path means root
            stage=api.deployment_stage,  # Explicitly set the stage
        )
        
        return custom_domain
