# OneDrive Migration Tool

A Python-based tool for migrating files between OneDrive accounts with verification and progress tracking.

## Features
- Migrate files between OneDrive accounts
- Exclude specific folders from migration
- Progress tracking and resume capability
- File verification after transfer
- Detailed logging and error reporting
- Configurable settings via config.json

## Prerequisites
- Python 3.9 or higher
- Microsoft Azure app registration with proper permissions
- Access to both source and destination OneDrive accounts

## Installation
1. Clone this repository
2. Install dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```
3. Create a `.env` file with your Azure app credentials:
   ```
   ONEDRIVE_CLIENT_ID=your_client_id
   ```

## Configuration
Create a `config.json` file with the following structure:
```json
{
    "excluded_paths": [
        "Z_Dropbox"
    ],
    "batch_size": 10,
    "retry_attempts": 3,
    "verify_after_transfer": true
}
```

## Usage
1. Run the migration script:
   ```bash
   python3 onedrive_migration.py
   ```
2. Enter the destination folder name when prompted
3. Follow the authentication steps in your browser
4. Monitor progress in the console and migration.log

## Files
- `onedrive_migration.py`: Main migration script
- `config.json`: Migration settings
- `.env`: Authentication credentials
- `migration.log`: Operation logs
- `migration_progress.json`: Progress tracking
- `migration_verification_*.txt`: Verification reports

## Error Handling
The script includes:
- Automatic token refresh
- Retry mechanisms for failed operations
- Detailed error logging
- Progress saving for resuming interrupted migrations

## Development Status
- Basic functionality implemented
- Authentication working
- Configuration system in place
- Progress tracking operational

## Next Steps
1. Implement parallel processing
2. Add support for large files
3. Enhance error recovery
4. Add more configuration options
5. Improve progress reporting

## License
This project is licensed under the MIT License - see the LICENSE file for details. 