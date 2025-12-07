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
)
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
        domain_name: str = None,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Store domain name for CORS configuration
        self.domain_name = domain_name

        # Store references
        self.database_stack = database_stack
        self.auth_stack = auth_stack

        # Get Lambda code directory
        lambda_dir = Path(__file__).parent.parent / "lambda"

        # Create Lambda layer for shared dependencies
        layer = self._create_lambda_layer(lambda_dir)

        # Create shared Lambda code asset (shared utilities)
        shared_code = lambda_.Code.from_asset(str(lambda_dir / "shared"))

        # Create Lambda functions for player endpoints (no auth)
        player_functions = self._create_player_functions(
            lambda_dir, shared_code, layer
        )

        # Create Lambda functions for admin endpoints (with auth)
        admin_functions = self._create_admin_functions(
            lambda_dir, shared_code, layer
        )

        # Create API Gateway REST API
        api = self._create_api_gateway(auth_stack)

        # Create Cognito authorizer for admin endpoints
        authorizer = self._create_cognito_authorizer(api, auth_stack)

        # Configure player endpoints (no auth)
        self._configure_player_endpoints(api, player_functions)

        # Configure admin endpoints (with Cognito auth)
        self._configure_admin_endpoints(api, admin_functions, authorizer)

        # Output API endpoint
        CfnOutput(
            self,
            "ApiEndpoint",
            value=api.url,
            description="API Gateway endpoint URL",
            export_name="ConsistencyTracker-ApiEndpoint",
        )

    def _create_lambda_layer(self, lambda_dir: Path) -> lambda_.LayerVersion:
        """Create Lambda layer with Python dependencies."""
        layer_dir = lambda_dir / "layer" / "python"
        
        return lambda_.LayerVersion(
            self,
            "SharedLayer",
            code=lambda_.Code.from_asset(str(layer_dir)),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
            description="Shared dependencies (boto3, bleach, python-jose)",
        )

    def _create_player_functions(
        self,
        lambda_dir: Path,
        shared_code: lambda_.Code,
        layer: lambda_.LayerVersion,
    ) -> dict:
        """Create Lambda functions for player endpoints."""
        functions = {}

        # Common environment variables
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
        }

        # Common IAM role for player functions
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

        # Player endpoint functions
        player_functions_config = [
            ("get_player", "get_player.py", "Get player data and current week"),
            ("get_week", "get_week.py", "Get specific week data"),
            ("get_progress", "get_progress.py", "Get aggregated progress statistics"),
            ("checkin", "checkin.py", "Mark activity complete"),
            ("save_reflection", "save_reflection.py", "Save/update weekly reflection"),
            ("get_leaderboard", "get_leaderboard.py", "Get leaderboard for a week"),
            ("list_content", "list_content.py", "List all published content pages"),
            ("get_content", "get_content.py", "Get specific content page by slug"),
        ]

        for func_name, handler_file, description in player_functions_config:
            functions[func_name] = lambda_.Function(
                self,
                f"Player{func_name.title().replace('_', '')}Function",
                runtime=lambda_.Runtime.PYTHON_3_11,
                handler=f"{handler_file[:-3]}.lambda_handler",
                code=lambda_.Code.from_asset(
                    str(lambda_dir),
                    exclude=["**/admin/**", "**/layer/**", "**/__pycache__/**"],
                ),
                layers=[layer],
                environment=env_vars,
                role=player_role,
                timeout=Duration.seconds(30),
                memory_size=256,
                description=description,
                log_retention=logs.RetentionDays.ONE_WEEK,
            )

        return functions

    def _create_admin_functions(
        self,
        lambda_dir: Path,
        shared_code: lambda_.Code,
        layer: lambda_.LayerVersion,
    ) -> dict:
        """Create Lambda functions for admin endpoints."""
        functions = {}

        # Common environment variables
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
        }

        # Common IAM role for admin functions
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

        # Admin endpoint functions
        admin_functions_config = [
            ("check_role", "admin/check_role.py", "Verify user's admin role"),
            ("clubs", "admin/clubs.py", "Club management (CRUD)"),
            ("teams", "admin/teams.py", "Team management (CRUD)"),
            ("players", "admin/players.py", "Player management (CRUD)"),
            ("activities", "admin/activities.py", "Activity management (CRUD)"),
            ("content", "admin/content.py", "Content management (CRUD)"),
            ("content_publish", "admin/content_publish.py", "Publish/unpublish content"),
            ("content_reorder", "admin/content_reorder.py", "Reorder content pages"),
            ("image_upload", "admin/image_upload.py", "Generate pre-signed S3 URLs"),
            ("overview", "admin/overview.py", "Team statistics and overview"),
            ("export", "admin/export.py", "Export week data (CSV)"),
            ("week_advance", "admin/week_advance.py", "Advance to next week"),
            ("reflections", "admin/reflections.py", "View all player reflections"),
        ]

        for func_name, handler_file, description in admin_functions_config:
            functions[func_name] = lambda_.Function(
                self,
                f"Admin{func_name.title().replace('_', '')}Function",
                runtime=lambda_.Runtime.PYTHON_3_11,
                handler=f"{handler_file[:-3].replace('/', '.')}.lambda_handler",
                code=lambda_.Code.from_asset(
                    str(lambda_dir),
                    exclude=["**/layer/**", "**/__pycache__/**"],
                ),
                layers=[layer],
                environment=env_vars,
                role=admin_role,
                timeout=Duration.seconds(30),
                memory_size=256,
                description=description,
                log_retention=logs.RetentionDays.ONE_WEEK,
            )

        return functions

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
        self, api: apigateway.RestApi, functions: dict
    ) -> None:
        """Configure player endpoints (no authentication)."""
        player_resource = api.root.add_resource("player")
        
        # GET /player/{uniqueLink}
        unique_link_resource = player_resource.add_resource("{uniqueLink}")
        unique_link_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(functions["get_player"]),
        )

        # GET /player/{uniqueLink}/week/{weekId}
        week_resource = unique_link_resource.add_resource("week").add_resource(
            "{weekId}"
        )
        week_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(functions["get_week"]),
        )

        # GET /player/{uniqueLink}/progress
        progress_resource = unique_link_resource.add_resource("progress")
        progress_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(functions["get_progress"]),
        )

        # POST /player/{uniqueLink}/checkin
        checkin_resource = unique_link_resource.add_resource("checkin")
        checkin_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(functions["checkin"]),
        )

        # PUT /player/{uniqueLink}/reflection
        reflection_resource = unique_link_resource.add_resource("reflection")
        reflection_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(functions["save_reflection"]),
        )

        # GET /leaderboard/{weekId}
        leaderboard_resource = api.root.add_resource("leaderboard").add_resource(
            "{weekId}"
        )
        leaderboard_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(functions["get_leaderboard"]),
        )

        # GET /content
        content_resource = api.root.add_resource("content")
        content_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(functions["list_content"]),
        )

        # GET /content/{slug}
        content_slug_resource = content_resource.add_resource("{slug}")
        content_slug_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(functions["get_content"]),
        )

    def _configure_admin_endpoints(
        self,
        api: apigateway.RestApi,
        functions: dict,
        authorizer: apigateway.CognitoUserPoolsAuthorizer,
    ) -> None:
        """Configure admin endpoints (with Cognito authentication)."""
        admin_resource = api.root.add_resource("admin")

        # GET /admin/check-role
        check_role_resource = admin_resource.add_resource("check-role")
        check_role_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(functions["check_role"]),
            authorizer=authorizer,
        )

        # Club management endpoints
        clubs_resource = admin_resource.add_resource("clubs")
        clubs_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(functions["clubs"]),
            authorizer=authorizer,
        )
        clubs_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(functions["clubs"]),
            authorizer=authorizer,
        )

        # GET /admin/clubs/{clubId}
        club_id_resource = clubs_resource.add_resource("{clubId}")
        club_id_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(functions["clubs"]),
            authorizer=authorizer,
        )
        club_id_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(functions["clubs"]),
            authorizer=authorizer,
        )

        # Team management endpoints
        teams_resource = admin_resource.add_resource("teams")
        teams_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(functions["teams"]),
            authorizer=authorizer,
        )
        teams_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(functions["teams"]),
            authorizer=authorizer,
        )

        # GET /admin/teams/{teamId}
        team_id_resource = teams_resource.add_resource("{teamId}")
        team_id_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(functions["teams"]),
            authorizer=authorizer,
        )
        team_id_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(functions["teams"]),
            authorizer=authorizer,
        )

        # Player management endpoints
        players_resource = admin_resource.add_resource("players")
        players_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(functions["players"]),
            authorizer=authorizer,
        )
        players_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(functions["players"]),
            authorizer=authorizer,
        )

        # PUT /admin/players/{playerId}
        player_id_resource = players_resource.add_resource("{playerId}")
        player_id_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(functions["players"]),
            authorizer=authorizer,
        )
        player_id_resource.add_method(
            "DELETE",
            apigateway.LambdaIntegration(functions["players"]),
            authorizer=authorizer,
        )

        # Activity management endpoints
        activities_resource = admin_resource.add_resource("activities")
        activities_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(functions["activities"]),
            authorizer=authorizer,
        )
        activities_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(functions["activities"]),
            authorizer=authorizer,
        )

        # PUT /admin/activities/{activityId}
        activity_id_resource = activities_resource.add_resource("{activityId}")
        activity_id_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(functions["activities"]),
            authorizer=authorizer,
        )
        activity_id_resource.add_method(
            "DELETE",
            apigateway.LambdaIntegration(functions["activities"]),
            authorizer=authorizer,
        )

        # Content management endpoints
        content_resource = admin_resource.add_resource("content")
        content_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(functions["content"]),
            authorizer=authorizer,
        )
        content_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(functions["content"]),
            authorizer=authorizer,
        )

        # PUT /admin/content/{contentId}
        content_id_resource = content_resource.add_resource("{contentId}")
        content_id_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(functions["content"]),
            authorizer=authorizer,
        )
        content_id_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(functions["content"]),
            authorizer=authorizer,
        )
        content_id_resource.add_method(
            "DELETE",
            apigateway.LambdaIntegration(functions["content"]),
            authorizer=authorizer,
        )

        # PUT /admin/content/{contentId}/publish
        publish_resource = content_id_resource.add_resource("publish")
        publish_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(functions["content_publish"]),
            authorizer=authorizer,
        )

        # PUT /admin/content/reorder
        reorder_resource = content_resource.add_resource("reorder")
        reorder_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(functions["content_reorder"]),
            authorizer=authorizer,
        )

        # POST /admin/content/image-upload-url
        image_upload_resource = content_resource.add_resource("image-upload-url")
        image_upload_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(functions["image_upload"]),
            authorizer=authorizer,
        )

        # GET /admin/overview
        overview_resource = admin_resource.add_resource("overview")
        overview_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(functions["overview"]),
            authorizer=authorizer,
        )

        # GET /admin/export/{weekId}
        export_resource = admin_resource.add_resource("export").add_resource(
            "{weekId}"
        )
        export_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(functions["export"]),
            authorizer=authorizer,
        )

        # POST /admin/week/advance
        week_resource = admin_resource.add_resource("week")
        advance_resource = week_resource.add_resource("advance")
        advance_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(functions["week_advance"]),
            authorizer=authorizer,
        )

        # GET /admin/reflections
        reflections_resource = admin_resource.add_resource("reflections")
        reflections_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(functions["reflections"]),
            authorizer=authorizer,
        )
