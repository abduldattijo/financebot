#!/usr/bin/env python3
"""
Quick Setup Test for Nigerian Bank Statement Transformer
Run this to verify your M4 MacBook + PyCharm setup is working correctly
"""

import sys
import os
import platform
from pathlib import Path


def test_system_info():
    """Test system compatibility"""
    print("🔍 System Information:")
    print(f"   Platform: {platform.platform()}")
    print(f"   Architecture: {platform.machine()}")
    print(f"   Python Version: {sys.version}")

    # Check if running on Apple Silicon
    if platform.machine() == 'arm64':
        print("   ✅ Apple Silicon (M-series) detected - Optimized!")
    else:
        print("   ⚠️  Not running on Apple Silicon")

    print()


def test_python_version():
    """Test Python version compatibility"""
    print("🐍 Python Version Check:")

    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro} - Compatible!")
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} - Upgrade to 3.9+")
        return False

    print()
    return True


def test_dependencies():
    """Test required dependencies"""
    print("📦 Dependencies Check:")

    required_packages = [
        'pandas',
        'openpyxl',
        'flask',
        'xlrd',
        'odfpy'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - Missing!")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n   📝 Install missing packages:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False

    print("   🎉 All dependencies installed!")
    print()
    return True


def test_transformer():
    """Test the transformer engine"""
    print("🔧 Transformer Engine Test:")

    try:
        # Try to import our transformer
        from bank_transformer import BankStatementTransformer

        # Initialize transformer
        transformer = BankStatementTransformer()

        print("   ✅ Transformer imported successfully")
        print(f"   ✅ Standard headers: {len(transformer.standard_headers)} columns")
        print(f"   ✅ Bank formats: {len(transformer.bank_formats)} supported")

        # Test basic functionality
        test_amount = transformer._parse_amount("1,234.56")
        if test_amount == 1234.56:
            print("   ✅ Amount parsing works")

        print("   🎉 Transformer engine ready!")
        print()
        return True

    except Exception as e:
        print(f"   ❌ Transformer test failed: {str(e)}")
        print()
        return False


def test_flask_app():
    """Test Flask application"""
    print("🌐 Flask Application Test:")

    try:
        from app import app

        # Test if app can be created
        with app.test_client() as client:
            # Test health endpoint
            response = client.get('/api/health')
            if response.status_code == 200:
                print("   ✅ Flask app initialized")
                print("   ✅ Health endpoint working")
            else:
                print(f"   ⚠️  Health endpoint returned: {response.status_code}")

        print("   🎉 Flask application ready!")
        print()
        return True

    except Exception as e:
        print(f"   ❌ Flask test failed: {str(e)}")
        print()
        return False


def test_file_processing():
    """Test file processing capabilities"""
    print("📄 File Processing Test:")

    try:
        from bank_transformer import BankStatementTransformer
        import pandas as pd

        transformer = BankStatementTransformer()

        # Create a simple test DataFrame
        test_data = [
            ['Transaction Date', 'Description', 'Withdrawls', 'Deposits', 'Balance'],
            ['01/01/2024', 'Test Transaction', '', '1000.00', '1000.00'],
            ['02/01/2024', 'Another Transaction', '500.00', '', '500.00']
        ]

        # Test date standardization
        test_date = transformer._standardize_date('01/01/2024')
        if test_date:
            print("   ✅ Date standardization works")

        # Test amount parsing
        test_amount = transformer._standardize_amount('1,234.56')
        if test_amount == '1234.56':
            print("   ✅ Amount standardization works")

        print("   🎉 File processing ready!")
        print()
        return True

    except Exception as e:
        print(f"   ❌ File processing test failed: {str(e)}")
        print()
        return False


def create_project_structure():
    """Create recommended project structure"""
    print("📁 Project Structure Setup:")

    directories = [
        'sample_files',
        'output',
        'tests',
        'static',
        'templates'
    ]

    for directory in directories:
        try:
            Path(directory).mkdir(exist_ok=True)
            print(f"   ✅ Created: {directory}/")
        except Exception as e:
            print(f"   ⚠️  Could not create {directory}/: {str(e)}")

    # Create .gitignore
    gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/

# Flask
instance/
.webassets-cache

# PyCharm
.idea/

# Output files
output/
*.xlsx
*.xls
*.ods

# Logs
*.log

# OS
.DS_Store
Thumbs.db
"""

    try:
        with open('.gitignore', 'w') as f:
            f.write(gitignore_content.strip())
        print("   ✅ Created: .gitignore")
    except Exception as e:
        print(f"   ⚠️  Could not create .gitignore: {str(e)}")

    print("   🎉 Project structure ready!")
    print()


def print_next_steps():
    """Print next steps for the user"""
    print("🚀 Setup Complete! Next Steps:")
    print()
    print("1. 📁 Copy your bank statement files to 'sample_files/' folder")
    print("2. 🔧 Run the Flask app:")
    print("   python app.py")
    print()
    print("3. 🌐 Open your browser to:")
    print("   http://localhost:5000")
    print()
    print("4. 📤 Upload your bank statements and test the transformation")
    print()
    print("5. 🔍 For development, use PyCharm's debugger:")
    print("   - Set breakpoints in bank_transformer.py")
    print("   - Run in Debug mode")
    print()
    print("📚 For more help, see the setup instructions!")
    print()


def main():
    """Run all tests"""
    print("🏛️  Nigerian Bank Statement Transformer - Setup Test")
    print("=" * 60)
    print()

    all_tests_passed = True

    # Run all tests
    test_system_info()

    if not test_python_version():
        all_tests_passed = False

    if not test_dependencies():
        all_tests_passed = False

    if not test_transformer():
        all_tests_passed = False

    if not test_flask_app():
        all_tests_passed = False

    if not test_file_processing():
        all_tests_passed = False

    # Create project structure regardless
    create_project_structure()

    # Summary
    print("=" * 60)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED! Your setup is ready!")
        print()
        print_next_steps()
    else:
        print("⚠️  Some tests failed. Please fix the issues above before proceeding.")
        print()
        print("💡 Common fixes:")
        print("   - Install missing packages: pip install -r requirements.txt")
        print("   - Check Python version: python --version")
        print("   - Verify virtual environment is activated")

    print("=" * 60)


if __name__ == "__main__":
    main()