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

## Architecture

### Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Jenkins Pipeline Start                        │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
          ┌───────────────┐
          │  Initialize   │
          │  Parameters   │
          └───────┬───────┘
                  │
                  ▼
        ┌──────────────────────┐
        │  Code Checkout       │
        │  (from source branch) │
        └──────────┬───────────┘
                   │
                   ▼
         ┌──────────────────────┐
         │  Setup Environment   │
         │  Install Dependencies │
         └──────────┬───────────┘
                    │
                    ▼
    ┌──────────────────────────────────┐
    │  Promotional Branch Strategy     │
    │  - Create promotion branch       │
    │  - Merge source into promotion   │
    └──────────┬───────────────────────┘
               │
               ▼
       ┌────────────────────────┐
       │  Prepare Delta Package │
       │  (Python automation)   │
       └────────────┬───────────┘
                    │
                    ▼
    ┌──────────────────────────────────┐
    │  Salesforce Authentication       │
    │  (OAuth/JWT/Credentials)         │
    └──────────┬───────────────────────┘
               │
               ▼
         ┌──────────────────────┐
         │  Apex PMD Analysis   │
         │  (Code Quality Check)│
         └──────────┬───────────┘
                    │
                    ▼
      ┌─────────────────────────────┐
      │  Delta Package Validation   │
      │  (CheckOnly deployment)     │
      └──────────┬──────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼ (if validate   ▼ (if deploy
         only)           mode)
    ┌────────┐      ┌────────────────┐
    │  Skip  │      │  Deploy Delta  │
    │Deploy  │      │  Package       │
    └────────┘      └────────┬───────┘
        │                    │
        │          ┌─────────┴────────┐
        │          │                  │
        │          ▼ (if success     │
        │     & auto-merge)           │
        │    ┌─────────────┐          │
        │    │ Merge to    │          │
        │    │ Target Brnch│          │
        │    └─────────────┘          │
        │          │                  │
        └──────────┼──────────────────┘
                   │
                   ▼
          ┌──────────────────┐
          │  Cleanup         │
          │  - Delete promo  │
          │  - Revoke auth   │
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │  Pipeline End    │
          │  (Success/Fail)  │
          └──────────────────┘
```

### Environment Mapping

| Environment | Source Branch | Target Branch | Org Type | Use Case |
|------------|---------------|---------------|----------|----------|
| DEV | `develop` | `develop` | Dev Org | Active Development |
| QA | `develop` → `main` | `main` | QA Org | Pre-production Testing |

---

## Prerequisites

### System Requirements
- Jenkins 2.300+
- SFDX CLI 2.47.0+
- Python 3.8+
- Git 2.30+
- Node.js 16+ (for PMD)
- npm 7+

### Jenkins Plugins Required
```
- Pipeline (Declarative & Scripted)
- Git
- GitHub (optional, for webhooks)
- Timestamper
- Log Parser (optional)
- Email Extension (optional)
- Slack Notification (optional)
```

### Salesforce Setup
- Admin access to DEV and QA orgs
- Connected App credentials (OAuth Client ID/Secret)
- Security tokens (if using password authentication)
- Test classes for Apex test execution

---

## Credentials Configuration

### 1. Creating Credentials in Jenkins

#### Via Web UI:
1. Go to **Jenkins Dashboard** → **Manage Jenkins** → **Manage Credentials**
2. Click **System** → **Global credentials (unrestricted)**
3. Click **Add Credentials** and select credential type
4. Fill in details and click **Create**

#### Via Jenkins CLI:
```bash
jenkins-cli create-credentials-by-xml system::system "CREDENTIAL_ID" < credential.xml
```

### 2. Required Credentials Setup

#### Git Repository Credentials
```
Credential ID: SFDEVOPS_GIT_CREDENTIALS
Type: Username with password
Username: <your-github-username>
Password: <github-personal-access-token>

Scopes:
  - Global
```

**Creating GitHub Personal Access Token:**
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Click "Generate new token"
3. Select scopes: `repo`, `admin:repo_hook`
4. Copy token and save securely

#### Git Configuration Credentials
```
Credential ID: GIT_USER_EMAIL
Type: Secret text
Secret: <your-email@company.com>

