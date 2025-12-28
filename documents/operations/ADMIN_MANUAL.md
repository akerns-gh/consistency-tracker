# Admin User Management Manual

This document describes the process for creating and managing admin users in the Consistency Tracker application.

## Overview

Admin users are authenticated through AWS Cognito User Pool. When a new admin user is created, they receive a temporary password and must change it on their first login. The application sends automated email notifications for user invitations, club/team creation, and password resets via AWS SES.

This manual covers:

1. Admin group hierarchy and permissions
2. Creating new admin users
3. Email notifications
4. First-time login process
5. Password requirements
6. Troubleshooting

## Admin Group Hierarchy

The application uses a hierarchical admin group structure to manage permissions:

### Group Types

1. **`app-admin`** (Platform Administrators)
   - **Scope**: Platform-wide access to all clubs
   - **Permissions**:
     - Create new clubs
     - Access all clubs and teams
     - Manage platform settings
   - **Creation**: Created manually via AWS Console or CLI (see "Creating Your First App-Admin" below)

2. **`club-{clubName}-admins`** (Club Administrators)
   - **Scope**: Access to a specific club and all its teams
   - **Permissions**:
     - Create teams within their club
     - Manage club settings
     - Access all teams in their club
     - Cannot create new clubs
   - **Creation**: Automatically created when an `app-admin` creates a new club
   - **Naming**: Uses sanitized club name (lowercase, underscores for spaces/special chars)
   - **Example**: `club-acme_club-admins` for club named "ACME CLUB"

3. **`coach-{clubId}-{teamId}`** (Team Coaches)
   - **Scope**: Access to a specific team within a club
   - **Permissions**:
     - View and manage team data
     - Access team-specific settings
     - Cannot create teams or clubs
   - **Creation**: Automatically created when a `club-admin` creates a new team
   - **Auto-assignment**: The club-admin who creates the team is automatically added to this group
   - **Example**: `coach-abc123-def456-789-xyz987-654-321` for team `xyz987-654-321` in club `abc123-def456-789`

### Automatic Group Creation

The system automatically creates admin groups when clubs and teams are created:

- **When an `app-admin` creates a club:**
  - The system automatically creates a `club-{sanitizedClubName}-admins` group in Cognito
  - The group name is based on the club name (sanitized for Cognito compatibility)
  - This group can then be used to assign club administrators

- **When a `club-admin` creates a team:**
  - The system automatically creates a `coach-{clubId}-{teamId}` group in Cognito
  - The club-admin who created the team is automatically added to this group
  - This allows the creator to immediately access and manage the team

### Group Assignment Workflow

```
1. App-admin creates club → `club-{sanitizedClubName}-admins` group created automatically
   → Email confirmation sent to app-admin
   → If club-admin created during club creation, invitation email sent with credentials
   → The initial club-admin's `custom:clubId` attribute is automatically set
2. App-admin can add additional club-admins via Club Management UI → Users created with `custom:clubId` set
   → Invitation email sent with credentials
   → Users automatically added to `club-{sanitizedClubName}-admins` group
3. Club-admin creates team → `coach-{clubId}-{teamId}` group created automatically
   → Email confirmation sent to club-admin
4. Club-admin (creator) automatically added to `coach-{clubId}-{teamId}` group
5. Additional coaches can be manually added to `coach-{clubId}-{teamId}` group
```

## Email Notifications

The application automatically sends email notifications for various events:

### Email Types

1. **User Invitation** - Sent when creating a new admin/coach user
   - Includes temporary password
   - Includes login URL
   - Sent to the new user's email address

2. **Club Creation** - Sent when a new club is created
   - Confirmation to app-admin who created the club
   - Invitation to new club-admin (if created during club creation)

3. **Team Creation** - Sent when a new team is created
   - Confirmation to club-admin who created the team

4. **Player Invitation** - Sent when creating or inviting a player
   - Includes temporary password and login credentials
   - Sent to player's email address

