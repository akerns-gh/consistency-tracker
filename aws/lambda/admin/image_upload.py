"""
Lambda function: POST /admin/content/image-upload-url
Generate pre-signed S3 URL for image upload.
"""

import json
import os
import boto3
from datetime import timedelta
from shared.response import success_response, error_response, cors_preflight_response
from shared.auth_utils import require_admin

# S3 bucket name (will be set via environment variable)
CONTENT_IMAGES_BUCKET = os.environ.get("CONTENT_IMAGES_BUCKET", "consistency-tracker-content-images")

# Initialize S3 client
s3_client = boto3.client("s3")


def lambda_handler(event, context):
    """Handle POST /admin/content/image-upload-url request."""
    
    # Handle CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return cors_preflight_response()
    
    try:
        # Require admin authentication
        require_admin(event)
        
        # Parse request body
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            return error_response("Invalid JSON in request body", status_code=400)
        
        file_name = body.get("fileName")
        content_type = body.get("contentType", "image/jpeg")
        
        if not file_name:
            return error_response("Missing fileName in request body", status_code=400)
        
        # Validate file extension
        allowed_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
        file_ext = os.path.splitext(file_name)[1].lower()
        if file_ext not in allowed_extensions:
            return error_response(
                f"Invalid file type. Allowed: {', '.join(allowed_extensions)}",
                status_code=400
            )
        
        # Generate unique file path (prevent overwrites)
        import uuid
        unique_id = str(uuid.uuid4())
        file_path = f"content/{unique_id}{file_ext}"
        
        # Generate pre-signed URL for PUT operation
        presigned_url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": CONTENT_IMAGES_BUCKET,
                "Key": file_path,
                "ContentType": content_type,
            },
            ExpiresIn=300,  # 5 minutes
        )
        
        # Generate public URL (after upload, via CloudFront)
        # This will be the CloudFront URL + file_path
        public_url = f"https://content.repwarrior.net/{file_path}"
        
        return success_response({
            "uploadUrl": presigned_url,
            "publicUrl": public_url,
            "filePath": file_path,
            "expiresIn": 300,
        })
        
    except Exception as e:
        error_msg = str(e)
        if "Authentication required" in error_msg or "Admin access required" in error_msg:
            return error_response(error_msg, status_code=403)
        print(f"Error in admin/image_upload: {e}")
        return error_response(f"Internal server error: {str(e)}", status_code=500)

