# Odoo Website Migrator

A comprehensive Python tool to migrate website data from Odoo 16 to Odoo 18. This tool provides an easy and reliable way to upgrade your Odoo website from the old version to the new one.

## Features

- **Website Pages Migration**: Migrate all published website pages with their content and structure
- **Website Menus Migration**: Transfer website navigation menus with proper hierarchy
- **Website Themes Migration**: Install and configure website themes
- **Website Assets Migration**: Transfer CSS, JavaScript, and image files
- **Configuration File Support**: Use JSON configuration files for easy setup
- **Comprehensive Logging**: Detailed logs and migration reports
- **Error Handling**: Robust error handling with detailed error reporting
- **Skip Existing Items**: Option to skip items that already exist in the target
- **Selective Migration**: Choose which components to migrate

## Requirements

- Python 3.7 or higher
- Network access to both Odoo 16 and Odoo 18 instances
- Valid credentials for both instances
- XML-RPC access enabled on both Odoo instances

## Installation

1. Clone or download this repository
2. Ensure you have Python 3.7+ installed
3. The tool uses only Python standard library modules, so no additional dependencies are required

## Usage

### Method 1: Using Configuration File (Recommended)

1. Edit the `config.json` file with your connection details:

```json
{
    "source": {
        "url": "http://your-odoo16-server:8069",
        "database": "your_odoo16_database",
        "username": "admin",
        "password": "your_password"
    },
    "target": {
        "url": "http://your-odoo18-server:8070",
        "database": "your_odoo18_database",
        "username": "admin",
        "password": "your_password"
    },
    "migration_options": {
        "migrate_pages": true,
        "migrate_menus": true,
        "migrate_themes": true,
        "migrate_assets": true,
        "skip_existing": true
    }
}
```

2. Run the enhanced migrator:

```bash
python odoo_migrator_enhanced.py --config config.json
```

### Method 2: Using Command Line Arguments

```bash
python odoo_migrator_enhanced.py \
    --source-url http://your-odoo16-server:8069 \
    --source-db your_odoo16_database \
    --source-username admin \
    --target-url http://your-odoo18-server:8070 \
    --target-db your_odoo18_database \
    --target-username admin
```

### Method 3: Using the Basic Migrator

```bash
python odoo_website_migrator.py \
    --source-url http://your-odoo16-server:8069 \
    --source-db your_odoo16_database \
    --source-username admin \
    --target-url http://your-odoo18-server:8070 \
    --target-db your_odoo18_database \
    --target-username admin
```

## Command Line Options

### Enhanced Migrator Options

- `--config, -c`: Path to configuration file
- `--source-url`: Source Odoo 16 URL
- `--source-db`: Source database name
- `--source-username`: Source username
- `--source-password`: Source password (will prompt if not provided)
- `--target-url`: Target Odoo 18 URL
- `--target-db`: Target database name
- `--target-username`: Target username
- `--target-password`: Target password (will prompt if not provided)

### Migration Control Options

- `--no-skip-existing`: Do not skip existing items (overwrite)
- `--no-pages`: Skip page migration
- `--no-menus`: Skip menu migration
- `--no-themes`: Skip theme migration
- `--no-assets`: Skip asset migration

## Configuration File Options

### Connection Settings

- `source.url`: URL of the source Odoo 16 instance
- `source.database`: Database name of the source instance
- `source.username`: Username for source instance
- `source.password`: Password for source instance
- `target.url`: URL of the target Odoo 18 instance
- `target.database`: Database name of the target instance
- `target.username`: Username for target instance
- `target.password`: Password for target instance

### Migration Options

- `migration_options.migrate_pages`: Enable/disable page migration (default: true)
- `migration_options.migrate_menus`: Enable/disable menu migration (default: true)
- `migration_options.migrate_themes`: Enable/disable theme migration (default: true)
- `migration_options.migrate_assets`: Enable/disable asset migration (default: true)
- `migration_options.skip_existing`: Skip items that already exist (default: true)

## What Gets Migrated

### Website Pages
- Page name and URL
- Page content (HTML/XML)
- Publication status
- Page templates and views

### Website Menus
- Menu name and URL
- Menu hierarchy (parent-child relationships)
- Menu visibility settings
- Menu sequence/order
- Mega menu settings

### Website Themes
- Installed theme modules
- Theme configurations
- Theme customizations

### Website Assets
- CSS files
- JavaScript files
- Images (PNG, JPEG, GIF, SVG)
- Other media files

## Output Files

The migration tool generates several output files:

1. **Migration Log**: `migration_YYYYMMDD_HHMMSS.log` - Detailed execution log
2. **Migration Report**: `enhanced_migration_report_YYYYMMDD_HHMMSS.txt` - Summary report
3. **Console Output**: Real-time progress and status information

## Example Migration Report

```
Enhanced Odoo Website Migration Report
=====================================
Generated: 2024-01-15 14:30:25

Source: http://localhost:8069 (odoo16_website)
Target: http://localhost:8070 (odoo18_website)

Migration Statistics:
- Pages migrated: 15
- Menus migrated: 8
- Themes migrated: 2
- Assets migrated: 45

Migration Options Used:
- Skip existing: True
- Migrate pages: True
- Migrate menus: True
- Migrate themes: True
- Migrate assets: True

Errors (0):
- No errors encountered
```

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Verify the URLs are correct and accessible
   - Check if XML-RPC is enabled on both Odoo instances
   - Ensure firewall allows connections to the specified ports

2. **Authentication Failed**
   - Verify username and password are correct
   - Ensure the user has sufficient permissions
   - Check if the database name is correct

3. **Permission Errors**
   - Ensure the user has access to website-related models
   - Check if the user has admin privileges or appropriate access rights

4. **Module Not Found**
   - Some themes or modules might not be available in Odoo 18
   - Check the Odoo 18 app store for compatible versions

### Debug Mode

For detailed debugging, you can modify the logging level in the script:

```python
logging.basicConfig(level=logging.DEBUG, ...)
```

### Manual Verification

After migration, verify the following in your Odoo 18 instance:

1. Check if all pages are accessible
2. Verify menu structure and navigation
3. Test theme functionality
4. Ensure all assets are loading correctly

## Security Considerations

- Store passwords securely and avoid hardcoding them in scripts
- Use HTTPS for production environments
- Consider using API keys or tokens instead of passwords
- Regularly update credentials and access permissions

## Limitations

- The tool migrates website data only, not business data
- Some custom modules might require manual migration
- Theme compatibility between Odoo versions may vary
- Large assets might take time to transfer

## Contributing

Feel free to contribute to this project by:

1. Reporting bugs and issues
2. Suggesting new features
3. Submitting pull requests
4. Improving documentation

## License

This project is open source and available under the MIT License.

## Support

For support and questions:

1. Check the troubleshooting section above
2. Review the migration logs for specific error messages
3. Ensure both Odoo instances are properly configured
4. Verify network connectivity and permissions

## Version History

- **v1.0**: Initial release with basic migration functionality
- **v1.1**: Enhanced version with configuration file support and improved error handling
- **v1.2**: Added selective migration options and comprehensive reporting
