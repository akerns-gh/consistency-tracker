# Legacy Lambda Handlers

This directory contains the original Lambda handler functions that have been replaced by Flask applications.

## Migration Status

All endpoints have been migrated to Flask:
- **Admin endpoints**: Now in `admin_app.py`
- **Player endpoints**: Now in `player_app.py`

## Files Archived

### Admin Handlers (14 files)
- `check_role.py` - GET /admin/check-role
- `clubs.py` - Club management (CRUD)
- `teams.py` - Team management (CRUD)
- `players.py` - Player management (CRUD)
- `activities.py` - Activity management (CRUD)
- `content.py` - Content management (CRUD)
- `content_publish.py` - Publish/unpublish content
- `content_reorder.py` - Reorder content pages
- `image_upload.py` - Generate pre-signed S3 URLs
- `overview.py` - Team statistics and overview
- `export.py` - Export week data (CSV)
- `week_advance.py` - Advance to next week
- `reflections.py` - View all player reflections

### Player Handlers (7 files)
- `get_player.py` - GET /player/{uniqueLink}
- `get_week.py` - GET /player/{uniqueLink}/week/{weekId}
- `get_progress.py` - GET /player/{uniqueLink}/progress
- `checkin.py` - POST /player/{uniqueLink}/checkin
- `save_reflection.py` - PUT /player/{uniqueLink}/reflection
- `get_leaderboard.py` - GET /leaderboard/{weekId}
- `list_content.py` - GET /content
- `get_content.py` - GET /content/{slug}

## When to Delete

These files can be safely deleted after:
1. ✅ Successful deployment of Flask applications
2. ✅ All endpoints tested and verified
3. ✅ Production validation complete (1-2 weeks)
4. ✅ No rollback needed

## Rollback Plan

If rollback is needed:
1. Restore files from this directory to their original locations
2. Revert CDK stack changes in `api_stack.py`
3. Redeploy infrastructure

