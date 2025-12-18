#!/usr/bin/env python3
"""
Script to delete old API Gateway routes before deploying Flask proxy routes.

This removes the old specific path parameter routes that conflict with {proxy+} routes.
"""

import boto3
import sys
from botocore.exceptions import ClientError

# Get API Gateway ID
apigw = boto3.client("apigateway", region_name="us-east-1")

# Find the API
try:
    apis = apigw.get_rest_apis()
    api_id = None
    for api in apis["items"]:
        if api["name"] == "Consistency Tracker API":
            api_id = api["id"]
            break
    
    if not api_id:
        print("❌ API 'Consistency Tracker API' not found")
        sys.exit(1)
    
    print(f"✅ Found API: {api_id}")
except Exception as e:
    print(f"❌ Error finding API: {e}")
    sys.exit(1)

# Get all resources
try:
    resources = apigw.get_resources(restApiId=api_id)
except Exception as e:
    print(f"❌ Error getting resources: {e}")
    sys.exit(1)

# Routes to delete (these conflict with {proxy+} routes)
routes_to_delete = [
    "/content/{slug}",
    "/leaderboard/{weekId}",
    "/player/{uniqueLink}",
    "/player/{uniqueLink}/week",
    "/player/{uniqueLink}/week/{weekId}",
    "/player/{uniqueLink}/progress",
    "/player/{uniqueLink}/checkin",
    "/player/{uniqueLink}/reflection",
]

# Build resource map
resource_map = {r["path"]: r["id"] for r in resources["items"]}

# Delete routes
deleted = []
failed = []

for route_path in routes_to_delete:
    if route_path in resource_map:
        resource_id = resource_map[route_path]
        try:
            # Get methods first
            methods = apigw.get_resource(restApiId=api_id, resourceId=resource_id)
            
            # Delete all methods
            if "resourceMethods" in methods:
                for method in methods["resourceMethods"].keys():
                    try:
                        apigw.delete_method(
                            restApiId=api_id,
                            resourceId=resource_id,
                            httpMethod=method
                        )
                        print(f"  ✅ Deleted method {method} from {route_path}")
                    except ClientError as e:
                        if e.response["Error"]["Code"] != "NotFoundException":
                            print(f"  ⚠️  Error deleting method {method}: {e}")
            
            # Delete the resource
            apigw.delete_resource(restApiId=api_id, resourceId=resource_id)
            print(f"✅ Deleted resource: {route_path}")
            deleted.append(route_path)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NotFoundException":
                print(f"⚠️  Resource already deleted: {route_path}")
            else:
                print(f"❌ Error deleting {route_path}: {e}")
                failed.append(route_path)
    else:
        print(f"⚠️  Resource not found: {route_path}")

# Summary
print("\n" + "=" * 60)
print("Cleanup Summary:")
print(f"  ✅ Deleted: {len(deleted)}")
print(f"  ❌ Failed: {len(failed)}")
if deleted:
    print("\nDeleted routes:")
    for route in deleted:
        print(f"  - {route}")

if failed:
    print("\nFailed routes:")
    for route in failed:
        print(f"  - {route}")
    sys.exit(1)

print("\n✅ Cleanup complete! You can now deploy the Flask proxy routes.")
sys.exit(0)

