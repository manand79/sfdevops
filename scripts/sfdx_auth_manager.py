#!/usr/bin/env python3
"""
SFDX/SF Authentication Manager
Handles OAuth and credential-based authentication to Salesforce orgs
Supports multiple authentication methods
"""

import os
import sys
import argparse
import subprocess
import json
import shutil
from pathlib import Path
import logging
from typing import Optional, Dict, Any, List


class SFDXAuthManager:
    """
    Manages Salesforce CLI authentication to Salesforce organizations
    """

    def __init__(self, workspace: str, org_alias: str, org_username: str):
        self.workspace = Path(workspace)
        self.org_alias = org_alias
        self.org_username = org_username
        self.sfdx_folder = Path.home() / '.sfdx'
        self.logger = self._setup_logger()
        self.cli_cmd = self._resolve_cli()

    def _setup_logger(self) -> logging.Logger:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.workspace / 'sfdx_auth_manager.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)

    def _resolve_cli(self) -> str:
        """
        Resolve Salesforce CLI executable in this order:
        1) sf in PATH
        2) sfdx in PATH
        3) Windows fallback %APPDATA%\\npm\\sf.cmd
        """
        sf = shutil.which('sf')
        if sf:
            self.logger.info(f"Using Salesforce CLI: {sf}")
            return sf

        sfdx = shutil.which('sfdx')
        if sfdx:
            self.logger.info(f"Using SFDX CLI: {sfdx}")
            return sfdx

        appdata = os.environ.get('APPDATA')
        if appdata:
            sf_cmd = Path(appdata) / 'npm' / 'sf.cmd'
            if sf_cmd.exists():
                self.logger.info(f"Using Salesforce CLI fallback: {sf_cmd}")
                return str(sf_cmd)

        raise FileNotFoundError(
            "Salesforce CLI not found. Expected 'sf' or 'sfdx' in PATH, "
            "or '%APPDATA%\\npm\\sf.cmd' on Windows."
        )

    def _run_cmd(self, args: List[str], env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
        cmd = [self.cli_cmd] + args
        self.logger.info(f"Executing command: {' '.join(cmd)}")
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env
        )

    def authenticate_oauth(
        self,
        client_id: str,
        client_secret: str,
        auth_url: str = 'https://login.salesforce.com'
    ) -> bool:
        try:
            self.logger.info(f"Starting OAuth authentication for {self.org_username}")

            # Prefer modern sf command
            if 'sf' in Path(self.cli_cmd).name.lower():
                args = [
                    'org', 'login', 'web',
                    '--instance-url', auth_url,
                    '--client-id', client_id,
                    '--alias', self.org_alias,
                    '--json'
                ]
            else:
                args = [
                    'force:auth:web:login',
                    '--instance-url', auth_url,
                    '--client-id', client_id,
                    '--alias', self.org_alias,
                    '--json'
                ]

            result = self._run_cmd(args)

            if result.returncode == 0:
                self.logger.info(f"OAuth authentication successful for {self.org_alias}")
                return True
            else:
                self.logger.error(f"OAuth authentication failed: {result.stderr or result.stdout}")
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
        try:
            self.logger.info(f"Starting JWT authentication for {self.org_username}")

            if not Path(jwt_key_file).exists():
                self.logger.error(f"JWT key file not found: {jwt_key_file}")
                return False

            if 'sf' in Path(self.cli_cmd).name.lower():
                args = [
                    'org', 'login', 'jwt',
                    '--client-id', client_id,
                    '--jwt-key-file', jwt_key_file,
                    '--username', self.org_username,
                    '--instance-url', auth_url,
                    '--alias', self.org_alias,
                    '--json'
                ]
            else:
                args = [
                    'force:auth:jwt:grant',
                    '--client-id', client_id,
                    '--jwt-key-file', jwt_key_file,
                    '--username', self.org_username,
                    '--instance-url', auth_url,
                    '--alias', self.org_alias,
                    '--json'
                ]

            result = self._run_cmd(args)

            if result.returncode == 0:
                self.logger.info(f"JWT authentication successful for {self.org_alias}")
                return True
            else:
                self.logger.error(f"JWT authentication failed: {result.stderr or result.stdout}")
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
        try:
            self.logger.info(f"Starting credential-based authentication for {username}")
            _ = f"{password}{security_token}"  # retained for parity if future command uses it

            # Note: web login is interactive; kept as-is for compatibility
            if 'sf' in Path(self.cli_cmd).name.lower():
                args = [
                    'org', 'login', 'web',
                    '--instance-url', auth_url,
                    '--alias', self.org_alias,
                    '--json'
                ]
            else:
                args = [
                    'force:auth:web:login',
                    '--instance-url', auth_url,
                    '--alias', self.org_alias,
                    '--json'
                ]

            env = os.environ.copy()
            env['SFDX_USE_GENERIC_UNIX_KEYCHAIN'] = 'true'

            result = self._run_cmd(args, env=env)

            if result.returncode == 0:
                self.logger.info(f"Credential authentication successful for {self.org_alias}")
                return True
            else:
                self.logger.error(f"Credential authentication failed: {result.stderr or result.stdout}")
                return False

        except Exception as e:
            self.logger.error(f"Error during credential authentication: {str(e)}")
            return False

    def verify_authentication(self) -> bool:
        try:
            self.logger.info(f"Verifying authentication for {self.org_alias}")

            if 'sf' in Path(self.cli_cmd).name.lower():
                args = ['org', 'list', '--json']
            else:
                args = ['force:org:list', '--json']

            result = self._run_cmd(args)

            if result.returncode == 0:
                org_list = json.loads(result.stdout)
                data = org_list.get('result', {})

                # sf shape
                authenticated_orgs = (
                    data.get('nonScratchOrgs', [])
                    or data.get('sandboxes', [])
                    or data.get('other', [])
                )

                # fallback: flatten any list values
                if not authenticated_orgs:
                    for v in data.values():
                        if isinstance(v, list):
                            authenticated_orgs.extend(v)

                for org in authenticated_orgs:
                    if org.get('alias') == self.org_alias or org.get('username') == self.org_username:
                        self.logger.info(f"Organization {self.org_alias} is authenticated and accessible")
                        return True

                self.logger.warning(f"Organization {self.org_alias} not found in authenticated orgs")
                return False
            else:
                self.logger.error(f"Failed to verify authentication: {result.stderr or result.stdout}")
                return False

        except Exception as e:
            self.logger.error(f"Error verifying authentication: {str(e)}")
            return False

    def get_org_info(self) -> Optional[Dict[str, Any]]:
        try:
            if 'sf' in Path(self.cli_cmd).name.lower():
                args = ['org', 'display', '--target-org', self.org_alias, '--json']
            else:
                args = ['force:org:display', '--target-org', self.org_alias, '--json']

            result = self._run_cmd(args)

            if result.returncode == 0:
                org_info = json.loads(result.stdout)
                self.logger.info(f"Retrieved org info for {self.org_alias}")
                return org_info.get('result', {})
            else:
                self.logger.error(f"Failed to get org info: {result.stderr or result.stdout}")
                return None

        except Exception as e:
            self.logger.error(f"Error getting org info: {str(e)}")
            return None

    def revoke_authentication(self) -> bool:
        try:
            self.logger.info(f"Revoking authentication for {self.org_alias}")

            if 'sf' in Path(self.cli_cmd).name.lower():
                args = ['org', 'logout', '--target-org', self.org_alias, '--no-prompt']
            else:
                args = ['force:org:logout', '--target-org', self.org_alias, '--no-prompt']

            result = self._run_cmd(args)

            if result.returncode == 0:
                self.logger.info(f"Authentication revoked for {self.org_alias}")
                return True
            else:
                self.logger.warning(f"Failed to revoke authentication: {result.stderr or result.stdout}")
                return False

        except Exception as e:
            self.logger.error(f"Error revoking authentication: {str(e)}")
            return False


def main():
    parser = argparse.ArgumentParser(description='SFDX/SF Authentication Manager')
    parser.add_argument('--action', required=True, choices=['authenticate', 'verify', 'revoke', 'info'],
                        help='Action to perform')
    parser.add_argument('--org-username', required=True, help='Salesforce org username')
    parser.add_argument('--org-alias', required=True, help='Alias for the org')
    parser.add_argument('--workspace', required=True, help='Jenkins workspace directory')

    parser.add_argument('--client-id', help='OAuth client ID')
    parser.add_argument('--client-secret', help='OAuth client secret')
    parser.add_argument('--auth-type', default='oauth', choices=['oauth', 'jwt', 'credentials'],
                        help='Authentication type')

    parser.add_argument('--password', help='Salesforce password')
    parser.add_argument('--security-token', help='Salesforce security token')
    parser.add_argument('--jwt-key-file', help='Path to JWT key file')

    parser.add_argument('--auth-url', default='https://login.salesforce.com',
                        help='Salesforce auth URL')

    args = parser.parse_args()

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
            else:
                success = manager.authenticate_oauth(
                    client_id=args.client_id,
                    client_secret=args.client_secret,
                    auth_url=args.auth_url
                )

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
