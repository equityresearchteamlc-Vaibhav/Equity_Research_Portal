"""
Simple Secrets Configuration Checker
Validates secrets.toml without requiring Streamlit
"""

import os
import sys

# Reconfigure stdout to support UTF-8 characters like emojis in Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def check_secrets():
    """Check if secrets.toml exists and has required sections"""
    
    print("=" * 60)
    print("🔐 SECRETS CONFIGURATION CHECKER")
    print("=" * 60)
    print()
    
    # Check if secrets file exists
    secrets_path = ".streamlit/secrets.toml"
    if not os.path.exists(secrets_path):
        print("❌ ERROR: secrets.toml not found!")
        print(f"   Expected location: {secrets_path}")
        return False
    
    print(f"✅ secrets.toml file found at: {secrets_path}")
    print()
    
    # Read the file
    try:
        with open(secrets_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ ERROR: Could not read secrets.toml: {e}")
        return False
    
    # Check for required sections
    print("📋 Checking Required Sections...")
    print("-" * 60)
    
    required_sections = {
        "[angel_one]": "Angel One API Configuration",
        "[google_drive]": "Google Drive Configuration",
        "[gcp_service_account]": "GCP Service Account Configuration"
    }
    
    all_found = True
    for section, description in required_sections.items():
        if section in content:
            print(f"   ✅ {section} - {description}")
        else:
            print(f"   ❌ {section} - Missing!")
            all_found = False
    
    if not all_found:
        print()
        print("❌ Some required sections are missing!")
        return False
    
    print()
    print("📊 Checking Angel One Fields...")
    print("-" * 60)
    
    angel_fields = ["api_key", "client_code", "password", "totp_secret"]
    for field in angel_fields:
        if f'{field} =' in content:
            print(f"   ✅ {field}: Found")
        else:
            print(f"   ❌ {field}: Missing")
            all_found = False
    
    print()
    print("☁️  Checking Google Drive Fields...")
    print("-" * 60)
    
    drive_fields = ["folder_id", "apps_script_url", "apps_script_token"]
    for field in drive_fields:
        if f'{field} =' in content:
            print(f"   ✅ {field}: Found")
        else:
            print(f"   ❌ {field}: Missing")
            all_found = False
    
    print()
    print("🔑 Checking GCP Service Account Fields...")
    print("-" * 60)
    
    gcp_fields = [
        "type", "project_id", "private_key_id", "private_key",
        "client_email", "client_id"
    ]
    for field in gcp_fields:
        if f'{field} =' in content:
            if field == "private_key":
                if "BEGIN PRIVATE KEY" in content:
                    print(f"   ✅ {field}: Found (valid format)")
                else:
                    print(f"   ⚠️  {field}: Found (check format)")
            else:
                print(f"   ✅ {field}: Found")
        else:
            print(f"   ❌ {field}: Missing")
            all_found = False
    
    # Check file size
    file_size = os.path.getsize(secrets_path)
    print()
    print("📏 File Information...")
    print("-" * 60)
    print(f"   File size: {file_size} bytes")
    print(f"   Lines: {len(content.splitlines())}")
    
    # Final result
    print()
    print("=" * 60)
    if all_found:
        print("🎉 ALL CHECKS PASSED!")
        print("=" * 60)
        print()
        print("Your secrets.toml appears to be properly configured.")
        print("Run the portal with: streamlit run app.py")
        print()
        return True
    else:
        print("❌ SOME CHECKS FAILED")
        print("=" * 60)
        print()
        print("Please review the errors above and fix your secrets.toml")
        print("See SECRETS_SETUP_GUIDE.md for help.")
        print()
        return False


if __name__ == "__main__":
    try:
        success = check_secrets()
        sys.exit(0 if success else 1)
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ CHECK FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        sys.exit(1)
