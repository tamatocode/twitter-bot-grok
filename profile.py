#!/usr/bin/env python3
"""
Helper script to find your Chrome profile path and which profile to use
"""

import os
import platform
import json

def find_chrome_profiles():
    """Find Chrome profile paths for different OS"""
    
    system = platform.system()
    
    print("\n" + "="*70)
    print("🔍 FINDING YOUR CHROME PROFILE")
    print("="*70 + "\n")
    
    # Determine Chrome user data path based on OS
    if system == "Darwin":  # macOS
        chrome_path = os.path.expanduser("~/Library/Application Support/Google/Chrome")
        print(f"Operating System: macOS")
    elif system == "Windows":
        chrome_path = os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data")
        print(f"Operating System: Windows")
    else:  # Linux
        chrome_path = os.path.expanduser("~/.config/google-chrome")
        print(f"Operating System: Linux")
    
    print(f"Chrome Path: {chrome_path}\n")
    
    if not os.path.exists(chrome_path):
        print("❌ Chrome profile not found at default location!")
        print("\nTo find it manually:")
        print("1. Open Chrome")
        print("2. Go to: chrome://version/")
        print("3. Look for 'Profile Path'")
        print("4. Copy the path up to 'User Data' (not including the profile folder)")
        return None
    
    print("✓ Chrome installation found!\n")
    print("-"*70)
    print("AVAILABLE PROFILES:")
    print("-"*70 + "\n")
    
    # List all profiles
    profiles = []
    for item in os.listdir(chrome_path):
        profile_path = os.path.join(chrome_path, item)
        
        # Check if it's a profile directory
        if os.path.isdir(profile_path) and (item == "Default" or item.startswith("Profile ")):
            # Try to read profile name from Preferences
            prefs_path = os.path.join(profile_path, "Preferences")
            profile_name = item
            profile_email = "Unknown"
            
            if os.path.exists(prefs_path):
                try:
                    with open(prefs_path, 'r', encoding='utf-8') as f:
                        prefs = json.load(f)
                        # Get profile name
                        if 'profile' in prefs and 'name' in prefs['profile']:
                            profile_name = prefs['profile']['name']
                        # Try to get email from account_info
                        if 'account_info' in prefs:
                            accounts = prefs['account_info']
                            if accounts:
                                first_account = list(accounts.values())[0]
                                if 'email' in first_account:
                                    profile_email = first_account['email']
                except Exception as e:
                    pass
            
            profiles.append({
                'folder': item,
                'name': profile_name,
                'email': profile_email,
                'path': profile_path
            })
    
    # Display profiles
    for i, profile in enumerate(profiles, 1):
        print(f"Profile {i}:")
        print(f"  Folder Name: {profile['folder']}")
        print(f"  Display Name: {profile['name']}")
        print(f"  Email: {profile['email']}")
        print(f"  Path: {profile['path']}")
        print()
    
    print("-"*70)
    print("\n📋 CONFIGURATION INSTRUCTIONS:")
    print("-"*70 + "\n")
    
    # Find the profile with matching email
    target_email = "adin.24504@sscbs.du.ac.in"
    matching_profile = None
    
    for profile in profiles:
        if target_email.lower() in profile['email'].lower():
            matching_profile = profile
            break
    
    if matching_profile:
        print(f"✓ Found profile with email: {target_email}")
        print(f"\nProfile to use: {matching_profile['folder']}\n")
    else:
        print(f"❌ Could not find profile with email: {target_email}")
        print(f"\nCheck which profile you use by looking at the emails above.")
        print(f"Usually it's 'Default' or 'Profile 1'\n")
    
    print("="*70)
    print("TO USE THIS PROFILE IN YOUR BOT:")
    print("="*70 + "\n")
    
    print("Option 1: Edit main.py (line ~20)")
    print("-" * 40)
    print("Change these lines:")
    print(f'  USE_EXISTING_PROFILE = True')
    print(f'  options.add_argument("user-data-dir={chrome_path}")')
    
    if matching_profile:
        print(f'  options.add_argument("profile-directory={matching_profile["folder"]}")')
    else:
        print(f'  options.add_argument("profile-directory=Default")  # Or Profile 1, Profile 2, etc.')
    
    print("\nOption 2: Quick test")
    print("-" * 40)
    print("Run the bot - it will automatically try to use your Default profile!")
    print("If it doesn't work, check chrome://version/ to see which profile you use.")
    
    print("\n" + "="*70)
    print("⚠️  IMPORTANT NOTES:")
    print("="*70)
    print("• Close ALL Chrome windows before running the bot")
    print("• Chrome and Selenium can't use the same profile simultaneously")
    print("• The bot will open a new Chrome window with your existing login")
    print("="*70 + "\n")
    
    return chrome_path, profiles

if __name__ == "__main__":
    find_chrome_profiles()