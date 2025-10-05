#!/usr/bin/env python3
"""Test Supabase integration setup."""

import os
import sys

# Add src to path
sys.path.insert(0, "src")

from app.core.config import get_settings
from app.core.supabase import get_supabase_client, get_supabase_admin_client

def test_configuration():
    """Test that Supabase configuration is loaded correctly."""
    print("Testing Supabase configuration...")
    
    settings = get_settings()
    
    assert settings.supabase_url is not None, "SUPABASE_URL not configured"
    assert settings.supabase_anon_key is not None, "SUPABASE_ANON_KEY not configured"
    assert settings.supabase_service_role_key is not None, "SUPABASE_SERVICE_ROLE_KEY not configured"
    
    print(f"  ✅ SUPABASE_URL: {settings.supabase_url}")
    print(f"  ✅ SUPABASE_ANON_KEY: {settings.supabase_anon_key[:20]}...")
    print(f"  ✅ SUPABASE_SERVICE_ROLE_KEY: {settings.supabase_service_role_key[:20]}...")

def test_client_creation():
    """Test that Supabase clients can be created."""
    print("\nTesting Supabase client creation...")
    
    client = get_supabase_client()
    assert client is not None, "Failed to create Supabase client"
    print("  ✅ Supabase client created successfully")
    
    admin_client = get_supabase_admin_client()
    assert admin_client is not None, "Failed to create Supabase admin client"
    print("  ✅ Supabase admin client created successfully")

def test_auth_service():
    """Test that AuthService can be initialized with Supabase."""
    print("\nTesting AuthService initialization...")
    
    from app.services.auth import AuthService, SupabaseAuthRepositoryLive
    
    # Test creating service with live repository
    try:
        service = AuthService()
        print(f"  ✅ AuthService initialized with repository: {type(service._repository).__name__}")
        
        # Verify it's using the live repository
        if isinstance(service._repository, SupabaseAuthRepositoryLive):
            print("  ✅ Using SupabaseAuthRepositoryLive (connected to database)")
        else:
            print("  ⚠️  Using in-memory repository (fallback mode)")
    except Exception as e:
        print(f"  ❌ Error initializing AuthService: {e}")
        raise

def main():
    """Run all tests."""
    print("=" * 60)
    print("Supabase Integration Tests")
    print("=" * 60)
    
    try:
        test_configuration()
        test_client_creation()
        test_auth_service()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Apply database migrations via Supabase dashboard")
        print("2. Run the application: uvicorn app.main:app --reload")
        print("3. Test authentication endpoints")
        
        return 0
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
