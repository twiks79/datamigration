# OneDrive Migration Tool

This tool helps you migrate your OneDrive data from one Microsoft account to another.

## Prerequisites

1. Python 3.6 or higher
2. A registered application in Azure AD with the following permissions:
   - Files.ReadWrite.All
   - User.Read

## Setup

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Register an application in Azure AD:
   - Go to https://portal.azure.com
   - Navigate to "Azure Active Directory" > "App registrations"
   - Click "New registration"
   - Enter a name for your application
   - Select "Accounts in any organizational directory (Any Azure AD directory - Multitenant)"
   - Click "Register"
   - Note down the "Application (client) ID"
   - Under "API permissions", add the following permissions:
     - Microsoft Graph > Delegated permissions > Files.ReadWrite.All
     - Microsoft Graph > Delegated permissions > User.Read
   - Click "Grant admin consent"

3. Set up environment variables:
   ```bash
   export ONEDRIVE_CLIENT_ID="your_client_id_here"
   ```

## Usage

1. Run the script:
   ```bash
   python onedrive_migration.py
   ```

2. When prompted:
   - Enter the password for your source account
   - Enter the password for your destination account
   - Enter the destination folder name (optional, press Enter for root folder)

The script will:
- Download files from your source OneDrive account
- Upload them to your destination OneDrive account
- Maintain the same folder structure
- Clean up temporary files after completion
- Generate a verification report

## Features

- **Resume Capability**: If the migration is interrupted, it can be resumed from where it left off
- **Progress Tracking**: Saves progress in `migration_progress.json`
- **Verification**: Verifies each file after migration and generates a detailed report
- **Error Handling**: Retries failed operations with exponential backoff
- **Logging**: Detailed logs are saved to `migration.log`

## Files Generated

- `migration.log`: Contains detailed logs of the migration process
- `migration_progress.json`: Tracks progress and failed files
- `migration_verification_TIMESTAMP.txt`: Contains verification report

## Notes

- The script uses a temporary directory to store files during migration
- Progress is shown with a progress bar
- Make sure you have enough free space on your computer for the temporary files
- Passwords are not stored and are only used for authentication
- The Client ID should be kept secure and not shared 