# Salesforce DevOps Pipeline - Complete Deployment Guide

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Credentials Configuration](#credentials-configuration)
5. [Pipeline Stages](#pipeline-stages)
6. [Git Branching Strategy](#git-branching-strategy)
7. [Salesforce Org Setup](#salesforce-org-setup)
8. [Pipeline Execution](#pipeline-execution)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

---

## Overview

This is an enterprise-grade Jenkins pipeline for Salesforce deployments that implements:
- **Promotional Branching Strategy**: Safe, controlled deployments through promotion branches
- **Dual Environment Support**: Development and QA environments with separate branch mappings
- **Delta Package Deployment**: Only deploy changed metadata for faster deployments
- **Apex Code Quality**: Automated PMD analysis before deployment
- **Multi-level Testing**: NoTestRun, RunSpecifiedTests, RunLocalTests, RunAllTestsInOrg
- **Validation & Deployment**: Separate validation and deployment modes

### Key Features
✅ Automated delta package creation  
✅ Git-based promotional branching  
✅ Salesforce org authentication (OAuth & JWT)  
✅ Apex PMD code quality analysis  
✅ Multi-environment support  
✅ Automated test execution  
✅ Pre-deployment validation  
✅ Post-deployment auto-merge

---

## Prerequisites

### System Requirements
- Jenkins 2.300+
- SFDX CLI 2.47.0+
- Python 3.8+
- Git 2.30+
- Node.js 16+ (for PMD)
- npm 7+

### Jenkins Plugins
- Pipeline (Declarative & Scripted)
- Git
- Timestamper
- Email Extension (optional)

---

## Credentials Configuration

All credentials must be created in Jenkins Credentials Manager before running the pipeline.

### Git Credentials
```
Credential ID: SFDEVOPS_GIT_CREDENTIALS
Type: Username with password
Username: <github-username>
Password: <github-personal-access-token>
```

### Salesforce Org Credentials (DEV)
```
DEV_ORG_USERNAME
DEV_ORG_PASSWORD
DEV_SECURITY_TOKEN
DEV_CLIENT_ID
DEV_CLIENT_SECRET
```

### Salesforce Org Credentials (QA)
```
QA_ORG_USERNAME
QA_ORG_PASSWORD
QA_SECURITY_TOKEN
QA_CLIENT_ID
QA_CLIENT_SECRET
```

See DEPLOYMENT_GUIDE.md for detailed setup instructions.
