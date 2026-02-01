"""
Cleanup script to truncate documents table and clear S3 bucket.
Run this to start fresh for testing.
"""

import asyncio
import sys

# Add backend to path
sys.path.insert(0, "/Users/bakiel/git/financial-poc/backend")

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from src.core.storage import minio_client, settings as minio_settings
from src.configurations.database import DatabaseSettings

# Instantiate settings
db_settings = DatabaseSettings()


async def cleanup_database():
    """Truncate documents, conversations, and messages tables, and add missing column."""
    print("📊 Cleaning up database...")

    # Create async engine
    engine = create_async_engine(db_settings.DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        # Truncate all tables (CASCADE handles foreign keys)
        print("  - Truncating conversations and messages tables...")
        await conn.execute(text("TRUNCATE TABLE conversations CASCADE"))

        print("  - Truncating documents table...")
        await conn.execute(text("TRUNCATE TABLE documents CASCADE"))

        # Add pdf_preview_path column if it doesn't exist
        print("  - Adding pdf_preview_path column...")
        await conn.execute(
            text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS pdf_preview_path VARCHAR(255) DEFAULT NULL")
        )

    await engine.dispose()
    print("✅ Database cleanup complete")


def cleanup_s3():
    """Clear all objects from S3 bucket."""
    print("🗑️  Cleaning up S3 bucket...")

    bucket_name = minio_settings.MINIO_BUCKET

    try:
        objects = list(minio_client.list_objects(bucket_name, recursive=True))
        if objects:
            for obj in objects:
                minio_client.remove_object(bucket_name, obj.object_name)
                print(f"  ✓ Deleted: {obj.object_name}")
            print(f"✅ Cleared {len(objects)} objects from bucket '{bucket_name}'")
        else:
            print(f"ℹ️  Bucket '{bucket_name}' is already empty")
    except Exception as e:
        print(f"⚠️  Error clearing bucket: {e}")


async def main():
    print("\n🧹 Starting cleanup...\n")

    # Cleanup database
    await cleanup_database()
    print()

    # Cleanup S3
    cleanup_s3()

    print("\n✅ All cleanup complete!")
    print("   - Conversations and messages tables truncated")
    print("   - Documents table truncated")
    print("   - pdf_preview_path column added")
    print("   - S3 bucket cleared")
    print("\nReady for fresh testing! 🚀\n")


if __name__ == "__main__":
    asyncio.run(main())
