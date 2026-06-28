#!/usr/bin/env python3
"""
Delta Package Manager
Handles creation of delta packages by comparing branches
Supports git operations for promotional branching strategy
"""

import os
import sys
import argparse
import subprocess
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
import xml.etree.ElementTree as ET
from xml.dom import minidom

class DeltaPackageManager:
    """
    Manages creation of delta packages for Salesforce deployments
    """
    
    def __init__(self, workspace: str, source_branch: str, target_branch: str, delta_output: str):
        """
        Initialize Delta Package Manager
        
        Args:
            workspace: Jenkins workspace directory
            source_branch: Source branch for comparison
            target_branch: Target branch for comparison
            delta_output: Output directory for delta package
        """
        self.workspace = Path(workspace)
        self.source_branch = source_branch
        self.target_branch = target_branch
        self.delta_output = Path(delta_output)
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """
        Setup logging configuration
        """
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.workspace / 'delta_package_manager.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def get_changed_files(self) -> List[str]:
        """
        Get list of changed files between branches
        
        Returns:
            List of changed file paths
        """
        try:
            self.logger.info(f"Comparing {self.source_branch} with {self.target_branch}")
            
            # Get diff between branches
            cmd = f"git diff --name-only origin/{self.target_branch}..origin/{self.source_branch}"
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=str(self.workspace),
                capture_output=True,
                text=True,
                check=True
            )
            
            changed_files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
            self.logger.info(f"Found {len(changed_files)} changed files")
            
            return changed_files
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to get changed files: {e.stderr}")
            raise
    
    def categorize_metadata(self, file_paths: List[str]) -> Dict[str, List[str]]:
        """
        Categorize files by Salesforce metadata type
        
        Args:
            file_paths: List of file paths to categorize
            
        Returns:
            Dictionary mapping metadata types to file lists
        """
        metadata_map = {
            'ApexClass': [],
            'ApexPage': [],
            'ApexComponent': [],
            'ApexTrigger': [],
            'StaticResource': [],
            'CustomObject': [],
            'CustomField': [],
            'Layout': [],
            'RecordType': [],
            'ValidationRule': [],
            'Workflow': [],
            'FlowDefinition': [],
            'LightningComponentBundle': [],
            'PermissionSet': [],
            'CustomApplication': [],
            'Document': [],
            'Email': [],
            'EmailTemplate': [],
            'LabelOrTranslation': [],
            'Report': [],
            'Dashboard': [],
            'List': []
        }
        
        # Extension to metadata type mapping
        ext_mapping = {
            '.cls': 'ApexClass',
            '.page': 'ApexPage',
            '.component': 'ApexComponent',
            '.trigger': 'ApexTrigger',
            '.resource': 'StaticResource',
            '.object': 'CustomObject',
            '.field': 'CustomField',
            '.layout': 'Layout',
            '.recordType': 'RecordType',
            '.validationRule': 'ValidationRule',
            '.workflow': 'Workflow',
            '.flow': 'FlowDefinition',
            '.js': 'LightningComponentBundle',
            '.permissionset': 'PermissionSet',
            '.app': 'CustomApplication',
            '.email': 'EmailTemplate',
            '.labels': 'LabelOrTranslation',
            '.report': 'Report',
            '.dashboard': 'Dashboard'
        }
        
        for file_path in file_paths:
            file_path = Path(file_path)
            
            # Skip non-metadata files
            if file_path.name.startswith('.'):
                continue
            
            # Check extension
            ext = file_path.suffix
            if ext in ext_mapping:
                metadata_type = ext_mapping[ext]
                metadata_map[metadata_type].append(str(file_path))
            elif 'force-app' in str(file_path) or 'src' in str(file_path):
                # Try to categorize by directory structure
                parts = file_path.parts
                if len(parts) > 1:
                    if parts[0] in ['force-app', 'src']:
                        type_dir = parts[1] if len(parts) > 1 else ''
                        if type_dir in metadata_map:
                            metadata_map[type_dir].append(str(file_path))
        
        self.logger.info(f"Categorized metadata types: {json.dumps({k: len(v) for k, v in metadata_map.items() if v})}")
        return metadata_map
    
    def create_package_xml(self, metadata_map: Dict[str, List[str]]) -> str:
        """
        Create package.xml for delta package
        
        Args:
            metadata_map: Dictionary of categorized metadata
            
        Returns:
            Path to generated package.xml
        """
        # Create delta package directory
        self.delta_output.mkdir(parents=True, exist_ok=True)
        
        # Create package.xml
        package_xml = self.delta_output / 'package.xml'
        
        # Create root element
        root = ET.Element('Package')
        root.set('xmlns', 'http://soap.sforce.com/2006/04/metadata')
        
        # Add members for each metadata type
        for metadata_type, files in metadata_map.items():
            if files:
                for file_path in files:
                    member = ET.SubElement(root, 'types')
                    
                    # Extract member name from file path
                    member_name = Path(file_path).stem
                    
                    name_elem = ET.SubElement(member, 'name')
                    name_elem.text = member_name
                    
                    type_elem = ET.SubElement(member, 'type')
                    type_elem.text = metadata_type
        
        # Add version
        version = ET.SubElement(root, 'version')
        version.text = '58.0'  # Adjust based on your Salesforce API version
        
        # Pretty print XML
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent='  ')
        # Remove XML declaration duplicate and extra blank lines
        xml_lines = [line for line in xml_str.split('\n') if line.strip()]
        xml_str = '\n'.join(xml_lines[1:])
        
        # Write to file
        with open(package_xml, 'w') as f:
            f.write(xml_str)
        
        self.logger.info(f"Created package.xml at {package_xml}")
        return str(package_xml)
    
    def copy_metadata_files(self, changed_files: List[str]) -> None:
        """
        Copy metadata files to delta package directory
        
        Args:
            changed_files: List of changed file paths
        """
        for file_path in changed_files:
            src = self.workspace / file_path
            if src.exists():
                # Maintain directory structure
                rel_path = Path(file_path).relative_to(Path(file_path).parts[0])
                dst = self.delta_output / rel_path
                
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                self.logger.info(f"Copied {file_path} to delta package")
            else:
                self.logger.warning(f"File not found: {file_path}")
    
    def prepare_package(self) -> bool:
        """
        Prepare complete delta package
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Starting delta package preparation...")
            
            # Get changed files
            changed_files = self.get_changed_files()
            
            if not changed_files:
                self.logger.warning("No changes found between branches")
                return False
            
            # Categorize metadata
            metadata_map = self.categorize_metadata(changed_files)
            
            # Create package.xml
            self.create_package_xml(metadata_map)
            
            # Copy metadata files
            self.copy_metadata_files(changed_files)
            
            self.logger.info("Delta package preparation completed successfully")
            return True
        
        except Exception as e:
            self.logger.error(f"Error preparing delta package: {str(e)}")
            return False
    
    def cleanup(self) -> None:
        """
        Clean up temporary files
        """
        try:
            self.logger.info("Cleaning up temporary files...")
            # Add cleanup logic if needed
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def main():
    """
    Main execution function
    """
    parser = argparse.ArgumentParser(
        description='Delta Package Manager for Salesforce Deployments'
    )
    parser.add_argument('--workspace', required=True, help='Jenkins workspace directory')
    parser.add_argument('--source-branch', required=True, help='Source branch')
    parser.add_argument('--target-branch', required=True, help='Target branch')
    parser.add_argument('--delta-output', required=True, help='Delta package output directory')
    parser.add_argument('--action', default='prepare', choices=['prepare', 'validate'], help='Action to perform')
    
    args = parser.parse_args()
    
    # Create manager instance
    manager = DeltaPackageManager(
        workspace=args.workspace,
        source_branch=args.source_branch,
        target_branch=args.target_branch,
        delta_output=args.delta_output
    )
    
    try:
        if args.action == 'prepare':
            success = manager.prepare_package()
            sys.exit(0 if success else 1)
    finally:
        manager.cleanup()


if __name__ == '__main__':
    main()
