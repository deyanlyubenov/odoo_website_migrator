#!/usr/bin/env python3
"""
Test script for Odoo Website Migrator
=====================================

This script tests the connection and basic functionality of the migration tool.
"""

import xmlrpc.client
import json
import sys
from datetime import datetime


def test_odoo_connection(url: str, db: str, username: str, password: str) -> bool:
    """
    Test connection to an Odoo instance.
    
    Args:
        url: Odoo instance URL
        db: Database name
        username: Username
        password: Password
        
    Returns:
        True if connection successful, False otherwise
    """
    try:
        print(f"Testing connection to {url}...")
        
        # Create SSL context that ignores certificate verification for HTTPS connections
        import ssl
        if url.startswith('https://'):
            # Create SSL context that doesn't verify certificates
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Create transport with custom SSL context
            import xmlrpc.client
            transport = xmlrpc.client.SafeTransport(context=ssl_context)
            common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', transport=transport)
            models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', transport=transport)
        else:
            common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
            models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        
        uid = common.authenticate(db, username, password, {})
        
        if not uid:
            print(f"❌ Authentication failed for {url}")
            return False
        
        # Test basic model access
        version_info = common.version()
        print(f"✅ Successfully connected to {url}")
        print(f"   Odoo version: {version_info.get('server_version', 'Unknown')}")
        print(f"   Database: {db}")
        print(f"   User ID: {uid}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed to {url}: {str(e)}")
        return False


def test_website_models(url: str, db: str, username: str, password: str) -> dict:
    """
    Test access to website-related models.
    
    Args:
        url: Odoo instance URL
        db: Database name
        username: Username
        password: Password
        
    Returns:
        Dictionary with test results
    """
    results = {
        'website_page': False,
        'website_menu': False,
        'ir_module_module': False,
        'ir_attachment': False
    }
    
    try:
        # Create SSL context that ignores certificate verification for HTTPS connections
        import ssl
        if url.startswith('https://'):
            # Create SSL context that doesn't verify certificates
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Create transport with custom SSL context
            import xmlrpc.client
            transport = xmlrpc.client.SafeTransport(context=ssl_context)
            models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', transport=transport)
            common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', transport=transport)
        else:
            models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
            common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        uid = common.authenticate(db, username, password, {})
        
        # Test website.page model
        try:
            pages = models.execute_kw(db, uid, password, 'website.page', 'search_count', [[]])
            results['website_page'] = True
            print(f"✅ website.page model accessible ({pages} pages found)")
        except Exception as e:
            print(f"❌ website.page model not accessible: {str(e)}")
        
        # Test website.menu model
        try:
            menus = models.execute_kw(db, uid, password, 'website.menu', 'search_count', [[]])
            results['website_menu'] = True
            print(f"✅ website.menu model accessible ({menus} menus found)")
        except Exception as e:
            print(f"❌ website.menu model not accessible: {str(e)}")
        
        # Test ir.module.module model
        try:
            modules = models.execute_kw(db, uid, password, 'ir.module.module', 'search_count', [[]])
            results['ir_module_module'] = True
            print(f"✅ ir.module.module model accessible ({modules} modules found)")
        except Exception as e:
            print(f"❌ ir.module.module model not accessible: {str(e)}")
        
        # Test ir.attachment model
        try:
            attachments = models.execute_kw(db, uid, password, 'ir.attachment', 'search_count', [[]])
            results['ir_attachment'] = True
            print(f"✅ ir.attachment model accessible ({attachments} attachments found)")
        except Exception as e:
            print(f"❌ ir.attachment model not accessible: {str(e)}")
        
    except Exception as e:
        print(f"❌ Error testing models: {str(e)}")
    
    return results


def main():
    """Main test function."""
    print("Odoo Website Migrator - Connection Test")
    print("=" * 50)
    
    # Load configuration if available
    config = None
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        print("📁 Configuration file loaded")
    except FileNotFoundError:
        print("⚠️  No config.json found, using default test values")
        config = {
            'source': {
                'url': 'http://localhost:8069',
                'database': 'odoo16_test',
                'username': 'admin',
                'password': 'admin'
            },
            'target': {
                'url': 'http://localhost:8070',
                'database': 'odoo18_test',
                'username': 'admin',
                'password': 'admin'
            }
        }
    
    # Test source connection
    print("\n🔍 Testing Source Connection (Odoo 16)")
    print("-" * 40)
    source_ok = test_odoo_connection(
        config['source']['url'],
        config['source']['database'],
        config['source']['username'],
        config['source']['password']
    )
    
    if source_ok:
        print("\n🔍 Testing Source Website Models")
        print("-" * 40)
        source_models = test_website_models(
            config['source']['url'],
            config['source']['database'],
            config['source']['username'],
            config['source']['password']
        )
    
    # Test target connection
    print("\n🔍 Testing Target Connection (Odoo 18)")
    print("-" * 40)
    target_ok = test_odoo_connection(
        config['target']['url'],
        config['target']['database'],
        config['target']['username'],
        config['target']['password']
    )
    
    if target_ok:
        print("\n🔍 Testing Target Website Models")
        print("-" * 40)
        target_models = test_website_models(
            config['target']['url'],
            config['target']['database'],
            config['target']['username'],
            config['target']['password']
        )
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    print(f"Source Connection: {'✅ OK' if source_ok else '❌ FAILED'}")
    print(f"Target Connection: {'✅ OK' if target_ok else '❌ FAILED'}")
    
    if source_ok and target_ok:
        print("\n🎉 All connections successful! You can proceed with migration.")
        print("\nTo run the migration:")
        print("1. Using config file: python odoo_migrator_enhanced.py --config config.json")
        print("2. Using command line: python odoo_migrator_enhanced.py --source-url ... --target-url ...")
    else:
        print("\n❌ Some connections failed. Please check your configuration and try again.")
        print("\nCommon issues:")
        print("- Verify Odoo instances are running")
        print("- Check URLs and database names")
        print("- Ensure XML-RPC is enabled")
        print("- Verify username and password")
    
    # Save test results
    test_results = {
        'timestamp': datetime.now().isoformat(),
        'source_connection': source_ok,
        'target_connection': target_ok,
        'source_models': source_models if source_ok else {},
        'target_models': target_models if target_ok else {}
    }
    
    with open('test_results.json', 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\n📄 Test results saved to: test_results.json")


if __name__ == '__main__':
    main()
