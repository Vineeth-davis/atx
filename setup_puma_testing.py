"""
Quick Setup Script for Puma Database Testing

This script helps you quickly set up and test the Puma database functionality.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add current directory to Python path
sys.path.append('.')

def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    required_packages = ['pyodbc', 'asyncio']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Install missing packages:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ All dependencies are installed!")
    return True

def check_odbc_drivers():
    """Check available ODBC drivers."""
    print("\n🔍 Checking ODBC drivers...")
    
    try:
        import pyodbc
        drivers = pyodbc.drivers()
        
        sql_server_drivers = [d for d in drivers if 'SQL Server' in d or 'ODBC Driver' in d]
        
        if sql_server_drivers:
            print("✅ Available SQL Server drivers:")
            for driver in sql_server_drivers:
                print(f"  📋 {driver}")
            return sql_server_drivers[0]  # Return the first one
        else:
            print("❌ No SQL Server ODBC drivers found!")
            print("📥 Download and install ODBC Driver for SQL Server from Microsoft")
            return None
            
    except ImportError:
        print("❌ pyodbc not installed")
        return None

def create_config_file():
    """Create configuration file from template."""
    print("\n📝 Creating configuration file...")
    
    template_file = Path("puma_config_template.py")
    config_file = Path("puma_config.py")
    
    if not template_file.exists():
        print("❌ Template file not found!")
        return False
    
    if config_file.exists():
        print(f"⚠️  Configuration file already exists: {config_file}")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("📄 Using existing configuration file")
            return True
    
    # Copy template to config
    with open(template_file, 'r') as f:
        content = f.read()
    
    with open(config_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Configuration file created: {config_file}")
    print("📝 Please edit this file with your database details")
    return True

def run_quick_test():
    """Run a quick connection test."""
    print("\n🚀 Running quick connection test...")
    
    try:
        from puma_config import get_config
        config = get_config()
        
        # Check if config is still using template values
        if config.host == "your-sql-server-host":
            print("⚠️  Configuration still uses template values!")
            print("📝 Please edit puma_config.py with your actual database details")
            return False
        
        print(f"🔌 Testing connection to: {config.host}:{config.port}/{config.database}")
        
        # Import and test connection
        from adapters.sqlserver_adapter import SQLServerAdapter
        
        async def test_connection():
            adapter = SQLServerAdapter(config)
            try:
                success = await adapter.connect()
                if success:
                    print("✅ Connection successful!")
                    await adapter.disconnect()
                    return True
                else:
                    print("❌ Connection failed")
                    return False
            except Exception as e:
                print(f"❌ Connection error: {e}")
                return False
        
        return asyncio.run(test_connection())
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("📝 Make sure puma_config.py exists and is properly configured")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def show_next_steps():
    """Show next steps for testing."""
    print("\n🎯 Next Steps:")
    print("=" * 50)
    print("1. 📝 Edit puma_config.py with your database details:")
    print("   - Update host, database, username, password")
    print("   - Update table names in sample queries")
    print("   - Update business domain mapping")
    print()
    print("2. 🚀 Run comprehensive tests:")
    print("   python puma_database_tester.py")
    print()
    print("3. 🔍 Test specific functionality:")
    print("   - Connection: test_connection()")
    print("   - Schema introspection: test_schema_introspection()")
    print("   - Custom queries: test_custom_queries()")
    print()
    print("4. 📊 Generate test report:")
    print("   - Report will be saved as 'puma_test_report.md'")
    print()
    print("5. 🚧 Future: NL→SQL testing (Phase 3 implementation)")

def main():
    """Main setup function."""
    print("🚀 Puma Database Testing Setup")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install missing dependencies first")
        return
    
    # Check ODBC drivers
    driver = check_odbc_drivers()
    if not driver:
        print("\n❌ Please install SQL Server ODBC driver first")
        return
    
    # Create config file
    if not create_config_file():
        print("\n❌ Failed to create configuration file")
        return
    
    # Run quick test
    print(f"\n🔧 Using ODBC driver: {driver}")
    test_success = run_quick_test()
    
    # Show next steps
    show_next_steps()
    
    if test_success:
        print("\n✅ Setup completed successfully!")
        print("🎉 Ready to run comprehensive tests!")
    else:
        print("\n⚠️  Setup completed with warnings")
        print("📝 Please configure your database details and try again")

if __name__ == "__main__":
    main()
