# CSV Seed Files

This folder contains **example CSV templates** you can use to populate DynamoDB after deployment.

Seeding is intentionally separate from infrastructure deployment.

## Usage

From repo root:

```bash
python aws/seed_from_csv.py \
  --clubs data/clubs.csv \
  --teams data/teams.csv \
  --players data/players.csv \
  --activities data/activities.csv \
  --content-pages data/content_pages.csv
```

## Notes

- If you reference `clubName` / `teamName`, you should seed **clubs first**, then **teams**, then **players/activities/content**.
- If you already know IDs, you can provide `clubId` / `teamId` directly and skip earlier CSVs.
- The script uses **put_item** (UPSERT). If you provide the same IDs, it will overwrite the existing item.


