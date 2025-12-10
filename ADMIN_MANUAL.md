# Admin User Management Manual

This document describes the process for creating and managing admin users in the Consistency Tracker application.

## Overview

Admin users are authenticated through AWS Cognito User Pool. When a new admin user is created, they receive a temporary password and must change it on their first login. This manual covers:

1. Creating new admin users
2. First-time login process
3. Password requirements
4. Troubleshooting

## Creating New Admin Users

### Option 1: Using Python Script (Recommended)

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
   - Add the user to the "Admins" group
   - Handle errors gracefully (e.g., user already exists)

4. **Share credentials with the new admin:**
   - Email: The email address you configured
   - Temporary Password: The temporary password you set
   - Login URL: `https://repwarrior.net/login` (for players) or `https://repwarrior.net/admin/login` (for admins)

### Option 2: Using AWS Console

1. **Navigate to Cognito:**
   - Go to AWS Console → Cognito → User Pools
   - Select "ConsistencyTracker-AdminPool"

2. **Create User:**
   - Click "Create user"
   - Enter the user's email address
   - Set a temporary password (must meet password policy)
   - Uncheck "Send an invitation" if you want to share credentials manually
   - Click "Create user"

3. **Add to Admins Group:**
   - Select the newly created user
   - Go to "Groups" tab
   - Click "Add user to group"
   - Select "Admins" group
   - Click "Add"

### Option 3: Using AWS CLI

```bash
# First, get the User Pool ID
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name ConsistencyTracker-Auth \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

# Create the admin user
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username admin@example.com \
  --user-attributes Name=email,Value=admin@example.com \
  --temporary-password "TempPass123!2025" \
  --message-action SUPPRESS \
  --region us-east-1

# Add to Admins group
aws cognito-idp admin-add-user-to-group \
  --user-pool-id $USER_POOL_ID \
  --username admin@example.com \
  --group-name Admins \
  --region us-east-1
```

## First-Time Login Process

When a new admin user logs in for the first time, they must change their temporary password. Here's what happens:

### Step 1: Initial Login

1. Navigate to the login page:
   - Admin login: `https://repwarrior.net/admin/login`
   - Player login: `https://repwarrior.net/login`

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

### User Not in Admins Group

**Issue**: User can log in but doesn't have admin access

**Solution**:
1. Go to AWS Console → Cognito → User Pools → ConsistencyTracker-AdminPool
2. Select the user
3. Go to "Groups" tab
4. Verify user is in "Admins" group
5. If not, click "Add user to group" and select "Admins"

### Temporary Password Expired

**Issue**: User didn't log in within 7 days and temporary password expired

**Solution**:
1. Go to AWS Console → Cognito → User Pools
2. Select the user
3. Click "Reset password" or "Set password"
4. Set a new temporary password
5. Share the new temporary password with the user
6. User must log in and change password within 7 days

## Best Practices

1. **Secure Temporary Passwords**: Use strong temporary passwords that meet the password policy
2. **Share Credentials Securely**: Use encrypted email or secure messaging to share temporary passwords
3. **Set Password Expiration Reminders**: Remind users to change their password if they haven't logged in within a few days
4. **Regular Audits**: Periodically review admin users in Cognito to ensure only authorized users have access
5. **Document User Creation**: Keep a record of when users were created and by whom

## Related Files

- **User Creation Script**: `aws/create_admin_user.py`
- **Auth Stack Configuration**: `aws/stacks/auth_stack.py`
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


