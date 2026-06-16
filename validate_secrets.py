"""
Secrets Configuration Validator
Validates that all required secrets are properly configured
"""

import sys
import os

# Reconfigure stdout to support UTF-8 characters like emojis in Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def validate_secrets():
    """Validate secrets.toml configuration"""
    
    print("=" * 60)
    print("🔐 SECRETS CONFIGURATION VALIDATOR")
    print("=" * 60)
    print()
    
    # Check if secrets file exists
    secrets_path = ".streamlit/secrets.toml"
    if not os.path.exists(secrets_path):
        print("❌ ERROR: secrets.toml not found!")
        print(f"   Expected location: {secrets_path}")
        return False
    
    print("✅ secrets.toml file found")
    print()
    
    # Try to load secrets using streamlit
    try:
        import streamlit as st
        print("✅ Streamlit imported successfully")
    except ImportError:
        print("❌ ERROR: Streamlit not installed")
        print("   Run: pip install streamlit")
        return False
    
    # Validate Angel One configuration
    print()
    print("📊 Validating Angel One Configuration...")
    print("-" * 60)
    
    try:
        angel_config = st.secrets["angel_one"]
        
        required_fields = ["api_key", "client_code", "password", "totp_secret"]
        for field in required_fields:
            if field in angel_config and angel_config[field]:
                print(f"   ✅ {field}: Configured")
            else:
                print(f"   ❌ {field}: Missing or empty")
                return False
        
        print("✅ Angel One configuration is complete")
        
    except KeyError:
        print("❌ ERROR: [angel_one] section not found in secrets.toml")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    
    # Validate Google Drive configuration
    print()
    print("☁️  Validating Google Drive Configuration...")
    print("-" * 60)
    
    try:
        drive_config = st.secrets["google_drive"]
        
        required_fields = ["folder_id", "apps_script_url", "apps_script_token"]
        for field in required_fields:
            if field in drive_config and drive_config[field]:
                print(f"   ✅ {field}: Configured")
            else:
                print(f"   ❌ {field}: Missing or empty")
                return False
        
        print("✅ Google Drive configuration is complete")
        
    except KeyError:
        print("❌ ERROR: [google_drive] section not found in secrets.toml")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    
    # Validate GCP Service Account configuration
    print()
    print("🔑 Validating GCP Service Account Configuration...")
    print("-" * 60)
    
    try:
        gcp_config = st.secrets["gcp_service_account"]
        
        required_fields = [
            "type", "project_id", "private_key_id", "private_key",
            "client_email", "client_id", "auth_uri", "token_uri"
        ]
        
        for field in required_fields:
            if field in gcp_config and gcp_config[field]:
                if field == "private_key":
                    # Check if private key is properly formatted
                    if "BEGIN PRIVATE KEY" in gcp_config[field]:
                        print(f"   ✅ {field}: Configured (valid format)")
                    else:
                        print(f"   ⚠️  {field}: Configured but may be invalid format")
                else:
                    print(f"   ✅ {field}: Configured")
            else:
                print(f"   ❌ {field}: Missing or empty")
                return False
        
        print("✅ GCP Service Account configuration is complete")
        
    except KeyError:
        print("❌ ERROR: [gcp_service_account] section not found in secrets.toml")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    
    # All validations passed
    print()
    print("=" * 60)
    print("🎉 ALL VALIDATIONS PASSED!")
    print("=" * 60)
    print()
    print("Your secrets.toml is properly configured.")
    print("You can now run the portal with: streamlit run app.py")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = validate_secrets()
        sys.exit(0 if success else 1)
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ VALIDATION FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        print("Please check your secrets.toml configuration.")
        print("See SECRETS_SETUP_GUIDE.md for help.")
        sys.exit(1)
