"""
Email templates for application emails.
Provides HTML and plain text versions of all email templates.
"""


def get_password_reset_template(reset_link: str, user_name: str = "User") -> dict:
    """Generate password reset email template."""
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reset Your Password</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
            <h1 style="color: #2c3e50; margin-top: 0;">Password Reset Request</h1>
        </div>
        <p>Hello {user_name},</p>
        <p>We received a request to reset your password for your Consistency Tracker account.</p>
        <p>Click the button below to reset your password:</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_link}" style="background-color: #3498db; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">Reset Password</a>
        </div>
        <p>Or copy and paste this link into your browser:</p>
        <p style="word-break: break-all; color: #7f8c8d; font-size: 12px;">{reset_link}</p>
        <p>This link will expire in 24 hours.</p>
        <p>If you didn't request a password reset, please ignore this email.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="color: #7f8c8d; font-size: 12px;">This is an automated message from Consistency Tracker. Please do not reply to this email.</p>
    </body>
    </html>
    """
    
    text_body = f"""
    Password Reset Request
    
    Hello {user_name},
    
    We received a request to reset your password for your Consistency Tracker account.
    
    Click the link below to reset your password:
    {reset_link}
    
    This link will expire in 24 hours.
    
    If you didn't request a password reset, please ignore this email.
    
    ---
    This is an automated message from Consistency Tracker. Please do not reply to this email.
    """
    
    return {
        "html": html_body,
        "text": text_body,
        "subject": "Reset Your Password - Consistency Tracker"
    }


def get_user_invitation_template(
    user_name: str,
    email: str,
    temporary_password: str,
    login_url: str,
    role: str = "administrator"
) -> dict:
    """Generate user invitation email template."""
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to Consistency Tracker</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
            <h1 style="color: #2c3e50; margin-top: 0;">Welcome to Consistency Tracker</h1>
        </div>
        <p>Hello {user_name},</p>
        <p>You have been invited to join Consistency Tracker as a {role}.</p>
        <p>Your account has been created with the following credentials:</p>
        <div style="background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <p style="margin: 5px 0;"><strong>Email:</strong> {email}</p>
            <p style="margin: 5px 0;"><strong>Temporary Password:</strong> {temporary_password}</p>
        </div>
        <p><strong>Important:</strong> You must change your password on first login.</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{login_url}" style="background-color: #27ae60; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">Login Now</a>
        </div>
        <p>After logging in, you'll be prompted to set a new password.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="color: #7f8c8d; font-size: 12px;">This is an automated message from Consistency Tracker. Please do not reply to this email.</p>
    </body>
    </html>
    """
    
    text_body = f"""
    Welcome to Consistency Tracker
    
    Hello {user_name},
    
    You have been invited to join Consistency Tracker as a {role}.
    
    Your account has been created with the following credentials:
    
    Email: {email}
    Temporary Password: {temporary_password}
    
    Important: You must change your password on first login.
    
    Login at: {login_url}
    
    After logging in, you'll be prompted to set a new password.
    
    ---
    This is an automated message from Consistency Tracker. Please do not reply to this email.
    """
    
    return {
        "html": html_body,
        "text": text_body,
        "subject": f"Welcome to Consistency Tracker - {role.title()} Account Created"
    }


def get_club_creation_template(club_name: str, club_id: str, admin_email: str) -> dict:
    """Generate club creation confirmation email template."""
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Club Created - Consistency Tracker</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
            <h1 style="color: #2c3e50; margin-top: 0;">Club Created Successfully</h1>
        </div>
        <p>Hello,</p>
        <p>Your club <strong>{club_name}</strong> has been successfully created in Consistency Tracker.</p>
        <div style="background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <p style="margin: 5px 0;"><strong>Club Name:</strong> {club_name}</p>
            <p style="margin: 5px 0;"><strong>Club ID:</strong> {club_id}</p>
            <p style="margin: 5px 0;"><strong>Admin Email:</strong> {admin_email}</p>
        </div>
        <p>You can now start creating teams and managing your club through the admin dashboard.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="color: #7f8c8d; font-size: 12px;">This is an automated message from Consistency Tracker. Please do not reply to this email.</p>
    </body>
    </html>
    """
    
    text_body = f"""
    Club Created Successfully
    
    Hello,
    
    Your club {club_name} has been successfully created in Consistency Tracker.
    
    Club Name: {club_name}
    Club ID: {club_id}
    Admin Email: {admin_email}
    
    You can now start creating teams and managing your club through the admin dashboard.
    
    ---
    This is an automated message from Consistency Tracker. Please do not reply to this email.
    """
    
    return {
        "html": html_body,
        "text": text_body,
        "subject": f"Club Created: {club_name}"
    }


def get_team_creation_template(team_name: str, club_name: str, team_id: str) -> dict:
    """Generate team creation confirmation email template."""
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Team Created - Consistency Tracker</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
            <h1 style="color: #2c3e50; margin-top: 0;">Team Created Successfully</h1>
        </div>
        <p>Hello,</p>
        <p>Your team <strong>{team_name}</strong> has been successfully created in club <strong>{club_name}</strong>.</p>
        <div style="background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <p style="margin: 5px 0;"><strong>Team Name:</strong> {team_name}</p>
            <p style="margin: 5px 0;"><strong>Club:</strong> {club_name}</p>
            <p style="margin: 5px 0;"><strong>Team ID:</strong> {team_id}</p>
        </div>
        <p>You can now start adding players and managing your team through the admin dashboard.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="color: #7f8c8d; font-size: 12px;">This is an automated message from Consistency Tracker. Please do not reply to this email.</p>
    </body>
    </html>
    """
    
    text_body = f"""
    Team Created Successfully
    
    Hello,
    
    Your team {team_name} has been successfully created in club {club_name}.
    
    Team Name: {team_name}
    Club: {club_name}
    Team ID: {team_id}
    
    You can now start adding players and managing your team through the admin dashboard.
    
    ---
    This is an automated message from Consistency Tracker. Please do not reply to this email.
    """
    
    return {
        "html": html_body,
        "text": text_body,
        "subject": f"Team Created: {team_name}"
    }


