#!/usr/bin/env python3
"""
APEX PMD Analysis Runner
Executes PMD analysis on Apex code in delta packages
Generates HTML reports with violations
"""

import os
import sys
import argparse
import subprocess
import json
from pathlib import Path
from datetime import datetime
import logging
from typing import Optional, List, Dict

class PMDAnalyzer:
    """
    Executes PMD analysis on Apex code
    """
    
    def __init__(self, workspace: str, delta_package: str, report_output: str):
        """
        Initialize PMD Analyzer
        
        Args:
            workspace: Jenkins workspace directory
            delta_package: Path to delta package with Apex code
            report_output: Path for output report
        """
        self.workspace = Path(workspace)
        self.delta_package = Path(delta_package)
        self.report_output = Path(report_output)
        self.logger = self._setup_logger()
        self.pmd_version = '6.55.0'  # Latest stable PMD version
    
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
                logging.FileHandler(self.workspace / 'pmd_analysis.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def install_pmd(self) -> bool:
        """
        Install or verify PMD installation
        
        Returns:
            True if PMD is available
        """
        try:
            # Check if PMD is already installed
            result = subprocess.run(
                ['pmd', '--version'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.logger.info(f"PMD is already installed: {result.stdout.strip()}")
                return True
            
            # Install PMD via npm
            self.logger.info("Installing PMD...")
            cmd = ['npm', 'install', '-g', f'pmd@{self.pmd_version}']
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.logger.info("PMD installed successfully")
                return True
            else:
                self.logger.error(f"Failed to install PMD: {result.stderr}")
                return False
        
        except Exception as e:
            self.logger.error(f"Error installing PMD: {str(e)}")
            return False
    
    def find_apex_files(self) -> List[str]:
        """
        Find all Apex files in delta package
        
        Returns:
            List of Apex file paths
        """
        apex_files = []
        
        try:
            # Search for .cls and .trigger files
            for pattern in ['**/*.cls', '**/*.trigger']:
                apex_files.extend([str(f) for f in self.delta_package.glob(pattern)])
            
            self.logger.info(f"Found {len(apex_files)} Apex files")
            return apex_files
        
        except Exception as e:
            self.logger.error(f"Error finding Apex files: {str(e)}")
            return []
    
    def create_pmd_ruleset(self) -> str:
        """
        Create PMD ruleset configuration for Apex
        
        Returns:
            Path to ruleset file
        """
        ruleset_path = self.workspace / 'pmd-ruleset.xml'
        
        ruleset_content = '''<?xml version="1.0" encoding="UTF-8"?>
<ruleset name="Salesforce Apex Rules"
         xmlns="http://pmd.sourceforge.net/ruleset/2.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://pmd.sourceforge.net/ruleset/2.0.0 http://pmd.sourceforge.net/ruleset_2_0_0.xsd">
    
    <description>PMD Ruleset for Salesforce Apex Code Quality Analysis</description>
    
    <!-- Best Practices -->
    <rule ref="category/apex/bestpractices.xml">
        <exclude name="ApexAssertionsShouldIncludeMessage" />
    </rule>
    
    <!-- Code Style -->
    <rule ref="category/apex/codestyle.xml">
        <exclude name="FieldNamingConventions" />
    </rule>
    
    <!-- Performance -->
    <rule ref="category/apex/performance.xml" />
    
    <!-- Security -->
    <rule ref="category/apex/security.xml" />
    
    <!-- Design -->
    <rule ref="category/apex/design.xml" />
    
    <!-- Error Prone -->
    <rule ref="category/apex/errorprone.xml" />
    
</ruleset>
'''
        
        try:
            with open(ruleset_path, 'w') as f:
                f.write(ruleset_content)
            
            self.logger.info(f"Created PMD ruleset at {ruleset_path}")
            return str(ruleset_path)
        
        except Exception as e:
            self.logger.error(f"Error creating PMD ruleset: {str(e)}")
            return ''
    
    def run_pmd_analysis(self, apex_files: List[str], fail_on_violation: bool = False) -> bool:
        """
        Execute PMD analysis on Apex files
        
        Args:
            apex_files: List of Apex file paths
            fail_on_violation: Whether to fail on violations
            
        Returns:
            True if analysis completed (violations don't affect result unless fail_on_violation=True)
        """
        try:
            if not apex_files:
                self.logger.warning("No Apex files to analyze")
                return True
            
            # Create ruleset
            ruleset_path = self.create_pmd_ruleset()
            if not ruleset_path:
                return False
            
            # Prepare file list
            files_arg = ','.join(apex_files)
            
            # Build PMD command
            cmd = [
                'pmd',
                'check',
                '--dir', str(self.delta_package),
                '--rulesets', ruleset_path,
                '--format', 'html',
                '--report-file', str(self.report_output),
                '--language', 'apex',
                '--failOnViolation', str(fail_on_violation).lower()
            ]
            
            self.logger.info(f"Running PMD analysis on {len(apex_files)} Apex files...")
            self.logger.info(f"Command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            # Log output
            if result.stdout:
                self.logger.info(f"PMD Output:\n{result.stdout}")
            
            if result.stderr:
                self.logger.warning(f"PMD Warnings:\n{result.stderr}")
            
            # Check result
            if result.returncode == 0:
                self.logger.info("PMD analysis completed successfully")
                return True
            elif result.returncode == 4 and not fail_on_violation:
                # Exit code 4 = violations found but not failing
                self.logger.warning("PMD analysis completed with violations (not failing)")
                return True
            else:
                self.logger.error(f"PMD analysis failed with exit code {result.returncode}")
                return not fail_on_violation
        
        except Exception as e:
            self.logger.error(f"Error running PMD analysis: {str(e)}")
            return False
    
    def generate_summary_report(self) -> bool:
        """
        Generate summary report from PMD analysis
        
        Returns:
            True if report generated successfully
        """
        try:
            if not self.report_output.exists():
                self.logger.warning("PMD report file not found")
                return False
            
            # Parse HTML report and log summary
            with open(self.report_output, 'r') as f:
                content = f.read()
            
            # Extract violation count
            if 'violation' in content.lower():
                self.logger.info("PMD report generated with violations")
            else:
                self.logger.info("PMD report generated - no violations found")
            
            self.logger.info(f"PMD report saved to {self.report_output}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error generating summary report: {str(e)}")
            return False
    
    def analyze(self, fail_on_violation: bool = False) -> bool:
        """
        Execute complete PMD analysis workflow
        
        Args:
            fail_on_violation: Whether to fail on violations
            
        Returns:
            True if analysis successful
        """
        try:
            self.logger.info("Starting PMD analysis...")
            
            # Verify delta package exists
            if not self.delta_package.exists():
                self.logger.error(f"Delta package not found: {self.delta_package}")
                return False
            
            # Verify PMD installation
            if not self.install_pmd():
                return False
            
            # Find Apex files
            apex_files = self.find_apex_files()
            if not apex_files:
                self.logger.warning("No Apex files found in delta package")
                return True
            
            # Run PMD analysis
            if not self.run_pmd_analysis(apex_files, fail_on_violation):
                return False
            
            # Generate summary
            self.generate_summary_report()
            
            self.logger.info("PMD analysis workflow completed successfully")
            return True
        
        except Exception as e:
            self.logger.error(f"Error in PMD analysis workflow: {str(e)}")
            return False


def main():
    """
    Main execution function
    """
    parser = argparse.ArgumentParser(
        description='Apex PMD Analysis Runner'
    )
    parser.add_argument('--workspace', required=True, help='Jenkins workspace directory')
    parser.add_argument('--delta-package', required=True, help='Path to delta package')
    parser.add_argument('--report-output', required=True, help='Output report file path')
    parser.add_argument('--fail-on-violation', default='false', 
                       help='Fail on violations (true/false)')
    
    args = parser.parse_args()
    
    # Create analyzer instance
    analyzer = PMDAnalyzer(
        workspace=args.workspace,
        delta_package=args.delta_package,
        report_output=args.report_output
    )
    
    # Run analysis
    fail_on_violation = args.fail_on_violation.lower() == 'true'
    success = analyzer.analyze(fail_on_violation=fail_on_violation)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
