#!/usr/bin/env python3
"""
Interactive script to update firstName/lastName for coaches and club admins.

This script allows you to:
- List all coaches/club admins with potentially incorrect names
- Select users to update
- Enter correct firstName and lastName
- Update DynamoDB records
- Supports bulk updates via CSV input
"""

import boto3
import csv
import sys
from typing import Dict, List, Optional
from botocore.exceptions import ClientError

# Configuration
AWS_REGION = "us-east-1"
COACH_TABLE = "ConsistencyTracker-Coaches"
CLUB_ADMIN_TABLE = "ConsistencyTracker-ClubAdmins"

def get_all_coaches() -> List[Dict]:
    """Get all coaches from DynamoDB."""
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(COACH_TABLE)
    
    coaches = []
    last_evaluated_key = None
    
    while True:
        if last_evaluated_key:
            response = table.scan(ExclusiveStartKey=last_evaluated_key)
        else:
            response = table.scan()
        
        coaches.extend(response.get('Items', []))
        
        last_evaluated_key = response.get('LastEvaluatedKey')
        if not last_evaluated_key:
            break
    
    return coaches

def get_all_club_admins() -> List[Dict]:
    """Get all club admins from DynamoDB."""
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(CLUB_ADMIN_TABLE)
    
    admins = []
    last_evaluated_key = None
    
    while True:
        if last_evaluated_key:
            response = table.scan(ExclusiveStartKey=last_evaluated_key)
        else:
            response = table.scan()
        
        admins.extend(response.get('Items', []))
        
        last_evaluated_key = response.get('LastEvaluatedKey')
        if not last_evaluated_key:
            break
    
    return admins

def update_coach_name(coach_id: str, first_name: str, last_name: str) -> bool:
    """Update coach firstName and lastName."""
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(COACH_TABLE)
    
    try:
        from datetime import datetime
        table.update_item(
            Key={"coachId": coach_id},
            UpdateExpression="SET firstName = :firstName, lastName = :lastName, updatedAt = :updatedAt",
            ExpressionAttributeValues={
                ":firstName": first_name,
                ":lastName": last_name,
                ":updatedAt": datetime.utcnow().isoformat() + "Z"
            }
        )
        return True
    except Exception as e:
        print(f"  ❌ Error updating coach {coach_id}: {e}")
        return False

def update_club_admin_name(admin_id: str, first_name: str, last_name: str) -> bool:
    """Update club admin firstName and lastName."""
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(CLUB_ADMIN_TABLE)
    
    try:
        from datetime import datetime
        table.update_item(
            Key={"adminId": admin_id},
            UpdateExpression="SET firstName = :firstName, lastName = :lastName, updatedAt = :updatedAt",
            ExpressionAttributeValues={
                ":firstName": first_name,
                ":lastName": last_name,
                ":updatedAt": datetime.utcnow().isoformat() + "Z"
            }
        )
        return True
    except Exception as e:
        print(f"  ❌ Error updating club admin {admin_id}: {e}")
        return False