5. **Password Reset** - Sent via Cognito when user requests password reset
   - Handled automatically by Cognito via SES

### Email Configuration

Emails are sent via AWS SES using a verified Proton Mail custom domain. See [aws/SES_SETUP.md](../aws/SES_SETUP.md) for configuration instructions.

**Note**: If SES is not configured, the application will still function, but email notifications will not be sent. Check CloudWatch logs for email sending errors.

## Creating Your First App-Admin

Before you can create clubs, you need at least one `app-admin` user. Here's how to create one:

### Using AWS Console

1. **Create the user** (follow "Creating New Admin Users" section below)
2. **Add to app-admin group:**
   - Go to AWS Console → Cognito → User Pools → ConsistencyTracker-AdminPool
   - Select the user
   - Go to "Groups" tab
   - Click "Add user to group"
   - Select `app-admin` group
   - Click "Add"

### Using AWS CLI

```bash
# Get User Pool ID
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name ConsistencyTracker-Auth \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

# Create user (if not already created)
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username admin@example.com \
  --user-attributes Name=email,Value=admin@example.com \
  --temporary-password "TempPass123!2025" \
  --message-action SUPPRESS \
  --region us-east-1

# Add to app-admin group
aws cognito-idp admin-add-user-to-group \
  --user-pool-id $USER_POOL_ID \
  --username admin@example.com \
  --group-name app-admin \
  --region us-east-1
```

### Using Python Script

Edit `aws/create_admin_user.py` and change the `ADMIN_GROUP_NAME` to `"app-admin"`:

```python
ADMIN_GROUP_NAME = "app-admin"  # For platform administrators
```

Then run:
```bash
cd aws
python create_admin_user.py
```

## Creating New Admin Users

### Option 1: Using Admin Dashboard UI (Recommended for Club-Admins)

**For App-Admins Adding Club-Admins to Existing Clubs:**

App-admins can add additional club-admins to existing clubs directly through the Club Management interface:

1. **Navigate to Club Management:**
   - Log in as an app-admin
   - Go to the "Clubs" section in the admin dashboard
   - Find the club you want to add an admin to

2. **Edit the Club:**
   - Click "Edit" on the club
   - Scroll to the "Additional Club Administrator (optional)" section
   - Enter the new admin's email address
   - Enter a temporary password (must meet password requirements)
   - Click "Update Club"

3. **What Happens:**
   - The club name is updated (if changed)
   - A new club-admin user is created in Cognito
   - The `custom:clubId` attribute is automatically set to the club's ID
   - The user is added to the `club-{sanitizedClubName}-admins` group
   - An invitation email is sent to the new admin with login credentials

**Note:** This method ensures the `custom:clubId` attribute is properly set, which is required for club-admins to access admin endpoints.

**For Creating Clubs with Initial Club-Admin:**

When creating a new club through the UI:
- The initial club-admin email and password are **required**
- The club-admin is automatically created with `custom:clubId` set
- An invitation email is sent immediately

### Option 2: Using Python Script

The easiest way to create a new admin user is using the provided Python script:

1. **Edit the script configuration:**
   ```bash
   # Open the script
   nano aws/create_admin_user.py
   ```

2. **Update the configuration section:**
   ```python
   # Admin User Configuration
   ADMIN_EMAIL = "newadmin@example.com"  # Change to the new admin's email
   ADMIN_USERNAME = "newadmin@example.com"  # Usually same as email
   TEMPORARY_PASSWORD = "TempPass123!2025"  # Must meet password policy
   ```

3. **Run the script:**
   ```bash
   cd aws
   python create_admin_user.py
   ```

   The script will:
   - Automatically fetch the User Pool ID from CloudFormation
   - Create the admin user with the specified email and temporary password
   - Add the user to the specified admin group (default: `club-admins`, but can be changed to `app-admin` or a dynamic group)
   - Handle errors gracefully (e.g., user already exists)

4. **Share credentials with the new admin:**
   - Email: The email address you configured
   - Temporary Password: The temporary password you set
   - Login URL: `https://repwarrior.net/login` (for all users - players and admins use the same login page)

