"""
Database Stack - DynamoDB Tables for Consistency Tracker

Creates all DynamoDB tables with proper schemas, GSIs, and multi-tenant support.
"""

from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    RemovalPolicy,
)
from constructs import Construct


class DatabaseStack(Stack):
    """Stack containing all DynamoDB tables for the Consistency Tracker application."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Club Table
        # Partition Key: clubId
        # No GSI needed (single partition key lookup)
        self.club_table = dynamodb.Table(
            self,
            "ClubTable",
            table_name="ConsistencyTracker-Clubs",
            partition_key=dynamodb.Attribute(
                name="clubId", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # Player Table
        # Partition Key: playerId
        # GSI: teamId (for querying all players in a team)
        self.player_table = dynamodb.Table(
            self,
            "PlayerTable",
            table_name="ConsistencyTracker-Players",
            partition_key=dynamodb.Attribute(
                name="playerId", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,  # Note: Deprecated but still works. Will update when CDK provides correct API.
            removal_policy=RemovalPolicy.RETAIN,  # Retain on stack deletion
        )

        # GSI: teamId for querying players by team
        self.player_table.add_global_secondary_index(
            index_name="teamId-index",
            partition_key=dynamodb.Attribute(
                name="teamId", type=dynamodb.AttributeType.STRING
            ),
        )

        # GSI: clubId for querying players by club
        self.player_table.add_global_secondary_index(
            index_name="clubId-index",
            partition_key=dynamodb.Attribute(
                name="clubId", type=dynamodb.AttributeType.STRING
            ),
        )

        # Activity Table
        # Partition Key: activityId
        # GSI: teamId (for querying all activities for a team)
        self.activity_table = dynamodb.Table(
            self,
            "ActivityTable",
            table_name="ConsistencyTracker-Activities",
            partition_key=dynamodb.Attribute(
                name="activityId", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # GSI: teamId for querying activities by team
        self.activity_table.add_global_secondary_index(
            index_name="teamId-index",
            partition_key=dynamodb.Attribute(
                name="teamId", type=dynamodb.AttributeType.STRING
            ),
        )

        # GSI: clubId for querying activities by club
        self.activity_table.add_global_secondary_index(
            index_name="clubId-index",
            partition_key=dynamodb.Attribute(
                name="clubId", type=dynamodb.AttributeType.STRING
            ),
        )

        # Tracking Table
        # Partition Key: trackingId (composite: playerId#weekId#date)
        # GSIs: playerId, weekId, teamId (for various query patterns)
        self.tracking_table = dynamodb.Table(
            self,
            "TrackingTable",
            table_name="ConsistencyTracker-Tracking",
            partition_key=dynamodb.Attribute(
                name="trackingId", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # GSI: playerId for querying all tracking records for a player
        self.tracking_table.add_global_secondary_index(
            index_name="playerId-index",
            partition_key=dynamodb.Attribute(
                name="playerId", type=dynamodb.AttributeType.STRING
            ),
        )

        # GSI: weekId for querying all tracking records for a week (leaderboard)
        self.tracking_table.add_global_secondary_index(
            index_name="weekId-index",
            partition_key=dynamodb.Attribute(
                name="weekId", type=dynamodb.AttributeType.STRING
            ),
        )

        # GSI: teamId for querying all tracking records for a team
        self.tracking_table.add_global_secondary_index(
            index_name="teamId-index",
            partition_key=dynamodb.Attribute(
                name="teamId", type=dynamodb.AttributeType.STRING
            ),
        )

        # GSI: clubId for querying all tracking records for a club
        self.tracking_table.add_global_secondary_index(
            index_name="clubId-index",
            partition_key=dynamodb.Attribute(
                name="clubId", type=dynamodb.AttributeType.STRING
            ),
        )

        # Reflection Table
        # Partition Key: reflectionId (composite: playerId#weekId)
        # GSIs: playerId, teamId (for querying reflections)
        self.reflection_table = dynamodb.Table(
            self,
            "ReflectionTable",
            table_name="ConsistencyTracker-Reflections",
            partition_key=dynamodb.Attribute(
                name="reflectionId", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # GSI: playerId for querying all reflections for a player
        self.reflection_table.add_global_secondary_index(
            index_name="playerId-index",
            partition_key=dynamodb.Attribute(
                name="playerId", type=dynamodb.AttributeType.STRING
            ),
        )

        # GSI: teamId for querying all reflections for a team
        self.reflection_table.add_global_secondary_index(
            index_name="teamId-index",
            partition_key=dynamodb.Attribute(
                name="teamId", type=dynamodb.AttributeType.STRING
            ),
        )

        # GSI: clubId for querying all reflections for a club
        self.reflection_table.add_global_secondary_index(
            index_name="clubId-index",
            partition_key=dynamodb.Attribute(
                name="clubId", type=dynamodb.AttributeType.STRING
            ),
        )

        # ContentPages Table
        # Partition Key: pageId
        # GSI: teamId (for querying all content pages for a team)
        self.content_pages_table = dynamodb.Table(
            self,
            "ContentPagesTable",
            table_name="ConsistencyTracker-ContentPages",
            partition_key=dynamodb.Attribute(
                name="pageId", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # GSI: teamId for querying content pages by team
        self.content_pages_table.add_global_secondary_index(
            index_name="teamId-index",
            partition_key=dynamodb.Attribute(
                name="teamId", type=dynamodb.AttributeType.STRING
            ),
        )

        # GSI: clubId for querying content pages by club
        self.content_pages_table.add_global_secondary_index(
            index_name="clubId-index",
            partition_key=dynamodb.Attribute(
                name="clubId", type=dynamodb.AttributeType.STRING
            ),
        )

        # Team/Config Table
        # Partition Key: teamId
        # GSI: clubId (for querying all teams in a club)
        self.team_table = dynamodb.Table(
            self,
            "TeamTable",
            table_name="ConsistencyTracker-Teams",
            partition_key=dynamodb.Attribute(
                name="teamId", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # GSI: clubId for querying teams by club
        self.team_table.add_global_secondary_index(
            index_name="clubId-index",
            partition_key=dynamodb.Attribute(
                name="clubId", type=dynamodb.AttributeType.STRING
            ),
        )

