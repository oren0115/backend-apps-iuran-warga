"""
Dependency Security Checker
Check untuk known vulnerabilities dalam Python dependencies

Usage:
    python testing/check_dependencies.py
"""

import subprocess
import sys
import json
from datetime import datetime

def check_pip_outdated():
    """Check for outdated packages"""
    print("🔍 Checking for outdated packages...")
    print("-" * 80)
    
    try:
        result = subprocess.run(
            ['pip', 'list', '--outdated', '--format=json'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            outdated = json.loads(result.stdout)
            
            if outdated:
                print(f"⚠️  Found {len(outdated)} outdated packages:\n")
                for pkg in outdated:
                    print(f"  📦 {pkg['name']}")
                    print(f"     Current: {pkg['version']}")
                    print(f"     Latest:  {pkg['latest_version']}")
                    print()
                
                print("💡 Recommendation: Update packages using:")
                print("   pip install --upgrade <package-name>")
                print()
            else:
                print("✅ All packages are up to date!\n")
        else:
            print(f"❌ Error checking outdated packages: {result.stderr}\n")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")

def check_with_safety():
    """Check for known security vulnerabilities using safety"""
    print("🔍 Checking for known security vulnerabilities...")
    print("-" * 80)
    
    try:
        # Try to run safety check
        result = subprocess.run(
            ['safety', 'check', '--json'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ No known security vulnerabilities found!\n")
        else:
            # Parse output
            try:
                vulnerabilities = json.loads(result.stdout)
                if vulnerabilities:
                    print(f"🚨 Found {len(vulnerabilities)} security vulnerabilities:\n")
                    for vuln in vulnerabilities:
                        print(f"  📦 Package: {vuln[0]}")
                        print(f"     Installed: {vuln[2]}")
                        print(f"     Vulnerability: {vuln[3]}")
                        print(f"     Fix: Upgrade to {vuln[1]}")
                        print()
            except:
                print(result.stdout)
                print()
        
    except FileNotFoundError:
        print("⚠️  'safety' not installed. Install with:")
        print("   pip install safety")
        print("\nSkipping vulnerability check...\n")
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")

def check_critical_packages():
    """Check versions of critical security-related packages"""
    print("🔍 Checking critical security packages...")
    print("-" * 80)
    
    critical_packages = [
        'fastapi',
        'pydantic',
        'jwt',
        'cryptography',
        'requests',
        'python-jose',
        'passlib'
    ]
    
    try:
        result = subprocess.run(
            ['pip', 'list', '--format=json'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            installed = json.loads(result.stdout)
            installed_dict = {pkg['name'].lower(): pkg['version'] for pkg in installed}
            
            print("Critical security packages status:\n")
            for pkg in critical_packages:
                if pkg.lower() in installed_dict:
                    print(f"  ✅ {pkg}: {installed_dict[pkg.lower()]}")
                else:
                    print(f"  ⚠️  {pkg}: Not installed")
            print()
            
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")

def check_requirements_file():
    """Check if requirements.txt has pinned versions"""
    print("🔍 Checking requirements.txt for version pinning...")
    print("-" * 80)
    
    try:
        with open('requirements.txt', 'r') as f:
            lines = f.readlines()
        
        unpinned = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                if '==' not in line and '>=' not in line and '<=' not in line:
                    unpinned.append(line)
        
        if unpinned:
            print("⚠️  Found packages without pinned versions:\n")
            for pkg in unpinned:
                print(f"  - {pkg}")
            print("\n💡 Recommendation: Pin package versions for production:")
            print("   Use '==' to specify exact versions")
            print("   Example: fastapi==0.104.1")
            print()
        else:
            print("✅ All packages have pinned versions!\n")
            
    except FileNotFoundError:
        print("⚠️  requirements.txt not found\n")
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")

def main():
    print("\n" + "="*80)
    print("🔒 DEPENDENCY SECURITY CHECK")
    print("="*80)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    check_pip_outdated()
    check_with_safety()
    check_critical_packages()
    check_requirements_file()
    
    print("="*80)
    print("✅ Dependency security check completed!")
    print("="*80)
    print("\n💡 Next steps:")
    print("   1. Update outdated packages")
    print("   2. Fix any security vulnerabilities")
    print("   3. Pin package versions in requirements.txt")
    print("   4. Run 'pip freeze > requirements.txt' to update")
    print()

if __name__ == "__main__":
    main()
