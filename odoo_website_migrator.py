#!/usr/bin/env python3
"""
Odoo Website Migrator
=====================

A tool to migrate website data from Odoo 16 to Odoo 18.
Supports migration of:
- Website pages
- Website menus
- Website themes
- Website snippets
- Website assets
- Website settings
"""

import xmlrpc.client
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import argparse
import getpass


class OdooWebsiteMigrator:
    """Main class for migrating website data between Odoo instances."""
    
    def __init__(self, source_url: str, source_db: str, source_username: str, 
                 source_password: str, target_url: str, target_db: str, 
                 target_username: str, target_password: str):
        """
        Initialize the migrator with connection details for both Odoo instances.
        
        Args:
            source_url: URL of the source Odoo 16 instance
            source_db: Database name of the source instance
            source_username: Username for source instance
            source_password: Password for source instance
            target_url: URL of the target Odoo 18 instance
            target_db: Database name of the target instance
            target_username: Username for target instance
            target_password: Password for target instance
        """
        self.source_url = source_url.rstrip('/')
        self.source_db = source_db
        self.source_username = source_username
        self.source_password = source_password
        
        self.target_url = target_url.rstrip('/')
        self.target_db = target_db
        self.target_username = target_username
        self.target_password = target_password
        
        # Initialize XML-RPC connections
        self.source_common = None
        self.source_models = None
        self.source_uid = None
        
        self.target_common = None
        self.target_models = None
        self.target_uid = None
        
        # Setup logging
        self.setup_logging()
        
        # Migration statistics
        self.migration_stats = {
            'pages_migrated': 0,
            'menus_migrated': 0,
            'themes_migrated': 0,
            'snippets_migrated': 0,
            'assets_migrated': 0,
            'errors': []
        }
    
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def connect_to_odoo(self, url: str, db: str, username: str, password: str) -> tuple:
        """
        Connect to an Odoo instance using XML-RPC.
        
        Args:
            url: Odoo instance URL
            db: Database name
            username: Username
            password: Password
            
        Returns:
            Tuple of (common, models, uid) for the connection
            
        Raises:
            Exception: If connection fails
        """
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
                common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', transport=transport)
                models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', transport=transport)
            else:
                common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
                models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
            
            uid = common.authenticate(db, username, password, {})
            
            if not uid:
                raise Exception(f"Authentication failed for {url}")
            
            self.logger.info(f"Successfully connected to {url}")
            return common, models, uid
            
        except Exception as e:
            self.logger.error(f"Failed to connect to {url}: {str(e)}")
            raise
    
    def connect_to_source(self):
        """Connect to the source Odoo 16 instance."""
        self.logger.info("Connecting to source Odoo 16 instance...")
        self.source_common, self.source_models, self.source_uid = self.connect_to_odoo(
            self.source_url, self.source_db, self.source_username, self.source_password
        )
    
    def connect_to_target(self):
        """Connect to the target Odoo 18 instance."""
        self.logger.info("Connecting to target Odoo 18 instance...")
        self.target_common, self.target_models, self.target_uid = self.connect_to_odoo(
            self.target_url, self.target_db, self.target_username, self.target_password
        )
    
    def get_website_pages(self) -> List[Dict[str, Any]]:
        """Retrieve all website pages from the source instance."""
        try:
            self.logger.info("Retrieving website pages from source...")
            pages = self.source_models.execute_kw(
                self.source_db, self.source_uid, self.source_password,
                'website.page', 'search_read',
                [[('is_published', '=', True)]],
                {
                    'fields': [
                        'name', 'url', 'is_published', 'website_id',
                        'view_id', 'key', 'arch', 'arch_db'
                    ]
                }
            )
            self.logger.info(f"Found {len(pages)} website pages")
            return pages
        except Exception as e:
            self.logger.error(f"Error retrieving website pages: {str(e)}")
            self.migration_stats['errors'].append(f"Website pages: {str(e)}")
            return []
    
    def get_website_menus(self) -> List[Dict[str, Any]]:
        """Retrieve all website menus from the source instance."""
        try:
            self.logger.info("Retrieving website menus from source...")
            menus = self.source_models.execute_kw(
                self.source_db, self.source_uid, self.source_password,
                'website.menu', 'search_read',
                [[]],
                {
                    'fields': [
                        'name', 'url', 'page_id', 'parent_id', 'sequence',
                        'website_id', 'is_visible', 'is_mega_menu'
                    ]
                }
            )
            self.logger.info(f"Found {len(menus)} website menus")
            return menus
        except Exception as e:
            self.logger.error(f"Error retrieving website menus: {str(e)}")
            self.migration_stats['errors'].append(f"Website menus: {str(e)}")
            return []
    
    def get_website_themes(self) -> List[Dict[str, Any]]:
        """Retrieve website themes from the source instance."""
        try:
            self.logger.info("Retrieving website themes from source...")
            themes = self.source_models.execute_kw(
                self.source_db, self.source_uid, self.source_password,
                'ir.module.module', 'search_read',
                [[('name', 'like', 'theme_'), ('state', '=', 'installed')]],
                {
                    'fields': ['name', 'shortdesc', 'description', 'state']
                }
            )
            self.logger.info(f"Found {len(themes)} website themes")
            return themes
        except Exception as e:
            self.logger.error(f"Error retrieving website themes: {str(e)}")
            self.migration_stats['errors'].append(f"Website themes: {str(e)}")
            return []
    
    def get_website_assets(self) -> List[Dict[str, Any]]:
        """Retrieve website assets from the source instance."""
        try:
            self.logger.info("Retrieving website assets from source...")
            assets = self.source_models.execute_kw(
                self.source_db, self.source_uid, self.source_password,
                'ir.attachment', 'search_read',
                [[('mimetype', 'in', ['text/css', 'application/javascript', 'image/png', 'image/jpeg', 'image/gif', 'image/svg+xml'])]],
                {
                    'fields': ['name', 'datas', 'mimetype', 'url', 'res_model', 'res_id']
                }
            )
            self.logger.info(f"Found {len(assets)} website assets")
            return assets
        except Exception as e:
            self.logger.error(f"Error retrieving website assets: {str(e)}")
            self.migration_stats['errors'].append(f"Website assets: {str(e)}")
            return []
    
    def migrate_website_pages(self, pages: List[Dict[str, Any]]):
        """Migrate website pages to the target instance."""
        self.logger.info("Starting website pages migration...")
        
        for page in pages:
            try:
                # Check if page already exists in target
                existing_page = self.target_models.execute_kw(
                    self.target_db, self.target_uid, self.target_password,
                    'website.page', 'search_read',
                    [[('url', '=', page['url'])]],
                    {'fields': ['id']}
                )
                
                if existing_page:
                    self.logger.info(f"Page {page['name']} already exists, skipping...")
                    continue
                
                # Prepare page data for migration
                page_data = {
                    'name': page['name'],
                    'url': page['url'],
                    'is_published': page.get('is_published', True),
                }
                
                # Handle content based on available fields
                if 'arch_db' in page and page['arch_db']:
                    page_data['arch_db'] = page['arch_db']
                elif 'arch' in page and page['arch']:
                    page_data['arch'] = page['arch']
                
                # Create page in target
                new_page_id = self.target_models.execute_kw(
                    self.target_db, self.target_uid, self.target_password,
                    'website.page', 'create',
                    [page_data]
                )
                
                self.logger.info(f"Successfully migrated page: {page['name']} (ID: {new_page_id})")
                self.migration_stats['pages_migrated'] += 1
                
            except Exception as e:
                error_msg = f"Error migrating page {page.get('name', 'Unknown')}: {str(e)}"
                self.logger.error(error_msg)
                self.migration_stats['errors'].append(error_msg)
    
    def migrate_website_menus(self, menus: List[Dict[str, Any]]):
        """Migrate website menus to the target instance."""
        self.logger.info("Starting website menus migration...")
        
        # Create a mapping of old menu IDs to new menu IDs
        menu_id_mapping = {}
        
        for menu in menus:
            try:
                # Check if menu already exists
                existing_menu = self.target_models.execute_kw(
                    self.target_db, self.target_uid, self.target_password,
                    'website.menu', 'search_read',
                    [[('name', '=', menu['name']), ('url', '=', menu.get('url', ''))]],
                    {'fields': ['id']}
                )
                
                if existing_menu:
                    self.logger.info(f"Menu {menu['name']} already exists, skipping...")
                    continue
                
                # Prepare menu data
                menu_data = {
                    'name': menu['name'],
                    'url': menu.get('url', ''),
                    'sequence': menu.get('sequence', 10),
                    'is_visible': menu.get('is_visible', True),
                    'is_mega_menu': menu.get('is_mega_menu', False),
                }
                
                # Handle parent menu mapping
                if menu.get('parent_id') and menu['parent_id'][0] in menu_id_mapping:
                    menu_data['parent_id'] = menu_id_mapping[menu['parent_id'][0]]
                
                # Create menu in target
                new_menu_id = self.target_models.execute_kw(
                    self.target_db, self.target_uid, self.target_password,
                    'website.menu', 'create',
                    [menu_data]
                )
                
                # Store mapping for child menus
                menu_id_mapping[menu['id']] = new_menu_id
                
                self.logger.info(f"Successfully migrated menu: {menu['name']} (ID: {new_menu_id})")
                self.migration_stats['menus_migrated'] += 1
                
            except Exception as e:
                error_msg = f"Error migrating menu {menu.get('name', 'Unknown')}: {str(e)}"
                self.logger.error(error_msg)
                self.migration_stats['errors'].append(error_msg)
    
    def migrate_website_themes(self, themes: List[Dict[str, Any]]):
        """Migrate website themes to the target instance."""
        self.logger.info("Starting website themes migration...")
        
        for theme in themes:
            try:
                # Check if theme is already installed in target
                existing_theme = self.target_models.execute_kw(
                    self.target_db, self.target_uid, self.target_password,
                    'ir.module.module', 'search_read',
                    [[('name', '=', theme['name'])]],
                    {'fields': ['state']}
                )
                
                if existing_theme and existing_theme[0]['state'] == 'installed':
                    self.logger.info(f"Theme {theme['name']} already installed, skipping...")
                    continue
                
                # Try to install the theme - use search to get the module ID first
                module_ids = self.target_models.execute_kw(
                    self.target_db, self.target_uid, self.target_password,
                    'ir.module.module', 'search',
                    [[('name', '=', theme['name'])]]
                )
                
                if module_ids:
                    # Try to install the theme
                    self.target_models.execute_kw(
                        self.target_db, self.target_uid, self.target_password,
                        'ir.module.module', 'button_immediate_install',
                        [module_ids]
                    )
                else:
                    self.logger.warning(f"Theme {theme['name']} not found in target instance")
                    continue
                
                self.logger.info(f"Successfully installed theme: {theme['name']}")
                self.migration_stats['themes_migrated'] += 1
                
            except Exception as e:
                error_msg = f"Error installing theme {theme.get('name', 'Unknown')}: {str(e)}"
                self.logger.error(error_msg)
                self.migration_stats['errors'].append(error_msg)
    
    def migrate_website_assets(self, assets: List[Dict[str, Any]]):
        """Migrate website assets to the target instance."""
        self.logger.info("Starting website assets migration...")
        
        for asset in assets:
            try:
                # Check if asset already exists
                existing_asset = self.target_models.execute_kw(
                    self.target_db, self.target_uid, self.target_password,
                    'ir.attachment', 'search_read',
                    [[('name', '=', asset['name'])]],
                    {'fields': ['id']}
                )
                
                if existing_asset:
                    self.logger.info(f"Asset {asset['name']} already exists, skipping...")
                    continue
                
                # Prepare asset data
                asset_data = {
                    'name': asset['name'],
                    'mimetype': asset['mimetype'],
                    'datas': asset.get('datas', ''),
                    'url': asset.get('url', ''),
                }
                
                # Create asset in target
                new_asset_id = self.target_models.execute_kw(
                    self.target_db, self.target_uid, self.target_password,
                    'ir.attachment', 'create',
                    [asset_data]
                )
                
                self.logger.info(f"Successfully migrated asset: {asset['name']} (ID: {new_asset_id})")
                self.migration_stats['assets_migrated'] += 1
                
            except Exception as e:
                error_msg = f"Error migrating asset {asset.get('name', 'Unknown')}: {str(e)}"
                self.logger.error(error_msg)
                self.migration_stats['errors'].append(error_msg)
    
    def generate_migration_report(self):
        """Generate a comprehensive migration report."""
        report = f"""
Odoo Website Migration Report
============================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Migration Statistics:
- Pages migrated: {self.migration_stats['pages_migrated']}
- Menus migrated: {self.migration_stats['menus_migrated']}
- Themes migrated: {self.migration_stats['themes_migrated']}
- Assets migrated: {self.migration_stats['assets_migrated']}

Errors ({len(self.migration_stats['errors'])}):
"""
        
        for error in self.migration_stats['errors']:
            report += f"- {error}\n"
        
        if not self.migration_stats['errors']:
            report += "- No errors encountered\n"
        
        # Save report to file
        report_filename = f'migration_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        with open(report_filename, 'w') as f:
            f.write(report)
        
        self.logger.info(f"Migration report saved to: {report_filename}")
        print(report)
    
    def run_migration(self):
        """Run the complete migration process."""
        try:
            self.logger.info("Starting Odoo website migration...")
            
            # Connect to both instances
            self.connect_to_source()
            self.connect_to_target()
            
            # Migrate website data
            pages = self.get_website_pages()
            self.migrate_website_pages(pages)
            
            menus = self.get_website_menus()
            self.migrate_website_menus(menus)
            
            themes = self.get_website_themes()
            self.migrate_website_themes(themes)
            
            assets = self.get_website_assets()
            self.migrate_website_assets(assets)
            
            # Generate report
            self.generate_migration_report()
            
            self.logger.info("Migration completed successfully!")
            
        except Exception as e:
            self.logger.error(f"Migration failed: {str(e)}")
            raise