Credential ID: GIT_USER_NAME
Type: Secret text
Secret: <Your Name>
```

#### GitHub Repository URL
```
Credential ID: SFDEVOPS_GIT_REPO
Type: Secret text
Secret: https://github.com/manand79/sfdevops.git
```

### 3. Salesforce Org Credentials - DEV Environment

#### Username/Password Authentication
```
Credential ID: DEV_ORG_USERNAME
Type: Secret text
Secret: dev-org-admin@company.com

Credential ID: DEV_ORG_PASSWORD
Type: Secret password
Secret: <your-org-password>

Credential ID: DEV_SECURITY_TOKEN
Type: Secret text
Secret: <your-security-token>
Note: Retrieve from Salesforce: Setup → Security → Reset Security Token
```

#### OAuth Authentication (Recommended for CI/CD)
```
Credential ID: DEV_CLIENT_ID
Type: Secret text
Secret: <oauth-client-id-from-connected-app>

Credential ID: DEV_CLIENT_SECRET
Type: Secret password
Secret: <oauth-client-secret>
```

### 4. Salesforce Org Credentials - QA Environment

```
Credential ID: QA_ORG_USERNAME
Type: Secret text
Secret: qa-org-admin@company.com

Credential ID: QA_ORG_PASSWORD
Type: Secret password
Secret: <your-qa-org-password>

Credential ID: QA_SECURITY_TOKEN
Type: Secret text
Secret: <your-qa-security-token>

Credential ID: QA_CLIENT_ID
Type: Secret text
Secret: <oauth-client-id-for-qa>

Credential ID: QA_CLIENT_SECRET
Type: Secret password
Secret: <oauth-client-secret-for-qa>
```

### 5. Optional Credentials

```
Credential ID: NPM_AUTH_TOKEN
Type: Secret text
Secret: <npm-authentication-token>
Note: Required for PMD npm package installation
```

### 6. Credential Verification

Verify credentials are accessible:
```bash
# Via Jenkins Script Console
jenkins-cli groovy-script

// Retrieve credential
import jenkins.model.Jenkins
import com.cloudbees.plugins.credentials.CredentialsProvider
def cred = CredentialsProvider.lookupCredentials(
    com.cloudbees.plugins.credentials.common.StandardUsernamePasswordCredentials.class,
    Jenkins.instance
).find { it.id == 'SFDEVOPS_GIT_CREDENTIALS' }
println cred?.username
```

---

## Pipeline Stages

### Stage 1: Initialize
- Validates pipeline parameters
- Logs environment configuration
- Displays build metadata

**Input Parameters:**
- `ENVIRONMENT`: DEV or QA
- `SOURCE_BRANCH`: Branch with changes
- `TEST_LEVEL`: Apex test execution level
- `VALIDATE_ONLY`: true/false
- `AUTO_MERGE`: true/false

### Stage 2: Code Checkout
- Clones repository from source branch
- Uses Git credentials for authentication
- Sets up workspace

**Key Operations:**
```bash
git clone <repo-url>
git checkout <source-branch>
```

### Stage 3: Setup & Validation
- Creates necessary directories
- Installs/validates SFDX CLI
- Validates environment

**Directory Structure Created:**
```
${WORKSPACE}/
├── deploy/
├── delta-package/
├── scripts/
├── config/
└── artifacts/
```

### Stage 4: Promotional Branch Strategy
- Creates promotion branch from target branch
- Merges source branch into promotion branch
- Handles merge conflicts if any

**Git Operations:**
```bash
git checkout -b promote/<ENVIRONMENT>/<BUILD_ID> origin/<TARGET_BRANCH>
git merge origin/<SOURCE_BRANCH>
```

**Promotion Branch Naming Convention:**
```
promote/DEV/1234    # DEV environment, build #1234
promote/QA/1235     # QA environment, build #1235
```

### Stage 5: Prepare Delta Package
- Identifies changed files between source and target branches
- Categorizes metadata by type (Apex, Custom Objects, etc.)
- Creates package.xml
- Copies changed files to delta package directory

**Delta Package Python Script:**
- Located: `scripts/delta_package_manager.py`
- Compares branches using `git diff`
- Creates proper metadata structure
- Generates package.xml with API version 58.0

**Supported Metadata Types:**
- ApexClass (.cls)
- ApexTrigger (.trigger)
- ApexPage (.page)
- ApexComponent (.component)
- StaticResource (.resource)
- CustomObject (.object)
- Layout (.layout)
- ValidationRule (.validationRule)
- And 15+ more types

**Output Structure:**
```
delta-package/
├── package.xml
└── force-app/
    ├── main/
    │   ├── default/
    │   │   ├── classes/
    │   │   ├── triggers/
    │   │   ├── objects/
    │   │   └── ...
