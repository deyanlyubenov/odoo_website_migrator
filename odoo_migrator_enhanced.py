#!/usr/bin/env python3
"""
Enhanced Odoo Website Migrator
==============================

An enhanced tool to migrate website data from Odoo 16 to Odoo 18.
Supports configuration files and additional migration features.
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
import shutil


class EnhancedOdooWebsiteMigrator:
    """Enhanced migrator with configuration file support and additional features."""
    
    def __init__(self, config_file: str = None, **kwargs):
        """
        Initialize the migrator with configuration file or direct parameters.
        
        Args:
            config_file: Path to configuration JSON file
            **kwargs: Direct connection parameters (overrides config file)
        """
        self.config = self.load_config(config_file) if config_file else {}
        
        # Override config with direct parameters
        for key, value in kwargs.items():
            if value is not None:
                if '.' in key:
                    section, param = key.split('.', 1)
                    if section not in self.config:
                        self.config[section] = {}
                    self.config[section][param] = value
                else:
                    self.config[key] = value
        
        # Initialize connection parameters
        self.source_url = self.config.get('source', {}).get('url', '').rstrip('/')
        self.source_db = self.config.get('source', {}).get('database', '')
        self.source_username = self.config.get('source', {}).get('username', '')
        self.source_password = self.config.get('source', {}).get('password', '')
        
        self.target_url = self.config.get('target', {}).get('url', '').rstrip('/')
        self.target_db = self.config.get('target', {}).get('database', '')
        self.target_username = self.config.get('target', {}).get('username', '')
        self.target_password = self.config.get('target', {}).get('password', '')
        
        # Migration options
        self.migration_options = self.config.get('migration_options', {})
        
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
            'websites_migrated': 0,
            'pages_migrated': 0,
            'menus_migrated': 0,
            'themes_migrated': 0,
            'snippets_migrated': 0,
            'assets_migrated': 0,
            'errors': []
        }
    
    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Failed to load configuration file {config_file}: {str(e)}")
    
    def setup_logging(self):
        """Setup logging configuration."""
        log_filename = f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def validate_connection_params(self):
        """Validate that all required connection parameters are provided."""
        required_params = [
            ('source_url', self.source_url),
            ('source_db', self.source_db),
            ('source_username', self.source_username),
            ('target_url', self.target_url),
            ('target_db', self.target_db),
            ('target_username', self.target_username),
        ]
        
        missing_params = [param for param, value in required_params if not value]
        if missing_params:
            raise ValueError(f"Missing required parameters: {', '.join(missing_params)}")
    
    def connect_to_odoo(self, url: str, db: str, username: str, password: str) -> tuple:
        """Connect to an Odoo instance using XML-RPC."""
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
    
    def get_website_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Retrieve all website data from the source instance."""
        data = {}
        
        if self.migration_options.get('migrate_websites', True):
            data['websites'] = self.get_websites()
        
        if self.migration_options.get('migrate_pages', True):
            data['pages'] = self.get_website_pages()
        
        if self.migration_options.get('migrate_menus', True):
            data['menus'] = self.get_website_menus()
        
        if self.migration_options.get('migrate_themes', True):
            data['themes'] = self.get_website_themes()
        
        if self.migration_options.get('migrate_assets', True):
            data['assets'] = self.get_website_assets()
        
        return data
    
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
    
    def get_websites(self) -> List[Dict[str, Any]]:
        """Retrieve all websites from the source instance."""
        try:
            self.logger.info("Retrieving websites from source...")
            websites = self.source_models.execute_kw(
                self.source_db, self.source_uid, self.source_password,
                'website', 'search_read',
                [[]],
                {
                    'fields': [
                        'name', 'domain', 'company_id', 'default_lang_id',
                        'social_twitter', 'social_facebook', 'social_github',
                        'social_linkedin', 'social_youtube', 'social_instagram',
                        'google_analytics_key', 'google_maps_api_key',
                        'cdn_activated', 'cdn_url', 'cdn_filters',
                        'favicon', 'logo', 'theme_id'
                    ]
                }
            )
            self.logger.info(f"Found {len(websites)} websites")
            return websites
        except Exception as e:
            self.logger.error(f"Error retrieving websites: {str(e)}")
            self.migration_stats['errors'].append(f"Websites: {str(e)}")
            return []
    
    def migrate_website_data(self, data: Dict[str, List[Dict[str, Any]]]):
        """Migrate all website data to the target instance."""
        if 'websites' in data:
            self.migrate_websites(data['websites'])
        
        if 'pages' in data:
            self.migrate_website_pages(data['pages'])
        
        if 'menus' in data:
            self.migrate_website_menus(data['menus'])
        
        if 'themes' in data:
            self.migrate_website_themes(data['themes'])
        
        if 'assets' in data:
            self.migrate_website_assets(data['assets'])
    
    def migrate_websites(self, websites: List[Dict[str, Any]]):
        """Migrate websites to the target instance."""
        self.logger.info("Starting websites migration...")
        
        for website in websites:
            try:
                # Check if website already exists
                if self.migration_options.get('skip_existing', True):
                    existing_website = self.target_models.execute_kw(
                        self.target_db, self.target_uid, self.target_password,
                        'website', 'search_read',
                        [[('name', '=', website['name'])]],
                        {'fields': ['id']}
                    )
                    
                    if existing_website:
                        self.logger.info(f"Website {website['name']} already exists, skipping...")
                        continue
                
                # Prepare website data for migration
                website_data = {
                    'name': website['name'],
                    'domain': website.get('domain', ''),
                    'social_twitter': website.get('social_twitter', ''),
                    'social_facebook': website.get('social_facebook', ''),
                    'social_github': website.get('social_github', ''),
                    'social_linkedin': website.get('social_linkedin', ''),
                    'social_youtube': website.get('social_youtube', ''),
                    'social_instagram': website.get('social_instagram', ''),
                    'google_analytics_key': website.get('google_analytics_key', ''),
                    'google_maps_api_key': website.get('google_maps_api_key', ''),
                    'cdn_activated': website.get('cdn_activated', False),
                    'cdn_url': website.get('cdn_url', ''),
                    'cdn_filters': website.get('cdn_filters', ''),
                }
                
                # Create website in target
                new_website_id = self.target_models.execute_kw(
                    self.target_db, self.target_uid, self.target_password,
                    'website', 'create',
                    [website_data]
                )
                
                self.logger.info(f"Successfully migrated website: {website['name']} (ID: {new_website_id})")
                self.migration_stats['websites_migrated'] += 1
                
                # Also migrate website settings and configurations
                self.migrate_website_settings(website, new_website_id)
                
            except Exception as e:
                error_msg = f"Error migrating website {website.get('name', 'Unknown')}: {str(e)}"
                self.logger.error(error_msg)
                self.migration_stats['errors'].append(error_msg)
    
    def migrate_website_settings(self, website: Dict[str, Any], new_website_id: int):
        """Migrate website settings and configurations."""
        try:
            self.logger.info(f"Migrating settings for website: {website['name']}")
            
            # Migrate website theme settings
            if website.get('theme_id'):
                try:
                    # Try to set the theme for the new website
                    self.target_models.execute_kw(
                        self.target_db, self.target_uid, self.target_password,
                        'website', 'write',
                        [[new_website_id], {'theme_id': website['theme_id'][0]}]
                    )
                    self.logger.info(f"Applied theme to website: {website['name']}")
                except Exception as e:
                    self.logger.warning(f"Could not apply theme to website {website['name']}: {str(e)}")
            
            # Migrate website configuration settings
            config_data = {
                'google_analytics_key': website.get('google_analytics_key', ''),
                'google_maps_api_key': website.get('google_maps_api_key', ''),
                'cdn_activated': website.get('cdn_activated', False),
                'cdn_url': website.get('cdn_url', ''),
                'cdn_filters': website.get('cdn_filters', ''),
            }
            
            # Update website with additional settings
            self.target_models.execute_kw(
                self.target_db, self.target_uid, self.target_password,
                'website', 'write',
                [[new_website_id], config_data]
            )
            
            self.logger.info(f"Successfully migrated settings for website: {website['name']}")
            
        except Exception as e:
            error_msg = f"Error migrating settings for website {website.get('name', 'Unknown')}: {str(e)}"
            self.logger.error(error_msg)
            self.migration_stats['errors'].append(error_msg)
    
    def migrate_website_pages(self, pages: List[Dict[str, Any]]):
        """Migrate website pages to the target instance."""
        self.logger.info("Starting website pages migration...")
        
        for page in pages:
            try:
                # Check if page already exists in target
                if self.migration_options.get('skip_existing', True):
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
                if self.migration_options.get('skip_existing', True):
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
                if self.migration_options.get('skip_existing', True):
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
                if self.migration_options.get('skip_existing', True):
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
Enhanced Odoo Website Migration Report
=====================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Source: {self.source_url} ({self.source_db})
Target: {self.target_url} ({self.target_db})

