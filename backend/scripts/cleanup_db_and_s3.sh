#!/bin/bash
# Script to clean up database and S3 bucket for fresh start

set -e

echo "🧹 Cleaning up database and S3 bucket..."

# Database cleanup
echo "📊 Truncating documents table..."
psql -h localhost -U postgres -d financial_poc -c "TRUNCATE TABLE documents CASCADE;"

# Add the missing column if needed
echo "📊 Adding pdf_preview_path column..."
psql -h localhost -U postgres -d financial_poc -c "ALTER TABLE documents ADD COLUMN IF NOT EXISTS pdf_preview_path VARCHAR(255) DEFAULT NULL;"

# MinIO/S3 cleanup
echo "🗑️  Clearing MinIO bucket..."
# Using mc (MinIO Client) - adjust alias if different
# mc rm --recursive --force local/documents/

# Alternative using Python with boto3
python3 << 'PYTHON_SCRIPT'
import os
from minio import Minio

# MinIO configuration from your settings
minio_client = Minio(
    "localhost:9000",
    access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
    secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
    secure=False
)

bucket_name = os.getenv("MINIO_BUCKET", "documents")

# List and delete all objects
try:
    objects = minio_client.list_objects(bucket_name, recursive=True)
    for obj in objects:
        minio_client.remove_object(bucket_name, obj.object_name)
        print(f"  ✓ Deleted: {obj.object_name}")
    print(f"✅ Cleared all objects from bucket '{bucket_name}'")
except Exception as e:
    print(f"⚠️  Error clearing bucket: {e}")
PYTHON_SCRIPT

echo ""
echo "✅ Cleanup complete!"
echo "   - Documents table truncated"
echo "   - pdf_preview_path column added"
echo "   - S3 bucket cleared"
