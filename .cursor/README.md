# OneDrive Migration Project

## Project Purpose
This project is designed to migrate files from one OneDrive account to another, with the following features:
- Exclude specific folders (e.g., Z_Dropbox)
- Progress tracking and resume capability
- File verification after transfer
- Detailed logging and error reporting

## Current State
- Basic migration functionality is implemented
- Authentication using device code flow is working
- Configuration file (config.json) for exclusions is set up
- Progress tracking and verification are in place

## Next Steps
1. Test the migration with actual files
2. Implement retry mechanism for failed transfers
3. Add more robust error handling
4. Consider adding parallel processing for faster transfers
5. Add support for large file handling

## Configuration
The project uses:
- `config.json` for migration settings
- `.env` for authentication credentials
- `migration.log` for operation logs
- `migration_progress.json` for tracking progress

## Important Notes
- The script uses Microsoft Graph API for OneDrive operations
- Authentication requires proper app registration in Azure Portal
- Temporary files are stored in `temp_downloads` directory
- Progress is saved in `migration_progress.json` 