```

### Stage 6: Salesforce Org Authentication
- Authenticates to target Salesforce org
- Supports OAuth, JWT, and credential-based auth
- Stores auth locally for subsequent operations

**SFDX Auth Manager Script:**
- Located: `scripts/sfdx_auth_manager.py`
- Creates org alias for pipeline use
- Verifies authentication
- Retrieves org information

**Authentication Methods:**
```
1. OAuth (Web Login Flow)
   - Interactive, suitable for local testing
   
2. JWT Bearer Flow (Recommended for CI/CD)
   - Non-interactive
   - Requires JWT key file
   - Most secure for automation
   
3. Credentials (Username + Password + Token)
   - Simple setup
   - Requires security token
   - Less secure than OAuth
```

### Stage 7: Apex PMD Analysis
- Installs/verifies PMD (code quality tool)
- Runs static analysis on Apex code in delta package
- Generates HTML report with violations
- Checks code quality standards

**PMD Rules Applied:**
- Best Practices (AvoidLogicInTrigger, etc.)
- Performance (AvoidSoqlInLoop, etc.)
- Security (SOQL Injection, Cross-site scripting, etc.)
- Design (TooManyFields, ExcessiveClassLength, etc.)

**PMD Report Output:**
- File: `${WORKSPACE}/pmd-report.html`
- Shows: Violations, severity levels, file locations
- Archived as artifact

### Stage 8: Delta Package Validation
- Performs CheckOnly deployment to target org
- Runs specified test level
- Validates metadata correctness
- No actual changes made to org

**Validation Parameters:**
```
Test Levels:
- NoTestRun: No tests executed (fastest, not recommended for production)
- RunSpecifiedTests: Only specified test classes
- RunLocalTests: All local tests (no managed package tests)
- RunAllTestsInOrg: All org tests (slowest, most thorough)
```

**SFDX Deployment Command:**
```bash
sfdx force:mdapi:deploy \
  --deploydir ${DELTA_PKG_DIR} \
  -u ${ENVIRONMENT}-org \
  --checkonly \
  --testlevel ${TEST_LEVEL} \
  --wait 60 \
  --json
```

### Stage 9: Deploy Delta Package
- Executes actual deployment (if not validate-only)
- Runs specified tests
- Deploys to target Salesforce org

**Conditional Execution:**
- Skipped if `VALIDATE_ONLY = true`
- Executes if `VALIDATE_ONLY = false`

**Deployment Success Criteria:**
- All tests pass (if applicable)
- No validation errors
- All metadata components deploy successfully

### Stage 10: Post-Deployment Merge
- Merges promotion branch to target branch
- Updates target branch with changes
- Pushes to remote repository

**Git Operations (if AUTO_MERGE = true):**
```bash
git checkout <TARGET_BRANCH>
git merge <PROMOTION_BRANCH>
git push origin <TARGET_BRANCH>
```

### Stage 11: Cleanup
- Deletes promotion branch locally and on remote
- Revokes SFDX authentication
- Cleans up temporary artifacts

**Cleanup Operations:**
```bash
git branch -D promote/QA/1234
git push origin --delete promote/QA/1234
sfdx force:org:logout --target-org QA-org
```

---

## Git Branching Strategy

### Promotional Branching Strategy

This pipeline implements a **promotional branching strategy** with the following workflow:

#### DEV Environment Workflow

```
develop (source)
    │
    ├──> promote/DEV/<BUILD_ID> (temporary promotion branch)
    │         │
    │         ├─ Validate
    │         ├─ Deploy
    │         └─ Merge back to develop
    │
    └──> develop (target - updated after successful merge)
```

**Flow:**
1. Changes committed to `develop` branch
2. Jenkins creates `promote/DEV/<BUILD_ID>` from `develop`
3. Merges latest `develop` into promotion branch
4. Validates and deploys
5. If successful, merges back to `develop`

#### QA Environment Workflow

```
main (source - actual target)
develop (source - provides changes)
    │
    ├──> promote/QA/<BUILD_ID> (temporary promotion branch)
    │         │
    │         ├─ Merge develop into this branch
    │         ├─ Validate
    │         ├─ Deploy to QA
    │         └─ Merge back to main
    │
    └──> main (target - updated after successful merge)
