#!/usr/bin/env python3
"""
Destroy script for Consistency Tracker Infrastructure

Destroys all AWS CDK stacks and optionally deletes retained resources.

⚠️  WARNING: This will delete all infrastructure resources!
   - DynamoDB tables and S3 buckets have RETAIN policy and will remain after stack deletion
   - Use --delete-retained flag to also delete these resources
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime
import json

# Configuration
AWS_REGION = "us-east-1"
AWS_ACCOUNT_ID = "707406431671"

# Stacks are destroyed in dependency order (opposite of deployment):
# 1. API (uses certificate from DNS, must be destroyed first)
# 2. DNS (uses Storage exports and has certificate)
# 3. Storage (S3 buckets + CloudFront distributions)
# 4. Auth (Cognito User Pool)
# 5. Database (DynamoDB tables - will be retained)
STACKS_TO_DESTROY = [
    "ConsistencyTracker-API",
    "ConsistencyTracker-DNS",
    "ConsistencyTracker-Storage",
    "ConsistencyTracker-Auth",
    "ConsistencyTracker-Database",
]

# Resources with RETAIN policy that will remain after stack deletion
RETAINED_DYNAMODB_TABLES = [
    "ConsistencyTracker-Clubs",
    "ConsistencyTracker-Players",
    "ConsistencyTracker-Teams",
    "ConsistencyTracker-Activities",
    "ConsistencyTracker-Tracking",
    "ConsistencyTracker-Reflections",
    "ConsistencyTracker-ContentPages",
]

RETAINED_S3_BUCKETS = [
    "consistency-tracker-frontend-us-east-1",
    "consistency-tracker-content-images-us-east-1",
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
    """Install Python dependencies and add venv to sys.path"""
    print("\n📦 Installing Python dependencies...")
    aws_dir = Path(__file__).parent
    
    # Determine pip path based on OS
    if os.name == 'nt':  # Windows
        pip_path = venv_path / "Scripts" / "pip"
        python_path = venv_path / "Scripts" / "python"
        site_packages = venv_path / "Lib" / "site-packages"
    else:  # Unix-like
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"
        # Find site-packages directory (varies by Python version)
        import sysconfig
        site_packages = Path(sysconfig.get_path("purelib", vars={"base": str(venv_path)}))
    
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
    
    # Add venv site-packages to sys.path so we can import boto3
    if str(site_packages) not in sys.path:
        sys.path.insert(0, str(site_packages))
    
    return site_packages

def run_command(command, cwd=None, timeout=300, check=True, env=None):
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
        timeout=timeout,
        env=env
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

def check_stacks_exist():
    """Check which stacks exist"""
    print("\n🔍 Checking which stacks exist...")
    existing_stacks = []
    
    for stack_name in STACKS_TO_DESTROY:
        result = subprocess.run(
            f"aws cloudformation describe-stacks --stack-name {stack_name} --region {AWS_REGION}",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            existing_stacks.append(stack_name)
            print(f"✅ Found: {stack_name}")
        else:
            print(f"⚠️  Not found: {stack_name}")
    
    return existing_stacks

def destroy_stack(stack_name, venv_path, exclusively=False):
    """Destroy a single CDK stack"""
    print(f"\n🗑️  Destroying stack: {stack_name}")
    if exclusively:
        print("   (destroying exclusively, without dependencies)")
    aws_dir = Path(__file__).parent
    
    # Set up environment to use venv's Python
    env = os.environ.copy()
    if os.name == 'nt':  # Windows
        venv_bin = venv_path / "Scripts"
        site_packages = venv_path / "Lib" / "site-packages"
    else:  # Unix-like
        venv_bin = venv_path / "bin"
        import sysconfig
        site_packages = Path(sysconfig.get_path("purelib", vars={"base": str(venv_path)}))
    
    # Add venv's bin to PATH (so it finds python first)
    env["PATH"] = f"{venv_bin}:{env.get('PATH', '')}"
    
    # Set PYTHONPATH to use venv's site-packages
    pythonpath = str(site_packages)
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{pythonpath}:{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = pythonpath
    
    # Use cdk command (it will use venv's python from PATH)
    destroy_cmd = f"cdk destroy {stack_name} --force"
    if exclusively:
        destroy_cmd += " --exclusively"
    
    if not run_command(destroy_cmd, cwd=aws_dir, timeout=1800, check=True, env=env):
        print(f"❌ Failed to destroy {stack_name}")
        return False
    
    print(f"✅ Successfully destroyed {stack_name}")
    return True

def delete_dynamodb_tables():
    """Delete all DynamoDB tables"""
    import boto3
    from botocore.exceptions import ClientError
    
    print("\n🗑️  Deleting DynamoDB tables...")
    dynamodb = boto3.client("dynamodb", region_name=AWS_REGION)
    
    for table_name in RETAINED_DYNAMODB_TABLES:
        try:
            print(f"   Deleting table: {table_name}")
            dynamodb.delete_table(TableName=table_name)
            print(f"   ✅ Deletion initiated for {table_name}")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ResourceNotFoundException":
                print(f"   ⚠️  Table {table_name} does not exist")
            else:
                print(f"   ❌ Error deleting {table_name}: {e}")
                return False
    
    # Wait for tables to be deleted
    print("\n⏳ Waiting for tables to be deleted...")
    for table_name in RETAINED_DYNAMODB_TABLES:
        try:
            waiter = dynamodb.get_waiter("table_not_exists")
            waiter.wait(TableName=table_name, WaiterConfig={"Delay": 5, "MaxAttempts": 60})
            print(f"   ✅ Table {table_name} deleted")
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") != "ResourceNotFoundException":
                print(f"   ⚠️  Error waiting for {table_name}: {e}")
    
    return True

def delete_cloudfront_distributions():
    """Delete CloudFront distributions that use the certificate"""
    import boto3
    from botocore.exceptions import ClientError
    import time
    
    print("\n🗑️  Deleting CloudFront distributions using the certificate...")
    cloudfront = boto3.client("cloudfront", region_name=AWS_REGION)
    certificate_arn = "arn:aws:acm:us-east-1:707406431671:certificate/98d1bf1b-dfd3-45bb-82aa-176aedd2babe"
    
    try:
        # List all distributions
        paginator = cloudfront.get_paginator('list_distributions')
        distributions = []
        
        for page in paginator.paginate():
            distributions.extend(page.get('DistributionList', {}).get('Items', []))
        
        if not distributions:
            print("   ✅ No CloudFront distributions found")
            return True
        
        print(f"   Found {len(distributions)} CloudFront distribution(s)")
        
        # Find distributions using the certificate
        distributions_to_delete = []
        for dist in distributions:
            dist_id = dist['Id']
            domain_name = dist.get('DomainName', '')
            
            # Get full distribution config
            try:
                config = cloudfront.get_distribution_config(Id=dist_id)
                etag = config['ETag']
                dist_config = config['DistributionConfig']
                viewer_cert = dist_config.get('ViewerCertificate', {})
                
                # Check if this distribution uses our certificate
                if viewer_cert.get('ACMCertificateArn') == certificate_arn:
                    distributions_to_delete.append((dist_id, etag, dist_config, domain_name))
                    print(f"      Found distribution {dist_id} ({domain_name}) using certificate")
            except ClientError as e:
                print(f"      ⚠️  Error checking distribution {dist_id}: {e}")
        
        if not distributions_to_delete:
            print("   ✅ No distributions are using the certificate")
            return True
        
        print(f"   🗑️  Deleting {len(distributions_to_delete)} distribution(s)...")
        
        # Delete each distribution
        for dist_id, etag, dist_config, domain_name in distributions_to_delete:
            print(f"\n      Processing distribution {dist_id} ({domain_name})...")
            try:
                # Disable the distribution first (required before deletion)
                if dist_config.get('Enabled', False):
                    print(f"         Disabling distribution...")
                    dist_config['Enabled'] = False
                    update_response = cloudfront.update_distribution(
                        Id=dist_id,
                        DistributionConfig=dist_config,
                        IfMatch=etag
                    )
                    new_etag = update_response['ETag']
                    print(f"         ✅ Distribution disabled")
                    
                    # Wait for distribution to be disabled (this can take a while)
                    print(f"         ⏳ Waiting for distribution to be disabled (this may take 10-15 minutes)...")
                    print(f"         ⏳ You can check progress in the CloudFront console")
                    
                    # Use waiter with longer timeout
                    waiter = cloudfront.get_waiter('distribution_deployed')
                    try:
                        waiter.wait(
                            Id=dist_id,
                            WaiterConfig={'Delay': 30, 'MaxAttempts': 60}  # Up to 30 minutes
                        )
                        print(f"         ✅ Distribution is disabled")
                    except Exception as e:
                        print(f"         ⚠️  Waiter timed out or failed: {e}")
                        print(f"         ⚠️  Continuing anyway - distribution may still be disabling")
                    
                    # Get updated config and etag for deletion
                    config = cloudfront.get_distribution_config(Id=dist_id)
                    etag = config['ETag']
                    dist_config = config['DistributionConfig']
                
                # Verify it's disabled before deleting
                if dist_config.get('Enabled', False):
                    print(f"         ⚠️  Distribution is still enabled, waiting a bit more...")
                    time.sleep(30)
                    config = cloudfront.get_distribution_config(Id=dist_id)
                    etag = config['ETag']
                    dist_config = config['DistributionConfig']
                
                if dist_config.get('Enabled', False):
                    print(f"         ❌ Distribution is still enabled. Please disable it manually in the console.")
                    print(f"         ❌ Then delete it manually, or wait for the Storage stack to delete it.")
                    continue
                
                # Delete the distribution
                print(f"         Deleting distribution...")
                cloudfront.delete_distribution(Id=dist_id, IfMatch=etag)
                print(f"         ✅ Distribution {dist_id} deletion initiated")
                print(f"         ℹ️  CloudFront deletions can take 15-30 minutes to complete")
                
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                if error_code == "NoSuchDistribution":
                    print(f"         ⚠️  Distribution {dist_id} already deleted")
                elif error_code == "InvalidIfMatchVersion":
                    print(f"         ⚠️  Distribution config changed, retrying...")
                    # Retry with fresh config
                    try:
                        config = cloudfront.get_distribution_config(Id=dist_id)
                        etag = config['ETag']
                        if not config['DistributionConfig'].get('Enabled', False):
                            cloudfront.delete_distribution(Id=dist_id, IfMatch=etag)
                            print(f"         ✅ Distribution {dist_id} deletion initiated")
                    except Exception as retry_e:
                        print(f"         ❌ Retry failed: {retry_e}")
                else:
                    print(f"         ❌ Error deleting distribution {dist_id}: {e}")
                    print(f"         ⚠️  You may need to delete it manually from the AWS Console")
        
        if distributions_to_delete:
            print(f"\n   ⏳ CloudFront distributions are being deleted...")
            print(f"   ℹ️  This process can take 15-30 minutes")
            print(f"   ℹ️  You can monitor progress in the CloudFront console")
            print(f"   ℹ️  Once deleted, you can retry DNS stack deletion")
        
        return True
        
    except ClientError as e:
        print(f"   ❌ Error deleting CloudFront distributions: {e}")
        return False

def cleanup_api_gateway_custom_domain():
    """Delete API Gateway custom domain and base path mappings"""
    import boto3
    from botocore.exceptions import ClientError
    
    print("\n🗑️  Cleaning up API Gateway custom domain...")
    apigw = boto3.client("apigateway", region_name=AWS_REGION)
    
    domain_name = "api.repwarrior.net"
    
    try:
        # Get the custom domain
        try:
            domain = apigw.get_domain_name(domainName=domain_name)
            print(f"   Found custom domain: {domain_name}")
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "NotFoundException":
                print(f"   ⚠️  Custom domain {domain_name} does not exist")
                return True
            raise
        
        # Get base path mappings
        try:
            mappings = apigw.get_base_path_mappings(domainName=domain_name)
            print(f"   Found {len(mappings.get('items', []))} base path mapping(s)")
            
            # Delete all base path mappings
            for mapping in mappings.get('items', []):
                base_path = mapping.get('basePath', '')
                base_path_display = base_path if base_path else '(root)'
                print(f"      Deleting base path mapping: {base_path_display}")
                try:
                    # API Gateway requires basePath parameter, use empty string for root
                    apigw.delete_base_path_mapping(
                        domainName=domain_name,
                        basePath=base_path if base_path else ''
                    )
                    print(f"      ✅ Deleted base path mapping: {base_path_display}")
                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "")
                    if error_code == "NotFoundException":
                        print(f"      ⚠️  Base path mapping already deleted")
                    else:
                        print(f"      ⚠️  Error deleting base path mapping: {e}")
                        # Continue anyway - might already be deleted
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") != "NotFoundException":
                print(f"   ⚠️  Error getting base path mappings: {e}")
        
        # Wait a moment for mappings to be fully deleted
        import time
        time.sleep(2)
        
        # Delete the custom domain
        print(f"   Deleting custom domain: {domain_name}")
        try:
            apigw.delete_domain_name(domainName=domain_name)
            print(f"   ✅ Custom domain {domain_name} deleted")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NotFoundException":
                print(f"   ⚠️  Custom domain {domain_name} does not exist")
            else:
                print(f"   ❌ Error deleting custom domain: {e}")
                return False
        
        return True
        
    except ClientError as e:
        print(f"   ❌ Error cleaning up API Gateway custom domain: {e}")
        return False

def delete_s3_buckets():
    """Delete all S3 buckets and their contents"""
    import boto3
    from botocore.exceptions import ClientError
    
    print("\n🗑️  Deleting S3 buckets...")
    s3 = boto3.client("s3", region_name=AWS_REGION)
    s3_resource = boto3.resource("s3", region_name=AWS_REGION)
    
    for bucket_name in RETAINED_S3_BUCKETS:
        try:
            bucket = s3_resource.Bucket(bucket_name)
            
            # Check if bucket exists
            try:
                s3.head_bucket(Bucket=bucket_name)
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                if error_code == "404":
                    print(f"   ⚠️  Bucket {bucket_name} does not exist")
                    continue
                else:
                    raise
            
            print(f"   Deleting bucket: {bucket_name}")
            
            # Delete all object versions (for versioned buckets)
            print(f"      Deleting all object versions...")
            bucket.object_versions.delete()
            
            # Delete all objects
            print(f"      Deleting all objects...")
            bucket.objects.all().delete()
            
            # Delete the bucket
            bucket.delete()
            print(f"   ✅ Bucket {bucket_name} deleted")
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchBucket":
                print(f"   ⚠️  Bucket {bucket_name} does not exist")
            else:
                print(f"   ❌ Error deleting {bucket_name}: {e}")
                return False
    
    return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Destroy all Consistency Tracker AWS infrastructure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
⚠️  WARNING: This will delete all infrastructure resources!

Resources with RETAIN policy (DynamoDB tables and S3 buckets) will remain
after stack deletion unless --delete-retained flag is used.

Examples:
  # Destroy stacks only (retained resources will remain)
  python destroy.py

  # Destroy stacks and delete retained resources
  python destroy.py --delete-retained
        """
    )
    parser.add_argument(
        "--delete-retained",
        action="store_true",
        help="Also delete DynamoDB tables and S3 buckets (they have RETAIN policy)"
    )
    parser.add_argument(
        "--skip-confirmation",
        action="store_true",
        help="Skip confirmation prompt (use with caution!)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🗑️  Consistency Tracker Infrastructure Destruction")
    print("=" * 60)
    
    if not args.skip_confirmation:
        print("\n⚠️  WARNING: This will DELETE all AWS infrastructure!")
        print("\nStacks to be destroyed:")
        for stack in STACKS_TO_DESTROY:
            print(f"   - {stack}")
        
        if args.delete_retained:
            print("\n⚠️  RETAINED RESOURCES will also be deleted:")
            print("   DynamoDB Tables:")
            for table in RETAINED_DYNAMODB_TABLES:
                print(f"      - {table}")
            print("   S3 Buckets:")
            for bucket in RETAINED_S3_BUCKETS:
                print(f"      - {bucket}")
        else:
            print("\n⚠️  RETAINED RESOURCES will remain (use --delete-retained to delete):")
            print("   DynamoDB Tables:")
            for table in RETAINED_DYNAMODB_TABLES:
                print(f"      - {table}")
            print("   S3 Buckets:")
            for bucket in RETAINED_S3_BUCKETS:
                print(f"      - {bucket}")
        
        response = input("\n❓ Are you sure you want to continue? (type 'yes' to confirm): ")
        if response.lower() != "yes":
            print("❌ Destruction cancelled.")
            sys.exit(0)
    
    start_time = datetime.now()
    
    # Step 1: Check prerequisites
    check_prerequisites()
    
    # Step 2: Set up virtual environment
    venv_path = setup_venv()
    
    # Step 3: Install dependencies
    install_dependencies(venv_path)
    
    # Step 4: Check which stacks exist
    existing_stacks = check_stacks_exist()
    
    if not existing_stacks:
        print("\n⚠️  No stacks found to destroy.")
        sys.exit(0)
    
    # Step 5: Clean up resources using the certificate
    print("\n🔧 Cleaning up resources using the certificate...")
    
    # Clean up API Gateway custom domain
    if not cleanup_api_gateway_custom_domain():
        print("⚠️  Failed to clean up API Gateway custom domain, but continuing...")
    
    # Delete CloudFront distributions that use the certificate
    # This is necessary before DNS stack can be deleted
    if not delete_cloudfront_distributions():
        print("⚠️  Failed to delete CloudFront distributions, but continuing...")
        print("⚠️  You may need to delete them manually from the AWS Console")
    
    # Step 6: Destroy stacks in dependency order
    print("\n🗑️  Destroying infrastructure stacks...")
    print(f"📋 Stacks to destroy: {', '.join(existing_stacks)}")
    
    success = True
    
    # Destroy API stack exclusively first (to release certificate)
    if "ConsistencyTracker-API" in existing_stacks:
        if not destroy_stack("ConsistencyTracker-API", venv_path, exclusively=True):
            success = False
            print(f"⚠️  Failed to destroy ConsistencyTracker-API, but continuing...")
        # Remove from list so we don't try again
        existing_stacks = [s for s in existing_stacks if s != "ConsistencyTracker-API"]
    
    # Destroy remaining stacks
    # Note: DNS stack may fail if certificate is still in use by CloudFront
    # Storage stack will delete CloudFront, but DNS dependencies may block it
    for stack_name in existing_stacks:
        if not destroy_stack(stack_name, venv_path):
            success = False
            print(f"⚠️  Failed to destroy {stack_name}, but continuing...")
            
            # If DNS failed due to certificate, provide helpful message
            if stack_name == "ConsistencyTracker-DNS":
                print(f"\n💡 Tip: If DNS stack failed due to certificate in use:")
                print(f"   1. Wait for CloudFront distributions to be deleted (can take 15-30 minutes)")
                print(f"   2. Or manually delete the DNS stack from AWS Console")
                print(f"   3. The certificate will be deleted when DNS stack is removed")
    
    # Step 7: Delete retained resources if requested
    if args.delete_retained and success:
        print("\n🗑️  Deleting retained resources...")
        
        # Delete S3 buckets first (they might be referenced by other resources)
        if not delete_s3_buckets():
            print("⚠️  Some S3 buckets failed to delete")
        
        # Delete DynamoDB tables
        if not delete_dynamodb_tables():
            print("⚠️  Some DynamoDB tables failed to delete")
    
    # Summary
    elapsed = datetime.now() - start_time
    print("\n" + "=" * 60)
    if success:
        print("🎉 Destruction completed!")
        print(f"⏱️ Total time: {elapsed.seconds // 60}m {elapsed.seconds % 60}s")
        
        if args.delete_retained:
            print("\n✅ All resources have been deleted, including retained resources.")
        else:
            print("\n⚠️  Stacks have been destroyed, but retained resources remain:")
            print("   - DynamoDB tables (use AWS Console or CLI to delete manually)")
            print("   - S3 buckets (use AWS Console or CLI to delete manually)")
            print("\n   To delete retained resources, run:")
            print("   python destroy.py --delete-retained")
    else:
        print("❌ Destruction completed with errors!")
        print("📝 Check CloudFormation console for details")
        sys.exit(1)

if __name__ == "__main__":
    main()

