#!/usr/bin/env python3
"""
Script to create test data: team 2030, 5 players, and 2 coaches (1 per team)
for Demo Club 1.
"""

import boto3
import uuid
import secrets
from datetime import datetime
from typing import Optional

# DynamoDB setup
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
teams_table = dynamodb.Table('ConsistencyTracker-Teams')
players_table = dynamodb.Table('ConsistencyTracker-Players')

# Cognito setup for coaches
cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
COGNITO_USER_POOL_ID = 'us-east-1_1voH0LIGL'  # From earlier console logs

def get_club_id_by_name(club_name: str) -> Optional[str]:
    """Get club ID by club name."""
    clubs_table = dynamodb.Table('ConsistencyTracker-Clubs')
    response = clubs_table.scan(
        FilterExpression='clubName = :name',
        ExpressionAttributeValues={':name': club_name}
    )
    items = response.get('Items', [])
    if items:
        return items[0].get('clubId')
    return None

def create_team_2030(club_id: str) -> bool:
    """Create team 2030 if it doesn't exist."""
    # Check if team exists
    try:
        response = teams_table.get_item(Key={'teamId': '2030'})
        if 'Item' in response:
            print("✅ Team 2030 already exists")
            return True
    except Exception as e:
        print(f"Error checking team 2030: {e}")
    
    # Create team 2030
    now = datetime.utcnow().isoformat() + "Z"
    team_item = {
        'teamId': '2030',
        'clubId': club_id,
        'teamName': 'Team 2030',
        'settings': {
            'weekStartDay': 'Monday',
            'autoAdvanceWeek': False,
            'scoringMethod': 'points',
        },
        'isActive': True,
        'createdAt': now,
    }
    
    try:
        teams_table.put_item(Item=team_item)
        print(f"✅ Created team 2030")
        return True
    except Exception as e:
        print(f"❌ Failed to create team 2030: {e}")
        return False

def create_player(name: str, email: str, team_id: str, club_id: str) -> Optional[str]:
    """Create a player."""
    player_id = str(uuid.uuid4())
    unique_link = secrets.token_urlsafe(32)
    now = datetime.utcnow().isoformat() + "Z"
    
    player_item = {
        'playerId': player_id,
        'name': name,
        'email': email,
        'uniqueLink': unique_link,
        'clubId': club_id,
        'teamId': team_id,
        'isActive': True,
        'createdAt': now,
    }
    
    try:
        players_table.put_item(Item=player_item)
        print(f"✅ Created player: {name} ({player_id}) on team {team_id}")
        return player_id
    except Exception as e:
        print(f"❌ Failed to create player {name}: {e}")
        return None

def create_coach(email: str, password: str, team_id: str, club_id: str) -> bool:
    """Create a coach in Cognito and add to team group."""
    try:
        # Create user in Cognito
        response = cognito_client.admin_create_user(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=email,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'email_verified', 'Value': 'true'},
            ],
            TemporaryPassword=password,
            MessageAction='SUPPRESS',  # Don't send welcome email
        )
        
        # Set permanent password
        cognito_client.admin_set_user_password(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=email,
            Password=password,
            Permanent=True
        )
        
        # Add to coach group for this team
        group_name = f"coach-{club_id}-{team_id}"
        try:
            cognito_client.admin_add_user_to_group(
                UserPoolId=COGNITO_USER_POOL_ID,
                Username=email,
                GroupName=group_name
            )
            print(f"✅ Created coach: {email} for team {team_id}")
            return True
        except Exception as e:
            if 'already a member' in str(e) or 'already exists' in str(e):
                print(f"✅ Coach {email} already exists for team {team_id}")
                return True
            else:
                print(f"⚠️  Created coach {email} but failed to add to group {group_name}: {e}")
                return True  # Still consider it a success
                
    except Exception as e:
        if 'already exists' in str(e) or 'UsernameExistsException' in str(e):
            print(f"✅ Coach {email} already exists")
            return True
        print(f"❌ Failed to create coach {email}: {e}")
        return False

def main():
    print("🚀 Creating test data for Demo Club 1...")
    
    # Get club ID
    club_id = get_club_id_by_name('Demo Club 1')
    if not club_id:
        print("❌ Could not find 'Demo Club 1'. Please check the club name.")
        return
    
    print(f"✅ Found club: Demo Club 1 (ID: {club_id})")
    
    # Create team 2030
    if not create_team_2030(club_id):
        print("❌ Failed to create team 2030. Aborting.")
        return
    
    # Create players
    print("\n📝 Creating players...")
    players = [
        # 3 players for team 2031
        ('Player 1 - Team 2031', 'test-player-1@repwarrior.net', '2031'),
        ('Player 2 - Team 2031', 'test-player-2@repwarrior.net', '2031'),
        ('Player 3 - Team 2031', 'test-player-3@repwarrior.net', '2031'),
        # 2 players for team 2030
        ('Player 4 - Team 2030', 'test-player-4@repwarrior.net', '2030'),
        ('Player 5 - Team 2030', 'test-player-5@repwarrior.net', '2030'),
    ]
    
    player_ids = []
    for name, email, team_id in players:
        player_id = create_player(name, email, team_id, club_id)
        if player_id:
            player_ids.append(player_id)
    
    # Create coaches (1 per team)
    print("\n👨‍🏫 Creating coaches...")
    coaches = [
        ('test-coach-1@repwarrior.net', 'TempPass123!2025', '2031'),
        ('test-coach-2@repwarrior.net', 'TempPass123!2025', '2030'),
    ]
    
    for email, password, team_id in coaches:
        create_coach(email, password, team_id, club_id)
    
    print(f"\n✅ Done! Created:")
    print(f"   - Team 2030")
    print(f"   - {len(player_ids)} players")
    print(f"   - {len(coaches)} coaches")

if __name__ == '__main__':
    main()

