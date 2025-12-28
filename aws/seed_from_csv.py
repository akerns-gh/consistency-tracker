#!/usr/bin/env python3
"""
Seed DynamoDB data from CSV files (post-deployment).

This is intentionally separate from infrastructure deploy. It is safe to re-run:
- Uses UPSERT semantics (put_item) for clubs/teams/activities/content when IDs provided
- Can optionally generate IDs when missing (clubs/teams/players/activities/content)

Recommended workflow:
1) Deploy infra: ./aws/deploy.sh
2) Configure domains: (now automated by deploy.py) or python aws/post_deploy_configure_domains.py --wait
3) Create admin user: python aws/create_admin_user.py
4) Seed data: python aws/seed_from_csv.py --clubs data/clubs.csv --teams data/teams.csv --players data/players.csv --activities data/activities.csv
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import boto3
from botocore.exceptions import ClientError


def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _log(msg: str) -> None:
    print(msg, flush=True)


def _die(msg: str, code: int = 1) -> None:
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(code)


def _read_csv(path: str) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [dict({k: (v or "").strip() for k, v in row.items()}) for row in reader]


def _parse_bool(v: str, default: bool = False) -> bool:
    if v == "":
        return default
    return v.lower() in ("1", "true", "yes", "y", "on")


def _parse_int(v: str, default: int = 0) -> int:
    if v == "":
        return default
    return int(v)


def _require(v: str, field: str, context: str) -> str:
    if not v:
        _die(f"Missing required field '{field}' in {context}")
    return v


def _ensure_table(dynamodb, name: str):
    return dynamodb.Table(name)


def _put_item(table, item: Dict[str, Any]) -> None:
    table.put_item(Item=item)


def seed_clubs(dynamodb, rows: List[Dict[str, str]], table_name: str) -> Dict[str, str]:
    """
    clubs.csv columns:
      clubId (optional), clubName (required)
    Returns mapping clubName -> clubId for convenience.
    """
    table = _ensure_table(dynamodb, table_name)
    name_to_id: Dict[str, str] = {}
    for i, r in enumerate(rows, start=1):
        club_name = _require(r.get("clubName", ""), "clubName", f"clubs.csv row {i}")
        club_id = r.get("clubId", "") or str(uuid.uuid4())
        item = {
            "clubId": club_id,
            "clubName": club_name,
            "createdAt": r.get("createdAt", "") or _now(),
        }
        _put_item(table, item)
        name_to_id[club_name] = club_id
        _log(f"✅ club: {club_name} ({club_id})")
    return name_to_id


def seed_teams(dynamodb, rows: List[Dict[str, str]], table_name: str, clubs_by_name: Dict[str, str]) -> Dict[str, str]:
    """
    teams.csv columns:
      teamId (optional), clubId OR clubName (one required), teamName (required), coachName (optional)
    Returns mapping teamName -> teamId for convenience.
    """
    table = _ensure_table(dynamodb, table_name)
    name_to_id: Dict[str, str] = {}
    for i, r in enumerate(rows, start=1):
        team_name = _require(r.get("teamName", ""), "teamName", f"teams.csv row {i}")
        club_id = (r.get("clubId", "") or "").strip()
        club_name = (r.get("clubName", "") or "").strip()
        if not club_id and club_name:
            club_id = clubs_by_name.get(club_name, "")
        club_id = _require(club_id, "clubId/clubName", f"teams.csv row {i}")
        team_id = r.get("teamId", "") or str(uuid.uuid4())
        item = {
            "teamId": team_id,
            "clubId": club_id,
            "teamName": team_name,
            "coachName": (r.get("coachName", "") or "").strip(),
            "settings": {},
            "isActive": _parse_bool(r.get("isActive", ""), default=True),
            "createdAt": r.get("createdAt", "") or _now(),
        }
        _put_item(table, item)
        name_to_id[team_name] = team_id
        _log(f"✅ team: {team_name} ({team_id}) club={club_id}")
    return name_to_id


def seed_players(dynamodb, rows: List[Dict[str, str]], table_name: str, clubs_by_name: Dict[str, str], teams_by_name: Dict[str, str]) -> None:
    """
    players.csv columns:
      playerId (optional), name (required), email (optional), clubId OR clubName (one required),
      teamId OR teamName (one required), uniqueLink (optional)
    """
    table = _ensure_table(dynamodb, table_name)
    for i, r in enumerate(rows, start=1):
        name = _require(r.get("name", ""), "name", f"players.csv row {i}")
        club_id = (r.get("clubId", "") or "").strip()
        club_name = (r.get("clubName", "") or "").strip()
        if not club_id and club_name:
            club_id = clubs_by_name.get(club_name, "")
        club_id = _require(club_id, "clubId/clubName", f"players.csv row {i}")

        team_id = (r.get("teamId", "") or "").strip()
        team_name = (r.get("teamName", "") or "").strip()
        if not team_id and team_name:
            team_id = teams_by_name.get(team_name, "")
        team_id = _require(team_id, "teamId/teamName", f"players.csv row {i}")

        player_id = r.get("playerId", "") or str(uuid.uuid4())
        unique_link = r.get("uniqueLink", "") or uuid.uuid4().hex[:12]
        item = {
            "playerId": player_id,
            "name": name,
            "email": (r.get("email", "") or "").strip(),
            "clubId": club_id,
            "teamId": team_id,
            "uniqueLink": unique_link,
            "isActive": _parse_bool(r.get("isActive", ""), default=True),
            "createdAt": r.get("createdAt", "") or _now(),
        }
        _put_item(table, item)
        _log(f"✅ player: {name} ({player_id}) team={team_id} link={unique_link}")


def seed_activities(dynamodb, rows: List[Dict[str, str]], table_name: str, clubs_by_name: Dict[str, str], teams_by_name: Dict[str, str]) -> None:
    """
    activities.csv columns:
      activityId (optional), clubId OR clubName (one required), scope (club|team, default=club),
      teamId OR teamName (required if scope=team),
      name (required), description (optional), frequency (optional), pointValue (optional int),
      displayOrder (optional int), isActive (optional bool)
    """
    table = _ensure_table(dynamodb, table_name)
    for i, r in enumerate(rows, start=1):
        name = _require(r.get("name", ""), "name", f"activities.csv row {i}")
        club_id = (r.get("clubId", "") or "").strip()
        club_name = (r.get("clubName", "") or "").strip()
        if not club_id and club_name:
            club_id = clubs_by_name.get(club_name, "")
        club_id = _require(club_id, "clubId/clubName", f"activities.csv row {i}")

        scope = (r.get("scope", "") or "club").strip().lower()
        if scope not in ("club", "team"):
            _die(f"Invalid scope '{scope}' in activities.csv row {i} (must be club|team)")

        team_id: Optional[str] = None
        if scope == "team":
            team_id_raw = (r.get("teamId", "") or "").strip()
            team_name = (r.get("teamName", "") or "").strip()
            if not team_id_raw and team_name:
                team_id_raw = teams_by_name.get(team_name, "")
            team_id = _require(team_id_raw, "teamId/teamName", f"activities.csv row {i}")

        activity_id = r.get("activityId", "") or str(uuid.uuid4())
        item = {
            "activityId": activity_id,
            "clubId": club_id,
            "teamId": team_id,
            "scope": scope,
            "name": name,
            "description": (r.get("description", "") or "").strip(),
            "frequency": (r.get("frequency", "") or "daily").strip(),
            "pointValue": _parse_int(r.get("pointValue", ""), default=1),
            "displayOrder": _parse_int(r.get("displayOrder", ""), default=999),
            "isActive": _parse_bool(r.get("isActive", ""), default=True),
            "createdAt": r.get("createdAt", "") or _now(),
        }
        _put_item(table, item)
        _log(f"✅ activity: {name} ({activity_id}) scope={scope}")


def seed_content_pages(
    dynamodb,
    rows: List[Dict[str, str]],
    table_name: str,
    clubs_by_name: Dict[str, str],
    teams_by_name: Dict[str, str],
) -> None:
    """
    content_pages.csv columns:
      pageId (optional), clubId OR clubName (one required), scope (club|team, default=club),
      teamId OR teamName (required if scope=team),
      title (required), slug (required), category (optional), htmlContent (optional),
      isPublished (optional bool), displayOrder (optional int)
    """
    table = _ensure_table(dynamodb, table_name)
    for i, r in enumerate(rows, start=1):
        title = _require(r.get("title", ""), "title", f"content_pages.csv row {i}")
        slug = _require(r.get("slug", ""), "slug", f"content_pages.csv row {i}")

        club_id = (r.get("clubId", "") or "").strip()
        club_name = (r.get("clubName", "") or "").strip()
        if not club_id and club_name:
            club_id = clubs_by_name.get(club_name, "")
        club_id = _require(club_id, "clubId/clubName", f"content_pages.csv row {i}")

        scope = (r.get("scope", "") or "club").strip().lower()
        if scope not in ("club", "team"):
            _die(f"Invalid scope '{scope}' in content_pages.csv row {i} (must be club|team)")

        team_id: Optional[str] = None
        if scope == "team":
            team_id_raw = (r.get("teamId", "") or "").strip()
            team_name = (r.get("teamName", "") or "").strip()
            if not team_id_raw and team_name:
                team_id_raw = teams_by_name.get(team_name, "")
            team_id = _require(team_id_raw, "teamId/teamName", f"content_pages.csv row {i}")

        page_id = r.get("pageId", "") or str(uuid.uuid4())
        item = {
            "pageId": page_id,
            "clubId": club_id,
            "teamId": team_id,
            "scope": scope,
            "title": title,
            "slug": slug,
            "category": (r.get("category", "") or "").strip(),
            "htmlContent": (r.get("htmlContent", "") or "").strip(),
            "isPublished": _parse_bool(r.get("isPublished", ""), default=False),
            "displayOrder": _parse_int(r.get("displayOrder", ""), default=999),
            "createdAt": r.get("createdAt", "") or _now(),
        }
        _put_item(table, item)
        _log(f"✅ content: {title} ({page_id}) scope={scope} slug={slug}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed DynamoDB from CSV files.")
    parser.add_argument("--region", default=os.environ.get("AWS_REGION", "us-east-1"))
    parser.add_argument("--clubs")
    parser.add_argument("--teams")
    parser.add_argument("--players")
    parser.add_argument("--activities")
    parser.add_argument("--content-pages")

    parser.add_argument("--club-table", default="ConsistencyTracker-Clubs")
    parser.add_argument("--team-table", default="ConsistencyTracker-Teams")
    parser.add_argument("--player-table", default="ConsistencyTracker-Players")
    parser.add_argument("--activity-table", default="ConsistencyTracker-Activities")
    parser.add_argument("--content-pages-table", default="ConsistencyTracker-ContentPages")

    args = parser.parse_args()

    if not any([args.clubs, args.teams, args.players, args.activities, args.content_pages]):
        _die("Provide at least one CSV input: --clubs/--teams/--players/--activities/--content-pages")

    session = boto3.Session(region_name=args.region)
    dynamodb = session.resource("dynamodb")

    clubs_by_name: Dict[str, str] = {}
    teams_by_name: Dict[str, str] = {}

    if args.clubs:
        _log(f"Seeding clubs from {args.clubs} ...")
        clubs_by_name = seed_clubs(dynamodb, _read_csv(args.clubs), args.club_table)
    if args.teams:
        _log(f"Seeding teams from {args.teams} ...")
        teams_by_name = seed_teams(dynamodb, _read_csv(args.teams), args.team_table, clubs_by_name)
    if args.players:
        _log(f"Seeding players from {args.players} ...")
        seed_players(dynamodb, _read_csv(args.players), args.player_table, clubs_by_name, teams_by_name)
    if args.activities:
        _log(f"Seeding activities from {args.activities} ...")
        seed_activities(dynamodb, _read_csv(args.activities), args.activity_table, clubs_by_name, teams_by_name)
    if args.content_pages:
        _log(f"Seeding content pages from {args.content_pages} ...")
        seed_content_pages(
            dynamodb,
            _read_csv(args.content_pages),
            args.content_pages_table,
            clubs_by_name,
            teams_by_name,
        )

    _log("\n🎉 Seed complete.")


if __name__ == "__main__":
    try:
        main()
    except ClientError as e:
        _die(f"AWS error: {e}")
    except Exception as e:
        _die(f"Error: {e}")