```

**Flow:**
1. QA release planned from `main` branch
2. Create `promote/QA/<BUILD_ID>` from `main`
3. Merge changes from `develop` into promotion branch
4. Validates and deploys to QA org
5. If successful, merges promotion branch back to `main`

### Promotion Branch Naming Convention

```
promote/<ENVIRONMENT>/<BUILD_ID>
promote/DEV/1234
promote/QA/1235
```

- `ENVIRONMENT`: DEV or QA
- `BUILD_ID`: Jenkins build number

### Advantages of Promotional Branching

✅ **Safety**: Changes validated before merging to target  
✅ **Traceability**: Each deployment tracked via promotion branch  
✅ **Rollback**: Previous state available via git history  
✅ **Separation**: Dev changes isolated from QA branch  
✅ **Conflict Resolution**: Merge conflicts detected early  
✅ **Audit Trail**: All deployments logged in git history  

---

## Salesforce Org Setup

### 1. Create Connected App for OAuth

#### In Salesforce Org:

1. Go to **Setup** → **Apps** → **App Manager**
2. Click **New Connected App**
3. Fill in details:
   - **Connected App Name**: SalesforceDevOps
   - **API Name**: SalesforceDevOps
   - **Contact Email**: your-email@company.com

4. Enable OAuth Settings:
   - Check **Enable OAuth Settings**
   - **Callback URL**: `http://localhost:8080` (for local) or Jenkins URL
   - **Selected OAuth Scopes**:
     - Full access (full)
     - Perform requests on your behalf at any time (refresh_token)
     - Access your basic information (id, profile, email, address, phone)
   - Click **Save**

5. Get OAuth Credentials:
   - Click **Manage Consumer Details**
   - Copy **Consumer Key** → `DEV_CLIENT_ID`/`QA_CLIENT_ID`
   - Copy **Consumer Secret** → `DEV_CLIENT_SECRET`/`QA_CLIENT_SECRET`

#### For JWT Bearer Flow (Recommended):

1. Create SSL Certificate:
   ```bash
   openssl req -x509 -newkey rsa:2048 -keyout server.key -out server.crt -days 365 -nodes
   ```

2. Upload Certificate to Salesforce:
   - Go to **Setup** → **Apps** → **App Manager**
   - Open connected app → **Edit**
   - Enable JWT OAuth:
     - Check **Enable OAuth Settings**
     - Add scope: full, refresh_token
     - Under **Certificates**, click **Choose File** and upload server.crt
   - Click **Save**

3. Authorize JWT Flow:
   ```bash
   sfdx force:auth:jwt:grant \
     --client-id <CLIENT_ID> \
     --jwt-key-file server.key \
     --username <SALESFORCE_USERNAME> \
     --alias DEV-org
   ```

### 2. Enable Salesforce Features

#### Required Features:
- Apex Development
- Metadata API
- Change Set (optional)

#### Recommended Settings:
1. Go to **Setup** → **Development** → **Apex Exceptions**
   - Enable exception logging for debugging
   
2. Go to **Setup** → **Development** → **Debug Logs**
   - Keep debug logs enabled for troubleshooting

3. Go to **Setup** → **Security** → **API Limits**
   - Check API usage limits

### 3. Create Deployment Users (Optional)

For security, create dedicated deployment user:

1. Go to **Setup** → **Users** → **Users**
2. Click **New User**
3. **First Name**: Deployment
4. **Last Name**: User
5. **Email**: deployment.user@company.com
6. **User License**: Salesforce
7. **Profile**: System Administrator
8. Click **Save**

9. Generate Security Token:
   - Click user name → **Settings**
   - Click **Reset My Security Token**
   - Check email for token

### 4. Configure Salesforce Limits

Check and configure:
```
Setup → System Overview → API Usage Limits
Setup → Performance → API Limits

Typical limits per day:
- API calls: 500,000 - 5,000,000+
- Daily batch API calls: 10,000,000+
```

---

## Pipeline Execution

### Starting the Pipeline