### Option 3: Using AWS Console

**⚠️ Important Note for Club-Admins:** If manually creating a club-admin user via AWS Console, you **must** also set the `custom:clubId` attribute to the club's ID. Otherwise, the user will not be able to access admin endpoints. It's recommended to use the Admin Dashboard UI (Option 1) instead, which handles this automatically.

1. **Navigate to Cognito:**
   - Go to AWS Console → Cognito → User Pools
   - Select "ConsistencyTracker-AdminPool"

2. **Create User:**
   - Click "Create user"
   - Enter the user's email address
   - Set a temporary password (must meet password policy)
   - **For club-admins:** Add custom attribute `clubId` with the club's ID value
   - Uncheck "Send an invitation" if you want to share credentials manually
   - Click "Create user"

3. **Add to Appropriate Group:**
   - Select the newly created user
   - Go to "Groups" tab
   - Click "Add user to group"
   - Select the appropriate group:
     - `app-admin` for platform administrators
     - `club-{sanitizedClubName}-admins` for club administrators (e.g., `club-acme_club-admins` for "ACME CLUB")
     - `coach-{clubId}-{teamId}` for team coaches (replace with actual club and team IDs)
   - Click "Add"

### Option 4: Using AWS CLI

**⚠️ Important Note for Club-Admins:** If manually creating a club-admin user via AWS CLI, you **must** also set the `custom:clubId` attribute to the club's ID. Otherwise, the user will not be able to access admin endpoints. It's recommended to use the Admin Dashboard UI (Option 1) instead, which handles this automatically.

```bash
# First, get the User Pool ID
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name ConsistencyTracker-Auth \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

# Create the admin user
# For app-admin:
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username admin@example.com \
  --user-attributes Name=email,Value=admin@example.com \
  --temporary-password "TempPass123!2025" \
  --message-action SUPPRESS \
  --region us-east-1

# For club-admin (include custom:clubId attribute):
# Replace CLUB_ID with the actual club ID from your database
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username clubadmin@example.com \
  --user-attributes \
    Name=email,Value=clubadmin@example.com \
    Name=custom:clubId,Value=CLUB_ID \
  --temporary-password "TempPass123!2025" \
  --message-action SUPPRESS \
  --region us-east-1

# Add to appropriate group (replace with actual group name)
# For app-admin:
aws cognito-idp admin-add-user-to-group \
  --user-pool-id $USER_POOL_ID \
  --username admin@example.com \
  --group-name app-admin \
  --region us-east-1

# For club-admin (replace with actual sanitized club name, e.g., club-acme_club-admins):
# aws cognito-idp admin-add-user-to-group \
#   --user-pool-id $USER_POOL_ID \
#   --username clubadmin@example.com \
#   --group-name club-{sanitizedClubName}-admins \
#   --region us-east-1
```

## First-Time Login Process

When a new admin user logs in for the first time, they must change their temporary password. Here's what happens:

### Step 1: Initial Login

1. Navigate to the login page:
   - All users: `https://repwarrior.net/login` (players and admins use the same login page)

2. Enter credentials:
   - **Email**: The email address used when creating the user
   - **Password**: The temporary password provided

3. Click "Sign in"

### Step 2: Password Change Required

After entering the temporary password, the system will detect that a password change is required and automatically show a "Change Password" form.

### Step 3: Set New Password

1. Enter a new password in the "New Password" field
2. Confirm the password in the "Confirm Password" field
3. Ensure the password meets all requirements (see Password Requirements below)
4. Click "Change Password"

### Step 4: Automatic Login

After successfully changing the password:
- The user is automatically logged in
- They are redirected to their dashboard
- The password change is saved and they can use the new password for future logins

## Password Requirements

All passwords must meet the following requirements:

- **Minimum length**: 12 characters
- **Uppercase letters**: At least one (A-Z)
- **Lowercase letters**: At least one (a-z)
- **Numbers**: At least one (0-9)
- **Special characters**: Not required (but allowed)

