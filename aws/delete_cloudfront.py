#!/usr/bin/env python3
"""
Quick script to delete CloudFront distributions that are blocking certificate deletion
"""

import boto3
import time
from botocore.exceptions import ClientError

# The two distributions blocking certificate deletion
DISTRIBUTION_IDS = [
    "E11CYNQ91MDSZR",
    "E1986A93DSMC7O"
]

def delete_distribution(dist_id):
    """Delete a CloudFront distribution"""
    cloudfront = boto3.client("cloudfront", region_name="us-east-1")
    
    print(f"\n🗑️  Processing distribution {dist_id}...")
    
    try:
        # Get current distribution status
        dist_response = cloudfront.get_distribution(Id=dist_id)
        dist_info = dist_response['Distribution']
        status = dist_info['Status']
        dist_config = dist_info['DistributionConfig']
        enabled = dist_config.get('Enabled', False)
        
        print(f"   Current status: Enabled={enabled}, Status={status}")
        
        # If enabled, disable it first
        if enabled:
            print(f"   Distribution is enabled. Disabling...")
            config_response = cloudfront.get_distribution_config(Id=dist_id)
            etag = config_response['ETag']
            dist_config = config_response['DistributionConfig']
            dist_config['Enabled'] = False
            
            update_response = cloudfront.update_distribution(
                Id=dist_id,
                DistributionConfig=dist_config,
                IfMatch=etag
            )
            print(f"   ✅ Disable request submitted")
            print(f"   ⏳ Waiting for distribution to be fully disabled (this takes 10-15 minutes)...")
            print(f"   ⏳ You can monitor progress in the CloudFront console")
            
            # Wait for deployment to complete
            waiter = cloudfront.get_waiter('distribution_deployed')
            try:
                waiter.wait(Id=dist_id, WaiterConfig={'Delay': 30, 'MaxAttempts': 60})
                print(f"   ✅ Distribution deployment completed")
            except Exception as e:
                print(f"   ⚠️  Waiter timed out: {e}")
                print(f"   ⚠️  This is normal - CloudFront can take 15-30 minutes")
        
        # Check if distribution is ready for deletion (disabled AND deployed)
        dist_response = cloudfront.get_distribution(Id=dist_id)
        dist_info = dist_response['Distribution']
        status = dist_info['Status']
        dist_config = dist_info['DistributionConfig']
        enabled = dist_config.get('Enabled', False)
        
        if enabled:
            print(f"   ⚠️  Distribution is still enabled")
            print(f"   ⚠️  Please wait and run this script again")
            return False
        
        if status != "Deployed":
            print(f"   ⚠️  Distribution status is '{status}' (needs to be 'Deployed')")
            print(f"   ⚠️  CloudFront disable deployment can take 15-30 minutes")
            print(f"   ⚠️  Please wait and run this script again in 15-30 minutes")
            print(f"   ⚠️  Or check status in CloudFront console")
            return False
        
        # Distribution is disabled and deployed - safe to delete
        print(f"   ✅ Distribution is disabled and deployed - ready to delete")
        config_response = cloudfront.get_distribution_config(Id=dist_id)
        etag = config_response['ETag']
        
        print(f"   Deleting distribution...")
        cloudfront.delete_distribution(Id=dist_id, IfMatch=etag)
        print(f"   ✅ Distribution {dist_id} deletion initiated")
        print(f"   ℹ️  Deletion will complete in 15-30 minutes")
        return True
        
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == "NoSuchDistribution":
            print(f"   ✅ Distribution {dist_id} already deleted")
            return True
        else:
            print(f"   ❌ Error: {e}")
            return False

def main():
    import sys
    
    print("=" * 60)
    print("🗑️  CloudFront Distribution Deletion")
    print("=" * 60)
    print(f"\nThis will delete {len(DISTRIBUTION_IDS)} CloudFront distribution(s):")
    for dist_id in DISTRIBUTION_IDS:
        print(f"   - {dist_id}")
    
    # Skip confirmation if --yes flag is provided
    skip_confirmation = "--yes" in sys.argv or "-y" in sys.argv
    
    if not skip_confirmation:
        response = input("\n❓ Continue? (yes/no): ")
        if response.lower() != "yes":
            print("❌ Cancelled.")
            return
    else:
        print("\n✅ Auto-confirming (--yes flag provided)")
    
    success = True
    for dist_id in DISTRIBUTION_IDS:
        if not delete_distribution(dist_id):
            success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Deletion process initiated for all distributions")
        print("⏳ Wait 15-30 minutes for deletions to complete")
        print("📝 Then you can delete the certificate and DNS stack")
    else:
        print("⚠️  Some distributions failed to delete")
        print("📝 Check the CloudFront console for status")

if __name__ == "__main__":
    main()