#### Via Jenkins Web UI:

1. Go to Jenkins Dashboard
2. Click on pipeline job (e.g., "Salesforce-Deployment")
3. Click **Build with Parameters**
4. Fill in parameters:
   - **ENVIRONMENT**: Select DEV or QA
   - **SOURCE_BRANCH**: develop or feature branch
   - **TEST_LEVEL**: Select test execution level
   - **VALIDATE_ONLY**: Check if validation only, uncheck to deploy
   - **AUTO_MERGE**: Check to auto-merge after deployment
5. Click **Build**

#### Via GitHub Webhook (Optional):

Configure webhook on GitHub to trigger pipeline on push:
1. Go to GitHub repo → **Settings** → **Webhooks**
2. Add webhook:
   - **Payload URL**: `https://jenkins-url/github-webhook/`
   - **Content type**: application/json
   - **Events**: Push events
   - Click **Add webhook**

### Parameter Explanations

| Parameter | Values | Description |
|-----------|--------|-------------|
| ENVIRONMENT | DEV, QA | Target deployment environment |
| SOURCE_BRANCH | develop, feature/* | Branch with changes to deploy |
| TEST_LEVEL | NoTestRun, RunSpecifiedTests, RunLocalTests, RunAllTestsInOrg | Apex test execution level |
| SPECIFIED_TESTS | MyTest1,MyTest2 | Test classes (required if RunSpecifiedTests) |
| VALIDATE_ONLY | true, false | If true, validate only; if false, deploy |
| AUTO_MERGE | true, false | Auto-merge promotion to target after success |

### Example Execution Scenarios

#### Scenario 1: DEV Deployment with Validation Only
```
Parameters:
- ENVIRONMENT: DEV
- SOURCE_BRANCH: develop
- TEST_LEVEL: RunLocalTests
- VALIDATE_ONLY: true ✓
- AUTO_MERGE: false

Result: Validates deployment without making changes
```

#### Scenario 2: QA Deployment with Auto-Merge
```
Parameters:
- ENVIRONMENT: QA
- SOURCE_BRANCH: develop
- TEST_LEVEL: RunAllTestsInOrg
- VALIDATE_ONLY: false
- AUTO_MERGE: true ✓

Result: Deploys to QA, runs all tests, merges to main if successful
```

#### Scenario 3: DEV Deployment with Specific Tests
```
Parameters:
- ENVIRONMENT: DEV
- SOURCE_BRANCH: feature/new-feature
- TEST_LEVEL: RunSpecifiedTests
- SPECIFIED_TESTS: AccountControllerTest,OpportunityTriggerTest
- VALIDATE_ONLY: false
- AUTO_MERGE: false

Result: Deploys specific feature, runs specific test classes
```

### Monitoring Execution

#### In Jenkins UI:
1. **Build History**: Shows all pipeline runs
2. **Console Output**: Detailed stage-by-stage logs
3. **Artifacts**: Download deployment results
4. **Pipeline View**: Visual representation of stage execution

#### Key Log Information:
```
[Stage: Code Checkout] Starting code checkout...
[Stage: Prepare Delta Package] Creating delta package...
[Stage: Salesforce Org Authentication] Authenticating to QA org...
[Stage: Delta Package Validation] Validating delta package...
[Stage: Deploy Delta Package] Deploying delta package to QA org...
```

### Viewing Results

#### Validation Results:
```
File: ${WORKSPACE}/validation-result.json
Contains:
- Deployment status
- Test results
- Error details (if any)
- Validation time
```

#### Deployment Results:
```
File: ${WORKSPACE}/deploy-result.json
Contains:
- Deployment ID
- Status (Succeeded/Failed)
- Component details
- Test coverage info
```

#### PMD Report:
```
File: ${WORKSPACE}/pmd-report.html
Contains:
- Code violations found
- Severity levels
- File locations
- Quick fixes
```

---

## Troubleshooting

### Common Issues & Solutions

#### Issue 1: Authentication Failure

**Error**: `invalid_grant`, `Authentication failed`

**Solutions**:
1. Verify credentials in Jenkins:
   ```bash
   sfdx force:org:list
   ```

2. Check security token:
   - Reset security token in Salesforce: Setup → Security → Reset Security Token
   - Add to password in Jenkins credentials

3. Verify OAuth Client ID/Secret:
   - Confirm in Salesforce Connected App settings
   - Check expiration dates

4. For JWT: Verify certificate:
   ```bash
   openssl x509 -in server.crt -text -noout
   ```

#### Issue 2: Delta Package Empty

**Error**: `No changes found between branches`

**Solutions**:
1. Verify branches exist and are correct:
   ```bash
   git branch -a
   ```

2. Check if there are actual commits between branches:
   ```bash
   git log --oneline source-branch..target-branch
   ```

3. Verify metadata file locations:
   ```bash
   find . -name "*.cls" -o -name "*.trigger" | head -20
   ```

#### Issue 3: Test Failures

**Error**: `Test execution failed`, `Number of test failures: 5`

**Solutions**:
1. Review test failure details in deployment results:
   ```json
   cat ${WORKSPACE}/deploy-result.json | grep -A 20 "failures"
   ```

2. Run tests locally:
   ```bash
   sfdx force:apex:test:run -u DEV-org --resultformat human
   ```

3. Check test coverage:
   ```bash
   sfdx force:apex:test:run -u DEV-org --resultformat tap
   ```

#### Issue 4: Merge Conflicts

**Error**: `Merge conflict in file.cls`

**Solutions**:
1. Resolve conflicts manually:
   ```bash
   git status
   git checkout --theirs file.cls  # Accept incoming changes
   git checkout --ours file.cls    # Accept current changes
   git add file.cls
   git commit -m "Resolved merge conflict"
   ```

2. Retry pipeline after resolving

3. Or, abort merge and investigate:
   ```bash
   git merge --abort
   ```

#### Issue 5: PMD Violations Blocking Deployment

**Error**: `PMD analysis failed with violations`

**Solutions**:
1. View PMD report:
   - Download `pmd-report.html` from artifacts
   - Open in browser
   - Review violations and their locations

2. Fix violations:
   - Update code to address violations
   - Commit changes
   - Re-trigger pipeline

3. Or, adjust PMD rules:
   - Edit `config/pmd-ruleset.xml`
   - Exclude rules if acceptable
   - Recommend fixing instead of excluding

#### Issue 6: SFDX CLI Issues

**Error**: `sfdx: command not found`

**Solutions**:
1. Verify SFDX installation:
   ```bash
   sfdx --version
   ```

2. Reinstall SFDX:
   ```bash
   npm uninstall -g @salesforce/cli
   npm install -g @salesforce/cli@latest
   ```

3. Check PATH:
   ```bash
   echo $PATH
   which sfdx
   ```

#### Issue 7: Git Credential Issues

**Error**: `fatal: Authentication failed for 'https://github.com/...'`

**Solutions**:
1. Verify GitHub credentials:
   - Check GitHub Personal Access Token is valid
   - Confirm token has `repo` scope

2. Test Git authentication:
   ```bash
   git ls-remote https://github.com/manand79/sfdevops.git
   ```

3. Update credentials in Jenkins:
   - Go to Manage Jenkins → Manage Credentials
   - Edit `SFDEVOPS_GIT_CREDENTIALS`
   - Update with new token

### Debug Mode

Enable verbose logging:

```groovy
// In Jenkinsfile, add:
environment {
    DEBUG = "true"
    SFDX_LOG_LEVEL = "DEBUG"
}
```

Or via Jenkins Script Console:
```groovy
def job = Jenkins.instance.getItem("Salesforce-Deployment")
job.properties.add(new ParametersDefinitionProperty([
    new StringParameterDefinition("DEBUG", "true")
]))
```

---

## Best Practices

### 1. Development Workflow

✅ **DO:**
- Use feature branches: `feature/JIRA-123-description`
- Keep commits small and focused
- Write clear commit messages
- Create pull requests for code review
- Run tests locally before pushing

❌ **DON'T:**
- Commit directly to `develop` or `main`
- Make large commits with unrelated changes
- Ignore test failures
- Deploy untested code

### 2. Testing Strategy

✅ **DO:**
- Write unit tests for all Apex code
- Maintain 75%+ code coverage
- Use `RunLocalTests` for DEV deployments
- Use `RunAllTestsInOrg` for QA/Prod deployments
- Test negative scenarios

❌ **DON'T:**
- Use `NoTestRun` for production deployments
- Ignore failing tests
- Deploy code with low coverage
- Skip regression testing

### 3. Credentials Management

✅ **DO:**
- Use Jenkins Credentials for all secrets
- Use OAuth/JWT for production
- Rotate credentials regularly
- Use least-privilege approach
- Audit credential usage

❌ **DON'T:**
- Store credentials in code/config files
- Use shared admin accounts
- Hardcode passwords
- Share credentials between team members
- Commit credentials to git

### 4. Branching Strategy

✅ **DO:**
- Use meaningful branch names
- Keep branches short-lived
- Delete merged branches
- Use promotion branches for safety
- Document branch purpose in PR

❌ **DON'T:**
- Use ambiguous branch names
- Keep stale branches
- Skip merge reviews
- Bypass promotional branches
- Force push to shared branches

### 5. Deployment Practices

✅ **DO:**
- Validate before deploying
- Deploy to DEV first
- Test in QA before production
- Keep deployment window small
- Document deployment changes

❌ **DON'T:**
- Deploy directly to production
- Skip validation phase
- Deploy during business hours (if possible)
- Deploy untested components
- Make changes without documentation

### 6. Monitoring & Logging

✅ **DO:**
- Monitor pipeline execution
- Review deployment logs
- Track deployment metrics
- Alert on failures
- Keep audit trail

❌ **DON'T:**
- Ignore pipeline failures
- Delete logs before reviewing
- Miss notification emails
- Forget to document issues
- Skip post-deployment verification

### 7. Code Quality

✅ **DO:**
- Run PMD analysis
- Fix code violations
- Review PMD reports
- Maintain consistency
- Use code standards

❌ **DON'T:**
- Disable PMD rules
- Ignore violations
- Ship code with issues
- Use inconsistent naming
- Skip code reviews

### 8. Error Handling

✅ **DO:**
- Catch and handle exceptions
- Log errors with context
- Provide meaningful error messages
- Use try-catch blocks
- Test error scenarios

❌ **DON'T:**
- Ignore exceptions
- Use generic error messages
- Miss error logging
- Assume happy path only
- Skip negative testing

### 9. Metadata Management

✅ **DO:**
- Use delta packages
- Track all metadata changes
- Version control all components
- Document metadata dependencies
- Review package.xml

❌ **DON'T:**
- Deploy full packages unnecessarily
- Manually manage metadata
- Skip documentation
- Break dependencies
- Deploy without review

### 10. Team Communication

✅ **DO:**
- Notify team of deployments
- Document deployment details
- Share deployment schedule
- Communicate issues early
- Conduct deployment reviews

❌ **DON'T:**
- Deploy silently
- Skip communication
- Surprise deployments
- Hide failures
- Deploy during critical periods

---

## Additional Resources

### Documentation
- [Salesforce SFDX Documentation](https://developer.salesforce.com/tools/sfdxcli)
- [Jenkins Pipeline Documentation](https://www.jenkins.io/doc/book/pipeline/)
- [Git Documentation](https://git-scm.com/doc)
- [PMD Documentation](https://pmd.github.io/)

### Salesforce Learning
- [Salesforce Metadata API](https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/)
- [Apex Testing Guide](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_testing.htm)
- [Package Development](https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/)

### DevOps Best Practices
- [Google Cloud DevOps Research](https://cloud.google.com/architecture/devops)
- [AWS DevOps](https://aws.amazon.com/devops/)
- [The Phoenix Project](https://www.oreilly.com/library/view/the-phoenix-project/9781457191985/)

---

## Support & Maintenance

### Regular Maintenance Tasks

- **Weekly**: Review failed deployments, update dependencies
- **Monthly**: Rotate credentials, audit access
- **Quarterly**: Update SFDX CLI, review pipeline efficiency
- **Annually**: Security audit, performance optimization

### Getting Help

1. Check troubleshooting section
2. Review Jenkins logs: `${WORKSPACE}/logs/`
3. Contact Salesforce admin for org issues
4. Review git history: `git log --oneline`
5. Consult team documentation

### Contact Information

For questions or issues:
- Jenkins Admin: jenkins-admin@company.com
- Salesforce Lead: salesforce-lead@company.com
- DevOps Team: devops@company.com

---

**Document Version**: 1.0  
**Last Updated**: 2026-06-28  
**Maintained By**: DevOps Team