def interactive_update():
    """Interactive mode to update names one by one."""
    print("🔄 Interactive Name Update")
    print("=" * 70)
    
    # Get all users
    print("\n📊 Loading users...")
    coaches = get_all_coaches()
    admins = get_all_club_admins()
    print(f"✅ Found {len(coaches)} coaches and {len(admins)} club admins")
    
    # Show coaches
    if coaches:
        print("\n📋 COACHES:")
        print("-" * 70)
        for i, coach in enumerate(coaches, 1):
            first_name = coach.get('firstName', '')
            last_name = coach.get('lastName', '')
            email = coach.get('email', '')
            print(f"{i}. {first_name} {last_name} ({email})")
    
    # Show club admins
    if admins:
        print("\n📋 CLUB ADMINS:")
        print("-" * 70)
        for i, admin in enumerate(admins, len(coaches) + 1):
            first_name = admin.get('firstName', '')
            last_name = admin.get('lastName', '')
            email = admin.get('email', '')
            print(f"{i}. {first_name} {last_name} ({email})")
    
    if not coaches and not admins:
        print("\n✅ No users found. Nothing to update.")
        return
    
    # Select user to update
    print("\n" + "=" * 70)
    try:
        selection = input("Enter the number of the user to update (or 'q' to quit): ").strip()
        if selection.lower() == 'q':
            return
        
        index = int(selection) - 1
        if index < len(coaches):
            user = coaches[index]
            user_type = 'coach'
            user_id = user.get('coachId')
        elif index < len(coaches) + len(admins):
            user = admins[index - len(coaches)]
            user_type = 'admin'
            user_id = user.get('adminId')
        else:
            print("❌ Invalid selection")
            return
        
        # Get new names
        current_first = user.get('firstName', '')
        current_last = user.get('lastName', '')
        email = user.get('email', '')
        
        print(f"\n📝 Updating: {current_first} {current_last} ({email})")
        new_first = input(f"Enter first name (current: '{current_first}'): ").strip()
        new_last = input(f"Enter last name (current: '{current_last}'): ").strip()
        
        if not new_first or not new_last:
            print("❌ First name and last name are required")
            return
        
        # Confirm
        confirm = input(f"\nUpdate to '{new_first} {new_last}'? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("❌ Cancelled")
            return
        
        # Update
        if user_type == 'coach':
            success = update_coach_name(user_id, new_first, new_last)
        else:
            success = update_club_admin_name(user_id, new_first, new_last)
        
        if success:
            print(f"✅ Updated {user_type}: {new_first} {new_last}")
        else:
            print(f"❌ Failed to update {user_type}")
    
    except ValueError:
        print("❌ Invalid input")
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")

def bulk_update_from_csv(csv_file: str, dry_run: bool = False):
    """Bulk update names from CSV file."""
    print(f"🔄 Bulk Update from CSV{' (DRY RUN)' if dry_run else ''}")
    print("=" * 70)
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return
    
    # Expected CSV format: id,firstName,lastName,type
    # type: 'coach' or 'admin'
    updates = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            updates.append({
                'id': row.get('id', '').strip(),
                'firstName': row.get('firstName', '').strip(),
                'lastName': row.get('lastName', '').strip(),
                'type': row.get('type', '').strip().lower()
            })
    
    print(f"✅ Loaded {len(updates)} updates from CSV")
    
    if dry_run:
        print("\n📋 DRY RUN - Would update:")
        for update in updates:
            print(f"  {update['type']} {update['id']}: {update['firstName']} {update['lastName']}")
        return
    
    updated = 0
    errors = 0
    
    print("\n" + "=" * 70)
    print("📋 UPDATE REPORT")
    print("=" * 70)
    
    for update in updates:
        if not update['id'] or not update['firstName'] or not update['lastName']:
            print(f"  ⚠️  Skipping - missing required fields")
            errors += 1
            continue
        
        if update['type'] == 'coach':
            success = update_coach_name(update['id'], update['firstName'], update['lastName'])
        elif update['type'] == 'admin':
            success = update_club_admin_name(update['id'], update['firstName'], update['lastName'])
        else:
            print(f"  ❌ Invalid type: {update['type']} (must be 'coach' or 'admin')")
            errors += 1
            continue
        
        if success:
            print(f"  ✅ Updated {update['type']} {update['id']}: {update['firstName']} {update['lastName']}")
            updated += 1
        else:
            errors += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 UPDATE SUMMARY")
    print("=" * 70)
    print(f"Total updates: {len(updates)}")
    print(f"Updated: {updated}")
    print(f"Errors: {errors}")

if __name__ == "__main__":
    import os
    
    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        csv_file = sys.argv[1]
        dry_run = '--dry-run' in sys.argv
        bulk_update_from_csv(csv_file, dry_run)
    else:
        interactive_update()