Migration Statistics:
- Websites migrated: {self.migration_stats['websites_migrated']}
- Pages migrated: {self.migration_stats['pages_migrated']}
- Menus migrated: {self.migration_stats['menus_migrated']}
- Themes migrated: {self.migration_stats['themes_migrated']}
- Assets migrated: {self.migration_stats['assets_migrated']}

Migration Options Used:
- Skip existing: {self.migration_options.get('skip_existing', True)}
- Migrate websites: {self.migration_options.get('migrate_websites', True)}
- Migrate pages: {self.migration_options.get('migrate_pages', True)}
- Migrate menus: {self.migration_options.get('migrate_menus', True)}
- Migrate themes: {self.migration_options.get('migrate_themes', True)}
- Migrate assets: {self.migration_options.get('migrate_assets', True)}

Errors ({len(self.migration_stats['errors'])}):
"""
        
        for error in self.migration_stats['errors']:
            report += f"- {error}\n"
        
        if not self.migration_stats['errors']:
            report += "- No errors encountered\n"
        
        # Save report to file
        report_filename = f'enhanced_migration_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        with open(report_filename, 'w') as f:
            f.write(report)
        
        self.logger.info(f"Migration report saved to: {report_filename}")
        print(report)
    
    def run_migration(self):
        """Run the complete migration process."""
        try:
            self.logger.info("Starting enhanced Odoo website migration...")
            
            # Validate connection parameters
            self.validate_connection_params()
            
            # Connect to both instances
            self.connect_to_source()
            self.connect_to_target()
            
            # Get website data from source
            data = self.get_website_data()
            
            # Migrate website data to target
            self.migrate_website_data(data)
            
            # Generate report
            self.generate_migration_report()
            
            self.logger.info("Migration completed successfully!")
            
        except Exception as e:
            self.logger.error(f"Migration failed: {str(e)}")
            raise


def main():
    """Main function to run the enhanced migration tool."""
    parser = argparse.ArgumentParser(description='Enhanced Odoo website migration tool')
    
    # Configuration file option
    parser.add_argument('--config', '-c', help='Configuration file path')
    
    # Direct connection parameters (overrides config file)
    parser.add_argument('--source-url', help='Source Odoo 16 URL')
    parser.add_argument('--source-db', help='Source database name')
    parser.add_argument('--source-username', help='Source username')
    parser.add_argument('--source-password', help='Source password')
    
    parser.add_argument('--target-url', help='Target Odoo 18 URL')
    parser.add_argument('--target-db', help='Target database name')
    parser.add_argument('--target-username', help='Target username')
    parser.add_argument('--target-password', help='Target password')
    
    # Migration options
    parser.add_argument('--no-skip-existing', action='store_true', help='Do not skip existing items')
    parser.add_argument('--no-pages', action='store_true', help='Skip page migration')
    parser.add_argument('--no-menus', action='store_true', help='Skip menu migration')
    parser.add_argument('--no-themes', action='store_true', help='Skip theme migration')
    parser.add_argument('--no-assets', action='store_true', help='Skip asset migration')
    
    args = parser.parse_args()
    
    # Prepare migration options
    migration_options = {
        'skip_existing': not args.no_skip_existing,
        'migrate_pages': not args.no_pages,
        'migrate_menus': not args.no_menus,
        'migrate_themes': not args.no_themes,
        'migrate_assets': not args.no_assets,
    }
    
    # Get passwords if not provided
    source_password = args.source_password or getpass.getpass('Source password: ')
    target_password = args.target_password or getpass.getpass('Target password: ')
    
    # Create and run migrator
    migrator = EnhancedOdooWebsiteMigrator(
        config_file=args.config,
        source_url=args.source_url,
        source_db=args.source_db,
        source_username=args.source_username,
        source_password=source_password,
        target_url=args.target_url,
        target_db=args.target_db,
        target_username=args.target_username,
        target_password=target_password,
        migration_options=migration_options
    )
    
    try:
        migrator.run_migration()
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