def get_player_invitation_template(
    player_name: str,
    email: str,
    temporary_password: str,
    login_url: str,
    team_name: str,
    club_name: str
) -> dict:
    """Generate player invitation email template."""
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to Consistency Tracker</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
            <h1 style="color: #2c3e50; margin-top: 0;">Welcome to Consistency Tracker</h1>
        </div>
        <p>Hello {player_name},</p>
        <p>You have been invited to join <strong>{team_name}</strong> in <strong>{club_name}</strong> on Consistency Tracker.</p>
        <p>Your account has been created with the following credentials:</p>
        <div style="background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <p style="margin: 5px 0;"><strong>Email:</strong> {email}</p>
            <p style="margin: 5px 0;"><strong>Temporary Password:</strong> {temporary_password}</p>
        </div>
        <p><strong>Important:</strong> You must change your password on first login.</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{login_url}" style="background-color: #27ae60; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">Login Now</a>
        </div>
        <p>After logging in, you'll be prompted to set a new password and can start tracking your consistency.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="color: #7f8c8d; font-size: 12px;">This is an automated message from Consistency Tracker. Please do not reply to this email.</p>
    </body>
    </html>
    """
    
    text_body = f"""
    Welcome to Consistency Tracker
    
    Hello {player_name},
    
    You have been invited to join {team_name} in {club_name} on Consistency Tracker.
    
    Your account has been created with the following credentials:
    
    Email: {email}
    Temporary Password: {temporary_password}
    
    Important: You must change your password on first login.
    
    Login at: {login_url}
    
    After logging in, you'll be prompted to set a new password and can start tracking your consistency.
    
    ---
    This is an automated message from Consistency Tracker. Please do not reply to this email.
    """
    
    return {
        "html": html_body,
        "text": text_body,
        "subject": f"Welcome to {team_name} - Consistency Tracker"
    }


def get_coach_invitation_template(
    coach_name: str,
    email: str,
    temporary_password: str,
    login_url: str,
    team_name: str,
    club_name: str
) -> dict:
    """Generate coach invitation email template."""
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to Consistency Tracker</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
            <h1 style="color: #2c3e50; margin-top: 0;">Welcome to Consistency Tracker</h1>
        </div>
        <p>Hello {coach_name},</p>
        <p>You have been invited to join <strong>{team_name}</strong> in <strong>{club_name}</strong> as a coach.</p>
        <p>Your account has been created with the following credentials:</p>
        <div style="background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <p style="margin: 5px 0;"><strong>Email:</strong> {email}</p>
            <p style="margin: 5px 0;"><strong>Temporary Password:</strong> {temporary_password}</p>
        </div>
        <p><strong>Important:</strong> You must change your password on first login.</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{login_url}" style="background-color: #27ae60; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">Login Now</a>
        </div>
        <p>After logging in, you'll be prompted to set a new password and can start managing your team.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="color: #7f8c8d; font-size: 12px;">This is an automated message from Consistency Tracker. Please do not reply to this email.</p>
    </body>
    </html>
    """
    
    text_body = f"""
    Welcome to Consistency Tracker
    
    Hello {coach_name},
    
    You have been invited to join {team_name} in {club_name} as a coach.
    
    Your account has been created with the following credentials:
    
    Email: {email}
    Temporary Password: {temporary_password}
    
    Important: You must change your password on first login.
    
    Login at: {login_url}
    
    After logging in, you'll be prompted to set a new password and can start managing your team.
    
    ---
    This is an automated message from Consistency Tracker. Please do not reply to this email.
    """
    
    return {
        "html": html_body,
        "text": text_body,
        "subject": f"Welcome to {team_name} - Coach Account Created"
    }


def get_email_verification_template(email: str, verification_url: str, user_name: str = "User") -> dict:
    """Generate email verification email template."""
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Verify Your Email - Consistency Tracker</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
            <h1 style="color: #2c3e50; margin-top: 0;">Verify Your Email Address</h1>
        </div>
        <p>Hello {user_name},</p>
        <p>Thank you for joining Consistency Tracker! Please verify your email address to complete your account setup and start using the platform.</p>
        <p>Click the button below to verify your email address:</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{verification_url}" style="background-color: #27ae60; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">Verify Email Address</a>
        </div>
        <p>Or copy and paste this link into your browser:</p>
        <p style="word-break: break-all; color: #7f8c8d; font-size: 12px;">{verification_url}</p>
        <p>This verification link will expire in 1 hour.</p>
        <p>If you didn't create an account with Consistency Tracker, please ignore this email.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="color: #7f8c8d; font-size: 12px;">This is an automated message from Consistency Tracker. Please do not reply to this email.</p>
    </body>
    </html>
    """
    
    text_body = f"""
    Verify Your Email Address - Consistency Tracker
    
    Hello {user_name},
    
    Thank you for joining Consistency Tracker! Please verify your email address to complete your account setup and start using the platform.
    
    Click the link below to verify your email address:
    {verification_url}
    
    This verification link will expire in 1 hour.
    
    If you didn't create an account with Consistency Tracker, please ignore this email.
    
    ---
    This is an automated message from Consistency Tracker. Please do not reply to this email.
    """
    
    return {
        "html": html_body,
        "text": text_body,
        "subject": "Verify Your Email - Consistency Tracker"
    }

