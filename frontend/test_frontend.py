#!/usr/bin/env python3
"""
Frontend test script for Document RAG Interface
"""

import subprocess
import sys
import os
import json
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def test_package_json():
    """Test package.json exists and has required dependencies"""
    package_json = Path("package.json")
    if not package_json.exists():
        print("❌ package.json not found")
        return False
    
    try:
        with open(package_json) as f:
            data = json.load(f)
        
        required_deps = ["react", "react-dom", "axios"]
        deps = data.get("dependencies", {})
        
        for dep in required_deps:
            if dep in deps:
                print(f"✅ {dep}: {deps[dep]}")
            else:
                print(f"❌ Missing dependency: {dep}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Error reading package.json: {e}")
        return False

def test_node_modules():
    """Test that node_modules exists"""
    if Path("node_modules").exists():
        print("✅ node_modules directory exists")
        return True
    else:
        print("❌ node_modules directory not found")
        return False

def test_source_files():
    """Test that source files exist and are valid"""
    files = [
        ("src/App.jsx", "React App component"),
        ("src/api.js", "API client"),
        ("src/index.css", "Tailwind styles"),
        ("src/main.jsx", "React entry point"),
        ("vite.config.js", "Vite configuration"),
        ("tailwind.config.js", "Tailwind configuration"),
        ("postcss.config.js", "PostCSS configuration")
    ]
    
    all_exist = True
    for file_path, description in files:
        if Path(file_path).exists():
            print(f"✅ {file_path} - {description}")
        else:
            print(f"❌ Missing {file_path} - {description}")
            all_exist = False
    
    return all_exist

def test_build():
    """Test that the project builds successfully"""
    print("Testing build process...")
    success, stdout, stderr = run_command("npm run build")
    
    if success:
        print("✅ Build successful")
        if Path("dist").exists():
            print("✅ Build output created in dist/")
        return True
    else:
        print("❌ Build failed")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return False

def main():
    print("=== Frontend Test Script ===\n")
    
    # Change to frontend directory if not already there
    if not Path("package.json").exists():
        frontend_dir = Path("../frontend")
        if frontend_dir.exists():
            os.chdir(frontend_dir)
        else:
            print("❌ Cannot find frontend directory")
            return 1
    
    tests = [
        ("Package.json", test_package_json),
        ("Node modules", test_node_modules),
        ("Source files", test_source_files),
        ("Build process", test_build)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} test failed")
    
    print(f"\n=== Results: {passed}/{total} tests passed ===")
    
    if passed == total:
        print("🎉 All frontend tests passed!")
        print("\nThe frontend is ready to run:")
        print("1. npm run dev - Start development server")
        print("2. npm run build - Build for production")
        print("3. npm run preview - Preview production build")
        return 0
    else:
        print("❌ Some frontend tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())