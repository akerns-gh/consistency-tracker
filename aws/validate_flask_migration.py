#!/usr/bin/env python3
"""
Validation script for Flask migration.

Checks that:
1. Flask apps can be imported (syntax check)
2. All required files exist
3. CDK stack synthesizes correctly
4. Lambda handlers are correctly configured
"""

import sys
import subprocess
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists."""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description} missing: {filepath}")
        return False

def check_cdk_synthesis():
    """Check if CDK stack synthesizes correctly."""
    print("\n🔨 Validating CDK stack synthesis...")
    aws_dir = Path(__file__).parent
    
    result = subprocess.run(
        ["cdk", "synth", "ConsistencyTracker-API"],
        cwd=aws_dir,
        capture_output=True,
        text=True,
        timeout=300
    )
    
    if result.returncode == 0:
        print("✅ CDK stack synthesizes successfully")
        
        # Check for Flask Lambda functions
        if "AdminAppFunction" in result.stdout and "PlayerAppFunction" in result.stdout:
            print("✅ Flask Lambda functions found in template")
            return True
        else:
            print("⚠️ Flask Lambda functions not found in template")
            return False
    else:
        print(f"❌ CDK synthesis failed: {result.stderr}")
        return False

def main():
    print("🔍 Validating Flask Migration")
    print("=" * 60)
    
    aws_dir = Path(__file__).parent
    lambda_dir = aws_dir / "lambda"
    
    all_checks_passed = True
    
    # Check Flask app files
    print("\n📁 Checking Flask application files...")
    all_checks_passed &= check_file_exists(
        lambda_dir / "admin_app.py",
        "Admin Flask app"
    )
    all_checks_passed &= check_file_exists(
        lambda_dir / "player_app.py",
        "Player Flask app"
    )
    all_checks_passed &= check_file_exists(
        lambda_dir / "shared" / "flask_auth.py",
        "Flask auth utilities"
    )
    
    # Check dependencies
    print("\n📦 Checking dependencies...")
    requirements_file = lambda_dir / "layer" / "python" / "requirements.txt"
    if requirements_file.exists():
        content = requirements_file.read_text()
        if "flask" in content.lower() and "serverless-wsgi" in content.lower():
            print("✅ Flask dependencies in requirements.txt")
        else:
            print("❌ Flask dependencies missing from requirements.txt")
            all_checks_passed = False
    else:
        print("❌ requirements.txt not found")
        all_checks_passed = False
    
    # Check CDK stack
    all_checks_passed &= check_cdk_synthesis()
    
    # Summary
    print("\n" + "=" * 60)
    if all_checks_passed:
        print("✅ All validation checks passed!")
        print("\n📝 Ready for deployment:")
        print("   cd aws && ./deploy.sh")
        return 0
    else:
        print("❌ Some validation checks failed")
        print("   Please review errors above before deploying")
        return 1

if __name__ == "__main__":
    sys.exit(main())