### Examples of Valid Passwords

✅ `MySecurePass123`
✅ `Admin2025Secure`
✅ `TrueLacrosse2025!`

❌ `password123` (too short, no uppercase)
❌ `PASSWORD123` (no lowercase)
❌ `MySecurePass` (no numbers)

## User Status in Cognito

When viewing users in the AWS Cognito console, you may see different statuses:

- **FORCE_CHANGE_PASSWORD**: User has a temporary password and must change it on first login
- **CONFIRMED**: User has set their permanent password and can log in normally
- **Enabled**: User account is active and can authenticate

## Troubleshooting

### User Cannot Log In

**Issue**: User gets "username is required to signin" error

**Solution**: 
- Ensure the email address is entered correctly
- Verify the user exists in Cognito User Pool
- Check that email is configured as a sign-in alias (it should be by default)

### Password Change Form Not Appearing

**Issue**: User enters temporary password but doesn't see password change form

**Possible causes**:
1. User already changed password (check status in Cognito console)
2. Temporary password expired (valid for 7 days by default)
3. Browser cache issues (try clearing cache or incognito mode)

**Solution**:
- Check user status in Cognito console
- If status is "CONFIRMED", user should use their permanent password
- If status is still "FORCE_CHANGE_PASSWORD", try resetting the password via AWS Console

### Password Doesn't Meet Requirements

**Issue**: User gets validation error when setting new password

**Solution**:
- Review password requirements listed on the form
- Ensure password has:
  - At least 12 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one number
- Check that both password fields match exactly

### User Not in Correct Admin Group

**Issue**: User can log in but doesn't have expected admin access

**Solution**:
1. Go to AWS Console → Cognito → User Pools → ConsistencyTracker-AdminPool
2. Select the user
3. Go to "Groups" tab
4. Verify user is in the appropriate group:
   - `app-admin` for platform-wide access
   - `club-{sanitizedClubName}-admins` for club-specific access (e.g., `club-acme_club-admins`)
   - `coach-{clubId}-{teamId}` for team-specific access (check club and team IDs)
5. If not in the correct group, click "Add user to group" and select the appropriate group
6. **Note**: Dynamic groups (`club-{sanitizedClubName}-admins` and `coach-{clubId}-{teamId}`) are created automatically when clubs/teams are created
7. **For club-admins**: Verify the `custom:clubId` attribute is set correctly. If missing, the user will get 403 errors when accessing admin endpoints. Use the Admin Dashboard UI to add club-admins, which handles this automatically.

### Temporary Password Expired

**Issue**: User didn't log in within 7 days and temporary password expired

**Solution**:
1. Go to AWS Console → Cognito → User Pools
2. Select the user
3. Click "Reset password" or "Set password"
4. Set a new temporary password
5. Share the new temporary password with the user
6. User must log in and change password within 7 days

### Club-Admin Getting 403 Errors

**Issue**: Club-admin user can log in successfully but gets "403 Forbidden" errors when trying to access admin endpoints (players, overview, reflections, etc.)

**Cause**: The user's `custom:clubId` attribute is not set or is incorrect. This attribute is required for club-admins to access admin endpoints.

**Solution**:
1. **Recommended**: Use the Admin Dashboard UI to add the club-admin (see "Creating New Admin Users" → Option 1). This automatically sets the `custom:clubId` attribute.

2. **If user already exists**, update the attribute:
   - Go to AWS Console → Cognito → User Pools → ConsistencyTracker-AdminPool
   - Select the user
   - Go to "Attributes" tab
   - Find or add `custom:clubId` attribute
   - Set the value to the club's ID (found in the Clubs table in DynamoDB)
   - Save changes
   - User must log out and log back in to get a new JWT token with the updated attribute

3. **Alternative**: Use the `aws/update_user_club_id.py` script (if available) to automatically set the attribute based on the user's group membership.

## Best Practices

