#!/bin/bash

################################################################################
# Jenkins Credentials Setup Script
# This script configures all required credentials in Jenkins for Salesforce
# deployment pipeline
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Jenkins Credentials Setup ===${NC}"
echo ""

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check Jenkins CLI availability
if ! command -v jenkins-cli &> /dev/null; then
    print_error "jenkins-cli not found. Please install Jenkins CLI."
    exit 1
fi

print_info "Jenkins Credentials will be created via Jenkins Web UI or CLI."
echo ""

# List of credentials to create
echo -e "${BLUE}Required Credentials:${NC}"
echo ""

echo "1. Git Repository Credentials:"
echo "   - Credential ID: SFDEVOPS_GIT_CREDENTIALS"
echo "   - Type: Username with password"
echo "   - Username: Your GitHub username"
echo "   - Password: GitHub personal access token"
echo ""

echo "2. Git Configuration:"
echo "   - Credential ID: GIT_USER_EMAIL"
echo "   - Type: Secret text"
echo "   - Value: Your git email"
echo ""
echo "   - Credential ID: GIT_USER_NAME"
echo "   - Type: Secret text"
echo "   - Value: Your git name"
echo ""

echo "3. GitHub Repository URL:"
echo "   - Credential ID: SFDEVOPS_GIT_REPO"
echo "   - Type: Secret text"
echo "   - Value: https://github.com/manand79/sfdevops.git"
echo ""

echo "4. DEV Environment Credentials:"
echo "   - Credential ID: DEV_ORG_USERNAME"
echo "   - Type: Secret text"
echo "   - Value: Your DEV org username"
echo ""
echo "   - Credential ID: DEV_ORG_PASSWORD"
echo "   - Type: Secret text"
echo "   - Value: Your DEV org password"
echo ""
echo "   - Credential ID: DEV_SECURITY_TOKEN"
echo "   - Type: Secret text"
echo "   - Value: Your DEV org security token"
echo ""
echo "   - Credential ID: DEV_CLIENT_ID"
echo "   - Type: Secret text"
echo "   - Value: OAuth Client ID for DEV org"
echo ""
echo "   - Credential ID: DEV_CLIENT_SECRET"
echo "   - Type: Secret text"
echo "   - Value: OAuth Client Secret for DEV org"
echo ""

echo "5. QA Environment Credentials:"
echo "   - Credential ID: QA_ORG_USERNAME"
echo "   - Type: Secret text"
echo "   - Value: Your QA org username"
echo ""
echo "   - Credential ID: QA_ORG_PASSWORD"
echo "   - Type: Secret text"
echo "   - Value: Your QA org password"
echo ""
echo "   - Credential ID: QA_SECURITY_TOKEN"
echo "   - Type: Secret text"
echo "   - Value: Your QA org security token"
echo ""
echo "   - Credential ID: QA_CLIENT_ID"
echo "   - Type: Secret text"
echo "   - Value: OAuth Client ID for QA org"
echo ""
echo "   - Credential ID: QA_CLIENT_SECRET"
echo "   - Type: Secret text"
echo "   - Value: OAuth Client Secret for QA org"
echo ""

echo "6. Optional Credentials:"
echo "   - Credential ID: NPM_AUTH_TOKEN"
echo "   - Type: Secret text"
echo "   - Value: Your NPM authentication token (for PMD installation)"
echo ""

echo -e "${BLUE}=== Steps to Create Credentials ===${NC}"
echo ""
echo "Option 1: Via Jenkins Web UI"
echo "1. Go to Jenkins Dashboard"
echo "2. Click 'Manage Jenkins' > 'Manage Credentials'"
echo "3. Click 'System' > 'Global credentials (unrestricted)'"
echo "4. Click 'Add Credentials'"
echo "5. Select credential type and fill in details"
echo "6. Click 'Create'"
echo ""

echo "Option 2: Via Jenkins CLI"
echo "1. Use Jenkins CLI commands to create credentials"
echo "2. Example:"
echo "   jenkins-cli create-credentials-by-xml system::system 'CREDENTIAL_ID' < credential.xml"
echo ""

echo -e "${YELLOW}Important Notes:${NC}"
echo "- Use personal access tokens instead of passwords"
echo "- Keep credentials secure and never commit them to repository"
echo "- Rotate credentials regularly"
echo "- Use Salesforce OAuth for production environments"
echo ""

print_success "Credentials setup documentation completed."
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Create all required credentials in Jenkins"
echo "2. Verify credentials are accessible"
echo "3. Configure Salesforce Connected App for OAuth"
echo "4. Test pipeline with Validate Only mode first"
echo ""