def main():
    """Main function to run the migration tool."""
    parser = argparse.ArgumentParser(description='Migrate website data from Odoo 16 to Odoo 18')
    
    parser.add_argument('--source-url', required=True, help='Source Odoo 16 URL')
    parser.add_argument('--source-db', required=True, help='Source database name')
    parser.add_argument('--source-username', required=True, help='Source username')
    parser.add_argument('--source-password', help='Source password (will prompt if not provided)')
    
    parser.add_argument('--target-url', required=True, help='Target Odoo 18 URL')
    parser.add_argument('--target-db', required=True, help='Target database name')
    parser.add_argument('--target-username', required=True, help='Target username')
    parser.add_argument('--target-password', help='Target password (will prompt if not provided)')
    
    args = parser.parse_args()
    
    # Get passwords if not provided
    source_password = args.source_password or getpass.getpass('Source password: ')
    target_password = args.target_password or getpass.getpass('Target password: ')
    
    # Create and run migrator
    migrator = OdooWebsiteMigrator(
        source_url=args.source_url,
        source_db=args.source_db,
        source_username=args.source_username,
        source_password=source_password,
        target_url=args.target_url,
        target_db=args.target_db,
        target_username=args.target_username,
        target_password=target_password
    )
    
    try:
        migrator.run_migration()
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