1. **Secure Temporary Passwords**: Use strong temporary passwords that meet the password policy
2. **Share Credentials Securely**: Use encrypted email or secure messaging to share temporary passwords
3. **Set Password Expiration Reminders**: Remind users to change their password if they haven't logged in within a few days
4. **Regular Audits**: Periodically review admin users in Cognito to ensure only authorized users have access
5. **Document User Creation**: Keep a record of when users were created and by whom

## Managing Dynamic Groups

### Adding Additional Club-Admins to Existing Clubs

**Recommended Method: Use Admin Dashboard UI**

The easiest and most reliable way to add additional club-admins to an existing club is through the Admin Dashboard:

1. Log in as an app-admin
2. Navigate to "Clubs" in the admin dashboard
3. Click "Edit" on the club you want to add an admin to
4. Scroll to "Additional Club Administrator (optional)" section
5. Enter the new admin's email and temporary password
6. Click "Update Club"

This method:
- Automatically sets the `custom:clubId` attribute (required for access)
- Adds the user to the correct `club-{sanitizedClubName}-admins` group
- Sends an invitation email with login credentials
- Handles user creation or updates existing users

**Manual Method: AWS Console/CLI**

If you must use AWS Console or CLI, remember to:
1. Set the `custom:clubId` attribute to the club's ID
2. Add the user to the `club-{sanitizedClubName}-admins` group
3. The group name must match exactly (sanitized club name)

See "Creating New Admin Users" → Options 3 and 4 for detailed instructions.

### Finding Club and Team IDs

To assign users to dynamic groups manually, you need to know the club and team IDs:

1. **From the Application UI:**
   - Log in as an admin
   - Navigate to Settings
   - Club ID and Team IDs are displayed in the UI

2. **From DynamoDB:**
   ```bash
   # List all clubs
   aws dynamodb scan \
     --table-name ConsistencyTracker-Clubs \
     --region us-east-1 \
     --query 'Items[*].[clubId.S,clubName.S]' \
     --output table
   
   # List teams for a club
   aws dynamodb query \
     --table-name ConsistencyTracker-Teams \
     --index-name ClubIdIndex \
     --key-condition-expression "clubId = :clubId" \
     --expression-attribute-values '{":clubId":{"S":"YOUR_CLUB_ID"}}' \
     --region us-east-1 \
     --query 'Items[*].[teamId.S,teamName.S]' \
     --output table
   ```

3. **From CloudWatch Logs:**
   - Check Lambda function logs for club/team creation events
   - Club and team IDs are logged when created

### Adding Users to Dynamic Groups

Once you have the club/team IDs, add users to the appropriate groups:

```bash
# Get User Pool ID
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name ConsistencyTracker-Auth \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

# Add user to club-admin group
aws cognito-idp admin-add-user-to-group \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com \
  --group-name club-{CLUB_ID}-admins \
  --region us-east-1

# Add user to coach group
aws cognito-idp admin-add-user-to-group \
  --user-pool-id $USER_POOL_ID \
  --username user@example.com \
  --group-name coach-{CLUB_ID}-{TEAM_ID} \
  --region us-east-1
```

**Note**: Replace `{CLUB_ID}` and `{TEAM_ID}` with actual IDs from your database.

## Related Files

- **User Creation Script**: `aws/create_admin_user.py`
- **Auth Stack Configuration**: `aws/stacks/auth_stack.py`
- **Admin App (Group Creation Logic)**: `aws/lambda/admin_app.py`
- **Auth Utilities**: `aws/lambda/shared/auth_utils.py`
- **Flask Auth Decorators**: `aws/lambda/shared/flask_auth.py`
- **Login Components**: 
  - `app/src/pages/AdminLogin.tsx`
  - `app/src/pages/PlayerLogin.tsx`
- **Auth Context**: `app/src/contexts/AuthContext.tsx`

## Support

For issues with user management:
1. Check this manual first
2. Review AWS Cognito console for user status
3. Check CloudWatch logs for authentication errors
4. Verify User Pool configuration in `aws/stacks/auth_stack.py`


