#!/usr/bin/env python3
"""Quick test to verify all imports work."""

import sys

def test_imports():
    """Test that all refactored modules can be imported."""
    
    print("Testing imports...")
    
    try:
        from app.core.supabase import get_supabase_client, require_supabase
        print("✓ Supabase client imports successful")
    except Exception as e:
        print(f"✗ Supabase client import failed: {e}")
        return False
    
    try:
        from app.core.dependencies import get_db, require_auth
        print("✓ Dependencies imports successful")
    except Exception as e:
        print(f"✗ Dependencies import failed: {e}")
        return False
    
    try:
        from app.services.auth_supabase import AuthService, get_auth_service
        print("✓ AuthService imports successful")
    except Exception as e:
        print(f"✗ AuthService import failed: {e}")
        return False
    
    try:
        from app.api.routes import auth
        print("✓ Auth routes imports successful")
    except Exception as e:
        print(f"✗ Auth routes import failed: {e}")
        return False
    
    try:
        from app.core.application import create_app
        print("✓ Application factory imports successful")
    except Exception as e:
        print(f"✗ Application factory import failed: {e}")
        return False
    
    print("\n✅ All imports successful!")
    return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
