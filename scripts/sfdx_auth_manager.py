#!/usr/bin/env python3
"""
SFDX Authentication Manager
Handles OAuth and credential-based authentication to Salesforce orgs
Supports multiple authentication methods
"""

import os
import sys
import argparse
import subprocess
import json
import base64
from pathlib import Path
from datetime import datetime
import logging
from typing import Optional, Dict, Any

class SFDXAuthManager:
    """
    Manages SFDX authentication to Salesforce organizations
    """
    
    def __init__(self, workspace: str, org_alias: str, org_username: str):
        """
        Initialize SFDX Auth Manager
        
        Args:
            workspace: Jenkins workspace directory
            org_alias: Alias for the org in SFDX
            org_username: Username for the org
        """
        self.workspace = Path(workspace)
        self.org_alias = org_alias
        self.org_username = org_username
        self.sfdx_folder = Path.home() / '.sfdx'
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """
        Setup logging configuration
        
        Returns:
            Configured logger instance
        """
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.workspace / 'sfdx_auth_manager.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def authenticate_oauth(
        self,
        client_id: str,
        client_secret: str,
        auth_url: str = 'https://login.salesforce.com'
    ) -> bool:
        """
        Authenticate using OAuth flow
        
        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            auth_url: Salesforce auth URL
            
        Returns:
            True if authentication successful
        """
        try:
            self.logger.info(f"Starting OAuth authentication for {self.org_username}")
            
            cmd = [
                'sfdx',
                'force:auth:web:login',
                '--instance-url', auth_url,
                '--client-id', client_id,
                '--alias', self.org_alias,
                '--json'
            ]
            
            # Note: This is for non-interactive OAuth. For CI/CD, use JWT or client credentials
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.logger.info(f"OAuth authentication successful for {self.org_alias}")
                return True
            else:
                self.logger.error(f"OAuth authentication failed: {result.stderr}")
                return False
        
        except Exception as e:
            self.logger.error(f"Error during OAuth authentication: {str(e)}")
            return False
    
    def authenticate_jwt(
        self,
        client_id: str,
        jwt_key_file: str,
        auth_url: str = 'https://login.salesforce.com'
    ) -> bool:
        """
        Authenticate using JWT bearer flow (recommended for CI/CD)
        
        Args:
            client_id: OAuth client ID
            jwt_key_file: Path to JWT key file
            auth_url: Salesforce auth URL
            
        Returns:
            True if authentication successful
        """
        try:
            self.logger.info(f"Starting JWT authentication for {self.org_username}")
            
            # Verify JWT key file exists
            if not Path(jwt_key_file).exists():
                self.logger.error(f"JWT key file not found: {jwt_key_file}")
                return False
            
            cmd = [
                'sfdx',
                'force:auth:jwt:grant',
                '--client-id', client_id,
                '--jwt-key-file', jwt_key_file,
                '--username', self.org_username,
                '--instance-url', auth_url,
                '--alias', self.org_alias,
                '--json'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.logger.info(f"JWT authentication successful for {self.org_alias}")
                return True
            else:
                self.logger.error(f"JWT authentication failed: {result.stderr}")
                return False
        
        except Exception as e:
            self.logger.error(f"Error during JWT authentication: {str(e)}")
            return False
    
    def authenticate_credentials(
        self,
        username: str,
        password: str,
        security_token: str = '',
        auth_url: str = 'https://login.salesforce.com'
    ) -> bool:
        """
        Authenticate using username and password
        
        Args:
            username: Salesforce username
            password: Salesforce password
            security_token: Security token (if required)
            auth_url: Salesforce auth URL
            
        Returns:
            True if authentication successful
        """
        try:
            self.logger.info(f"Starting credential-based authentication for {username}")
            
            # Combine password and security token
            full_password = f"{password}{security_token}"
            
            cmd = [
                'sfdx',
                'force:auth:web:login',
                '--username', username,
                '--instance-url', auth_url,
                '--alias', self.org_alias,
                '--json'
            ]
            
            # Use environment variables for password (more secure)
            env = os.environ.copy()
            env['SFDX_USE_GENERIC_UNIX_KEYCHAIN'] = 'true'
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env
            )
            
            if result.returncode == 0:
                self.logger.info(f"Credential authentication successful for {self.org_alias}")
                return True
            else:
                self.logger.error(f"Credential authentication failed: {result.stderr}")
                return False
        
        except Exception as e:
            self.logger.error(f"Error during credential authentication: {str(e)}")
            return False
    
    def verify_authentication(self) -> bool:
        """
        Verify that org is authenticated and accessible
        
        Returns:
            True if org is accessible
        """
        try:
            self.logger.info(f"Verifying authentication for {self.org_alias}")
            
            cmd = [
                'sfdx',
                'force:org:list',
                '--json'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                org_list = json.loads(result.stdout)
                authenticated_orgs = org_list.get('result', {}).get('nonScratchOrgs', [])
                
                for org in authenticated_orgs:
                    if org.get('alias') == self.org_alias:
                        self.logger.info(f"Organization {self.org_alias} is authenticated and accessible")
                        return True
                
                self.logger.warning(f"Organization {self.org_alias} not found in authenticated orgs")
                return False
            else:
                self.logger.error(f"Failed to verify authentication: {result.stderr}")
                return False
        
        except Exception as e:
            self.logger.error(f"Error verifying authentication: {str(e)}")
            return False
    
    def get_org_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about authenticated org
        
        Returns:
            Dictionary with org information or None
        """
        try:
            cmd = [
                'sfdx',
                'force:org:display',
                '--target-org', self.org_alias,
                '--json'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                org_info = json.loads(result.stdout)
                self.logger.info(f"Retrieved org info for {self.org_alias}")
                return org_info.get('result', {})
            else:
                self.logger.error(f"Failed to get org info: {result.stderr}")
                return None
        
        except Exception as e:
            self.logger.error(f"Error getting org info: {str(e)}")
            return None
    
    def revoke_authentication(self) -> bool:
        """
        Revoke authentication for the org
        
        Returns:
            True if revocation successful
        """
        try:
            self.logger.info(f"Revoking authentication for {self.org_alias}")
            
            cmd = [
                'sfdx',
                'force:org:logout',
                '--target-org', self.org_alias,
                '--no-prompt'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.logger.info(f"Authentication revoked for {self.org_alias}")
                return True
            else:
                self.logger.warning(f"Failed to revoke authentication: {result.stderr}")
                return False
        
        except Exception as e:
            self.logger.error(f"Error revoking authentication: {str(e)}")
            return False


def main():
    """
    Main execution function
    """
    parser = argparse.ArgumentParser(
        description='SFDX Authentication Manager'
    )
    parser.add_argument('--action', required=True, choices=['authenticate', 'verify', 'revoke', 'info'],
                       help='Action to perform')
    parser.add_argument('--org-username', required=True, help='Salesforce org username')
    parser.add_argument('--org-alias', required=True, help='Alias for the org')
    parser.add_argument('--workspace', required=True, help='Jenkins workspace directory')
    
    # OAuth options
    parser.add_argument('--client-id', help='OAuth client ID')
    parser.add_argument('--client-secret', help='OAuth client secret')
    parser.add_argument('--auth-type', default='oauth', choices=['oauth', 'jwt', 'credentials'],
                       help='Authentication type')
    
    # Credentials options
    parser.add_argument('--password', help='Salesforce password')
    parser.add_argument('--security-token', help='Salesforce security token')
    parser.add_argument('--jwt-key-file', help='Path to JWT key file')
    
    # Auth URL
    parser.add_argument('--auth-url', default='https://login.salesforce.com',
                       help='Salesforce auth URL')
    
    args = parser.parse_args()
    
    # Create manager instance
    manager = SFDXAuthManager(
        workspace=args.workspace,
        org_alias=args.org_alias,
        org_username=args.org_username
    )
    
    try:
        if args.action == 'authenticate':
            if args.auth_type == 'jwt':
                if not args.jwt_key_file:
                    print("Error: --jwt-key-file required for JWT authentication")
                    sys.exit(1)
                success = manager.authenticate_jwt(
                    client_id=args.client_id,
                    jwt_key_file=args.jwt_key_file,
                    auth_url=args.auth_url
                )
            elif args.auth_type == 'credentials':
                if not args.password:
                    print("Error: --password required for credential authentication")
                    sys.exit(1)
                success = manager.authenticate_credentials(
                    username=args.org_username,
                    password=args.password,
                    security_token=args.security_token or '',
                    auth_url=args.auth_url
                )
            else:  # oauth
                success = manager.authenticate_oauth(
                    client_id=args.client_id,
                    client_secret=args.client_secret,
                    auth_url=args.auth_url
                )
            
            # Verify authentication
            if success:
                success = manager.verify_authentication()
            
            sys.exit(0 if success else 1)
        
        elif args.action == 'verify':
            success = manager.verify_authentication()
            sys.exit(0 if success else 1)
        
        elif args.action == 'revoke':
            success = manager.revoke_authentication()
            sys.exit(0 if success else 1)
        
        elif args.action == 'info':
            info = manager.get_org_info()
            if info:
                print(json.dumps(info, indent=2))
                sys.exit(0)
            else:
                sys.exit(1)
    
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
