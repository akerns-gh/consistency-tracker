#!/usr/bin/env python3
"""
Deployment script for Consistency Tracker Infrastructure
Deploys AWS CDK stacks for Phase 1 (Database and Auth)
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime

# Configuration
AWS_REGION = "us-east-2"
AWS_ACCOUNT_ID = "707406431671"
STACKS_TO_DEPLOY = [
    "ConsistencyTracker-Database",
    "ConsistencyTracker-Auth",
]

def check_prerequisites():
    """Check if required tools are installed"""
    print("🔍 Checking prerequisites...")
    
    # Check AWS CLI
    try:
        result = subprocess.run(["aws", "--version"], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print("❌ AWS CLI not found. Please install AWS CLI first.")
            sys.exit(1)
        print(f"✅ AWS CLI found: {result.stdout.strip()}")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("❌ AWS CLI not found. Please install AWS CLI first.")
        sys.exit(1)
    
    # Check CDK CLI
    try:
        result = subprocess.run(["cdk", "--version"], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print("❌ AWS CDK not found. Please install with: npm install -g aws-cdk")
            sys.exit(1)
        print(f"✅ AWS CDK found: {result.stdout.strip()}")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("❌ AWS CDK not found. Please install with: npm install -g aws-cdk")
        sys.exit(1)
    
    # Check Python version
    if sys.version_info < (3, 9):
        print(f"❌ Python 3.9+ required. Found: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version.split()[0]}")

def setup_venv():
    """Set up Python virtual environment"""
    aws_dir = Path(__file__).parent
    venv_path = aws_dir / ".venv"
    
    if not venv_path.exists():
        print("\n🐍 Creating Python virtual environment...")
        result = subprocess.run(
            [sys.executable, "-m", "venv", ".venv"],
            cwd=aws_dir,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"❌ Failed to create virtual environment: {result.stderr}")
            sys.exit(1)
        print("✅ Virtual environment created")
    else:
        print("✅ Virtual environment already exists")
    
    return venv_path

def install_dependencies(venv_path):
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    aws_dir = Path(__file__).parent
    
    # Determine pip path based on OS
    if os.name == 'nt':  # Windows
        pip_path = venv_path / "Scripts" / "pip"
        python_path = venv_path / "Scripts" / "python"
    else:  # Unix-like
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"
    
    result = subprocess.run(
        [str(python_path), "-m", "pip", "install", "-r", "requirements.txt"],
        cwd=aws_dir,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Failed to install dependencies: {result.stderr}")
        sys.exit(1)
    print("✅ Dependencies installed")

def run_command(command, cwd=None, timeout=300, check=True):
    """Run a command with error handling"""
    print(f"\n🔄 Running: {command}")
    if cwd:
        print(f"📁 Working directory: {cwd}")
    
    result = subprocess.run(
        command,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout
    )
    
    if result.stdout:
        print(result.stdout)
    
    if result.returncode != 0:
        if result.stderr:
            print(f"❌ Error: {result.stderr}")
        if check:
            return False
        return result
    
    print(f"✅ Command completed successfully")
    return result

def bootstrap_cdk(venv_path):
    """Bootstrap CDK if needed"""
    print("\n🔧 Checking CDK bootstrap status...")
    aws_dir = Path(__file__).parent
    
    # Check if already bootstrapped
    result = subprocess.run(
        f"aws cloudformation describe-stacks --stack-name CDKToolkit --region {AWS_REGION}",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ CDK already bootstrapped")
        return True
    
    print("🔧 Bootstrapping CDK...")
    bootstrap_cmd = f"cdk bootstrap aws://{AWS_ACCOUNT_ID}/{AWS_REGION}"
    
    if not run_command(bootstrap_cmd, cwd=aws_dir, timeout=600, check=False):
        print("⚠️ Bootstrap may have failed, but continuing...")
        print("   You can manually bootstrap with:")
        print(f"   cdk bootstrap aws://{AWS_ACCOUNT_ID}/{AWS_REGION}")
    
    return True

def deploy_stack(stack_name, venv_path):
    """Deploy a single CDK stack"""
    print(f"\n☁️ Deploying stack: {stack_name}")
    aws_dir = Path(__file__).parent
    
    deploy_cmd = f"cdk deploy {stack_name} --require-approval never"
    
    if not run_command(deploy_cmd, cwd=aws_dir, timeout=1800, check=True):
        print(f"❌ Failed to deploy {stack_name}")
        return False
    
    print(f"✅ Successfully deployed {stack_name}")
    return True

def verify_deployment():
    """Verify that stacks were deployed successfully"""
    print("\n📊 Verifying deployment...")
    
    for stack_name in STACKS_TO_DEPLOY:
        result = subprocess.run(
            f"aws cloudformation describe-stacks --stack-name {stack_name} --region {AWS_REGION} --query 'Stacks[0].StackStatus' --output text",
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            status = result.stdout.strip()
            if status == "CREATE_COMPLETE" or status == "UPDATE_COMPLETE":
                print(f"✅ {stack_name}: {status}")
            else:
                print(f"⚠️ {stack_name}: {status}")
        else:
            print(f"❌ Could not verify {stack_name}")

def main():
    print("🚀 Starting Consistency Tracker Infrastructure Deployment")
    print("=" * 60)
    
    start_time = datetime.now()
    
    # Step 1: Check prerequisites
    check_prerequisites()
    
    # Step 2: Set up virtual environment
    venv_path = setup_venv()
    
    # Step 3: Install dependencies
    install_dependencies(venv_path)
    
    # Step 4: Bootstrap CDK
    bootstrap_cdk(venv_path)
    
    # Step 5: Synthesize templates
    print("\n🔨 Synthesizing CDK templates...")
    aws_dir = Path(__file__).parent
    if not run_command("cdk synth", cwd=aws_dir, timeout=300, check=True):
        print("❌ Synthesis failed. Please check for errors above.")
        sys.exit(1)
    
    # Step 6: Deploy stacks
    print("\n☁️ Deploying infrastructure stacks...")
    print(f"📋 Stacks to deploy: {', '.join(STACKS_TO_DEPLOY)}")
    
    success = True
    for stack_name in STACKS_TO_DEPLOY:
        if not deploy_stack(stack_name, venv_path):
            success = False
            break
    
    # Step 7: Verify deployment
    if success:
        verify_deployment()
    
    # Summary
    elapsed = datetime.now() - start_time
    print("\n" + "=" * 60)
    if success:
        print("🎉 Deployment completed successfully!")
        print(f"⏱️ Total time: {elapsed.seconds // 60}m {elapsed.seconds % 60}s")
        print("\n📋 Deployed Stacks:")
        for stack_name in STACKS_TO_DEPLOY:
            print(f"   ✅ {stack_name}")
        print("\n📝 Next Steps:")
        print("   1. Create first admin user in Cognito User Pool")
        print("   2. Verify DynamoDB tables were created")
        print("   3. Check CloudFormation console for stack details")
        print("\n💡 To create admin user:")
        print("   aws cognito-idp admin-create-user \\")
        print("     --user-pool-id <USER_POOL_ID> \\")
        print("     --username admin@example.com \\")
        print("     --user-attributes Name=email,Value=admin@example.com")
        print("\n   Then add to Admins group:")
        print("   aws cognito-idp admin-add-user-to-group \\")
        print("     --user-pool-id <USER_POOL_ID> \\")
        print("     --username admin@example.com \\")
        print("     --group-name Admins")
    else:
        print("❌ Deployment failed!")
        print("📝 Troubleshooting:")
        print("   1. Check CloudFormation console for detailed errors")
        print("   2. Verify AWS credentials and permissions")
        print("   3. Check CDK bootstrap status")
        print("   4. Review error messages above")
        sys.exit(1)

if __name__ == "__main__":
    main()

