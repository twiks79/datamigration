import os
import json
import hashlib
import requests
from msal import PublicClientApplication
from tqdm import tqdm
import time
from datetime import datetime
import logging

# Configuration
CLIENT_ID = os.getenv('ONEDRIVE_CLIENT_ID')  # Get Client ID from environment variable
if not CLIENT_ID:
    raise ValueError("Please set the ONEDRIVE_CLIENT_ID environment variable")
SCOPES = ["Files.ReadWrite.All", "User.Read"]
AUTHORITY = "https://login.microsoftonline.com/common"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)

class OneDriveMigration:
    def __init__(self, source_username, dest_username, dest_folder):
        self.source_username = source_username
        self.dest_username = dest_username
        self.dest_folder = dest_folder.strip('/')  # Remove leading/trailing slashes
        self.progress_file = 'migration_progress.json'
        self.migrated_files = self._load_progress()
        self.temp_dir = "temp_downloads"
        os.makedirs(self.temp_dir, exist_ok=True)

    def _load_progress(self):
        """Load progress from previous migration attempts"""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {'migrated_files': [], 'failed_files': []}

    def _save_progress(self):
        """Save migration progress"""
        with open(self.progress_file, 'w') as f:
            json.dump(self.migrated_files, f)

    def get_access_token(self, client_id, username, password):
        app = PublicClientApplication(client_id, authority=AUTHORITY)
        result = app.acquire_token_by_username_password(username, password, scopes=SCOPES)
        if not result.get("access_token"):
            raise Exception(f"Failed to get access token for {username}: {result.get('error_description')}")
        return result.get("access_token")

    def get_file_hash(self, access_token, item_id):
        """Get file hash from OneDrive"""
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        url = f"https://graph.microsoft.com/v1.0/me/drive/items/{item_id}"
        response = requests.get(url, headers=headers)
        file_info = response.json()
        return file_info.get('file', {}).get('hashes', {}).get('sha1Hash', '')

    def get_drive_items(self, access_token, path=""):
        """Get items from OneDrive with pagination support"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        items = []
        url = f"https://graph.microsoft.com/v1.0/me/drive/root:{path}:/children"
        
        while url:
            response = requests.get(url, headers=headers)
            data = response.json()
            items.extend(data.get('value', []))
            url = data.get('@odata.nextLink', None)
            
        return items

    def create_folder(self, access_token, path):
        """Create folder structure in destination"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        current_path = ""
        for folder in path.split('/'):
            if not folder:
                continue
            current_path = f"{current_path}/{folder}" if current_path else folder
            url = f"https://graph.microsoft.com/v1.0/me/drive/root:{current_path}"
            
            # Check if folder exists
            response = requests.get(url, headers=headers)
            if response.status_code == 404:
                # Create folder if it doesn't exist
                create_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{current_path}"
                requests.put(create_url, headers=headers, json={"folder": {}})

    def download_file(self, access_token, item, local_path):
        """Download file with retry mechanism"""
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        url = f"https://graph.microsoft.com/v1.0/me/drive/items/{item['id']}/content"
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, stream=True)
                response.raise_for_status()
                
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                with open(local_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                return True
            except Exception as e:
                if attempt == max_retries - 1:
                    logging.error(f"Failed to download {item['name']}: {str(e)}")
                    return False
                time.sleep(2 ** attempt)  # Exponential backoff

    def upload_file(self, access_token, local_path, remote_path):
        """Upload file with retry mechanism"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/octet-stream"
        }
        
        # Create the folder structure if it doesn't exist
        folder_path = os.path.dirname(remote_path)
        if folder_path:
            self.create_folder(access_token, folder_path)
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                url = f"https://graph.microsoft.com/v1.0/me/drive/root:{remote_path}:/content"
                with open(local_path, "rb") as f:
                    response = requests.put(url, headers=headers, data=f)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                if attempt == max_retries - 1:
                    logging.error(f"Failed to upload {local_path}: {str(e)}")
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff

    def verify_file_migration(self, source_token, dest_token, source_item, dest_path):
        """Verify if a file was migrated correctly"""
        source_hash = self.get_file_hash(source_token, source_item['id'])
        
        # Get destination file info
        headers = {
            "Authorization": f"Bearer {dest_token}"
        }
        url = f"https://graph.microsoft.com/v1.0/me/drive/root:{dest_path}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            dest_item = response.json()
            dest_hash = dest_item.get('file', {}).get('hashes', {}).get('sha1Hash', '')
            return source_hash == dest_hash
        return False

    def migrate_folder(self, source_token, dest_token, source_path="", relative_path=""):
        """Migrate folder contents with resume capability"""
        items = self.get_drive_items(source_token, source_path)
        
        for item in tqdm(items, desc=f"Processing {source_path or 'root'}"):
            item_path = f"{source_path}/{item['name']}" if source_path else item['name']
            relative_item_path = f"{relative_path}/{item['name']}" if relative_path else item['name']
            dest_item_path = f"{self.dest_folder}/{relative_item_path}" if self.dest_folder else relative_item_path

            if item.get("folder"):
                # Create folder in destination
                self.create_folder(dest_token, dest_item_path)
                # Recursively process folder contents
                self.migrate_folder(source_token, dest_token, item_path, relative_item_path)
            else:
                # Skip if file was already successfully migrated
                if item_path in self.migrated_files['migrated_files']:
                    logging.info(f"Skipping already migrated file: {item_path}")
                    continue

                # Download and upload file
                local_path = os.path.join(self.temp_dir, relative_item_path)
                if self.download_file(source_token, item, local_path):
                    upload_result = self.upload_file(dest_token, local_path, dest_item_path)
                    
                    if upload_result and self.verify_file_migration(source_token, dest_token, item, dest_item_path):
                        self.migrated_files['migrated_files'].append(item_path)
                        self._save_progress()
                    else:
                        self.migrated_files['failed_files'].append(item_path)
                        self._save_progress()
                        logging.error(f"Failed to verify migration of {item_path}")
                
                # Clean up temporary file
                if os.path.exists(local_path):
                    os.remove(local_path)

    def verify_complete_migration(self, source_token, dest_token):
        """Verify the entire migration"""
        logging.info("Starting complete migration verification...")
        
        def get_all_items(token, path=""):
            items = {}
            folder_contents = self.get_drive_items(token, path)
            
            for item in folder_contents:
                item_path = f"{path}/{item['name']}" if path else item['name']
                if item.get("folder"):
                    items.update(get_all_items(token, item_path))
                else:
                    items[item_path] = item
            
            return items

        # Get all files from source and destination
        source_items = get_all_items(source_token)
        dest_base = f"{self.dest_folder}/" if self.dest_folder else ""
        dest_items = get_all_items(dest_token, self.dest_folder)

        # Compare files
        verification_results = {
            'total_files': len(source_items),
            'verified_files': 0,
            'missing_files': [],
            'mismatched_files': []
        }

        for source_path, source_item in source_items.items():
            dest_path = f"{dest_base}{source_path}"
            if dest_path not in dest_items:
                verification_results['missing_files'].append(source_path)
            elif not self.verify_file_migration(source_token, dest_token, source_item, dest_path):
                verification_results['mismatched_files'].append(source_path)
            else:
                verification_results['verified_files'] += 1

        # Generate verification report
        report = (
            f"\nMigration Verification Report\n"
            f"===========================\n"
            f"Total files: {verification_results['total_files']}\n"
            f"Successfully verified: {verification_results['verified_files']}\n"
            f"Missing files: {len(verification_results['missing_files'])}\n"
            f"Mismatched files: {len(verification_results['mismatched_files'])}\n"
        )

        if verification_results['missing_files']:
            report += "\nMissing Files:\n" + "\n".join(verification_results['missing_files'])
        if verification_results['mismatched_files']:
            report += "\nMismatched Files:\n" + "\n".join(verification_results['mismatched_files'])

        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"migration_verification_{timestamp}.txt"
        with open(report_file, 'w') as f:
            f.write(report)

        logging.info(f"Verification report saved to: {report_file}")
        return verification_results['verified_files'] == verification_results['total_files']

def main():
    # Get credentials from user
    source_username = "juergenrichert@gmx.de"
    source_password = input("Enter password for juergenrichert@gmx.de: ")
    dest_username = "juergen@team-richert"
    dest_password = input("Enter password for juergen@team-richert: ")
    
    # Get destination folder
    dest_folder = input("Enter destination folder name (press Enter for root folder): ").strip()
    
    # Initialize migration
    migration = OneDriveMigration(source_username, dest_username, dest_folder)
    
    try:
        # Get access tokens
        logging.info("Authenticating with source account...")
        source_token = migration.get_access_token(CLIENT_ID, source_username, source_password)
        logging.info("Authenticating with destination account...")
        dest_token = migration.get_access_token(CLIENT_ID, dest_username, dest_password)
        
        # Create destination folder if specified
        if dest_folder:
            logging.info(f"Creating destination folder: {dest_folder}")
            migration.create_folder(dest_token, dest_folder)
        
        # Start migration
        logging.info("Starting migration...")
        migration.migrate_folder(source_token, dest_token)
        
        # Verify migration
        logging.info("Verifying migration...")
        if migration.verify_complete_migration(source_token, dest_token):
            logging.info("Migration completed and verified successfully!")
        else:
            logging.warning("Migration completed but verification found discrepancies. Check the verification report for details.")
            
    except Exception as e:
        logging.error(f"An error occurred during migration: {str(e)}")
    finally:
        # Clean up temporary directory
        if os.path.exists(migration.temp_dir):
            for root, dirs, files in os.walk(migration.temp_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(migration.temp_dir)

if __name__ == "__main__":
    main() 