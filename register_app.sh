#!/bin/bash

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "Azure CLI is not installed. Please install it first:"
    echo "https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if user is logged in
if ! az account show &> /dev/null; then
    echo "Please log in to Azure CLI first:"
    echo "az login"
    exit 1
fi

# Register the application
echo "Registering OneDrive Migration application..."
APP_NAME="OneDriveMigration"
APP_ID=$(az ad app create \
    --display-name "$APP_NAME" \
    --sign-in-audience "AzureADandPersonalMicrosoftAccount" \
    --required-resource-accesses '[{"resourceAppId":"00000003-0000-0000-c000-000000000000","resourceAccess":[{"id":"e1fe6dd8-ba31-4d61-89e7-88639da4683d","type":"Scope"}]}]' \
    --query "appId" \
    --output tsv)

# Create a service principal
echo "Creating service principal..."
az ad sp create --id "$APP_ID"

# Grant admin consent
echo "Granting admin consent..."
az ad app permission admin-consent --id "$APP_ID"

echo "Application registration completed!"
echo "Your Client ID is: $APP_ID"
echo "Please update the CLIENT_ID in onedrive_migration.py with this value." 