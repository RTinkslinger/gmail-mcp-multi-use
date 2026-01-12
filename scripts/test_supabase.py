#!/usr/bin/env python3
"""Test script to verify Supabase storage backend works.

This script tests basic CRUD operations against the Supabase database.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gmail_multi_user.config import ConfigLoader
from gmail_multi_user.storage.supabase import SupabaseBackend


async def main() -> None:
    """Run Supabase connection tests."""
    print("=" * 60)
    print("Supabase Storage Backend Test")
    print("=" * 60)

    # Load config
    loader = ConfigLoader()
    config = loader.load()
    print(f"\nConfig loaded from: {loader.get_config_path()}")
    print(f"Storage type: {config.storage.type}")

    if config.storage.type != "supabase":
        print("\nERROR: Config is not set to use Supabase!")
        print("Update storage.type to 'supabase' in gmail_config.yaml")
        return

    if config.storage.supabase is None:
        print("\nERROR: Supabase config not found!")
        return

    print(f"Supabase URL: {config.storage.supabase.url}")

    # Initialize Supabase backend
    backend = SupabaseBackend(
        supabase_url=config.storage.supabase.url,
        supabase_key=config.storage.supabase.key,
    )

    try:
        # Test 1: Initialize (verify connection)
        print("\n" + "-" * 40)
        print("Test 1: Initialize connection")
        print("-" * 40)
        await backend.initialize()
        print("✓ Connection successful!")

        # Test 2: Health check
        print("\n" + "-" * 40)
        print("Test 2: Health check")
        print("-" * 40)
        healthy = await backend.health_check()
        print(f"✓ Health check: {'healthy' if healthy else 'unhealthy'}")

        # Test 3: Create a user
        print("\n" + "-" * 40)
        print("Test 3: Create/get user")
        print("-" * 40)
        user = await backend.get_or_create_user(
            external_user_id="test_user_supabase",
            email="test@example.com",
        )
        print(f"✓ User ID: {user.id}")
        print(f"  External ID: {user.external_user_id}")
        print(f"  Email: {user.email}")

        # Test 4: List users
        print("\n" + "-" * 40)
        print("Test 4: List users")
        print("-" * 40)
        users = await backend.list_users()
        print(f"✓ Found {len(users)} user(s)")
        for u in users:
            print(f"  - {u.external_user_id} ({u.email})")

        # Test 5: Create a connection
        print("\n" + "-" * 40)
        print("Test 5: Create connection")
        print("-" * 40)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        # First check if connection exists and delete it
        existing = await backend.get_connection_by_user_and_email(
            user_id=user.id,
            gmail_address="test_supabase@gmail.com",
        )
        if existing:
            await backend.delete_connection(existing.id)
            print("  (Deleted existing test connection)")

        connection = await backend.create_connection(
            user_id=user.id,
            gmail_address="test_supabase@gmail.com",
            access_token_encrypted="encrypted_access_token_test",
            refresh_token_encrypted="encrypted_refresh_token_test",
            token_expires_at=expires_at,
            scopes=["gmail.readonly", "gmail.send"],
        )
        print(f"✓ Connection ID: {connection.id}")
        print(f"  Gmail: {connection.gmail_address}")
        print(f"  Active: {connection.is_active}")

        # Test 6: Get connection
        print("\n" + "-" * 40)
        print("Test 6: Get connection")
        print("-" * 40)
        fetched = await backend.get_connection(connection.id)
        print(f"✓ Fetched connection: {fetched.id if fetched else 'None'}")

        # Test 7: List connections
        print("\n" + "-" * 40)
        print("Test 7: List connections")
        print("-" * 40)
        connections = await backend.list_connections()
        print(f"✓ Found {len(connections)} connection(s)")

        # Test 8: Update connection tokens
        print("\n" + "-" * 40)
        print("Test 8: Update connection tokens")
        print("-" * 40)
        new_expires = datetime.now(timezone.utc) + timedelta(hours=2)
        updated = await backend.update_connection_tokens(
            connection_id=connection.id,
            access_token_encrypted="new_encrypted_token",
            refresh_token_encrypted=None,
            token_expires_at=new_expires,
        )
        print(f"✓ Updated token expires at: {updated.token_expires_at}")

        # Test 9: Create and cleanup OAuth state
        print("\n" + "-" * 40)
        print("Test 9: OAuth state operations")
        print("-" * 40)
        state_expires = datetime.now(timezone.utc) + timedelta(minutes=10)
        oauth_state = await backend.create_oauth_state(
            state="test_state_12345",
            user_id=user.id,
            scopes=["gmail.readonly"],
            redirect_uri="http://localhost:8000/callback",
            code_verifier="test_verifier",
            expires_at=state_expires,
        )
        print(f"✓ Created OAuth state: {oauth_state.state}")

        fetched_state = await backend.get_oauth_state("test_state_12345")
        print(f"✓ Fetched OAuth state: {fetched_state.state if fetched_state else 'None'}")

        await backend.delete_oauth_state("test_state_12345")
        print("✓ Deleted OAuth state")

        # Test 10: Clean up test data
        print("\n" + "-" * 40)
        print("Test 10: Cleanup test data")
        print("-" * 40)
        await backend.delete_connection(connection.id)
        print("✓ Deleted test connection")

        # Note: We'll leave the user for now (might be useful)

        print("\n" + "=" * 60)
        print("All Supabase tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return

    finally:
        await backend.close()


if __name__ == "__main__":
    asyncio.run(main())
