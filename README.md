# Salesforce DevOps Pipeline

Enterprise-grade Jenkins pipeline for automated Salesforce deployments with promotional branching strategy.

## 🚀 Quick Start

### Prerequisites
- Jenkins 2.300+
- SFDX CLI 2.47.0+
- Python 3.8+
- Git 2.30+
- Node.js 16+

### Initial Setup

1. **Clone Repository**
   ```bash
   git clone https://github.com/manand79/sfdevops.git
   cd sfdevops
   ```

2. **Create Git Branches**
   ```bash
   git checkout -b develop
   git push origin develop
   ```

3. **Configure Jenkins Credentials** (See DEPLOYMENT_GUIDE.md)
   - Git credentials
   - Salesforce org credentials (DEV & QA)
   - OAuth/JWT credentials

4. **Run First Deployment**
   - Go to Jenkins → Build with Parameters
   - Select ENVIRONMENT: DEV
   - Set VALIDATE_ONLY: true
   - Click Build

## 📋 Pipeline Stages

1. **Initialize** - Validate parameters
2. **Code Checkout** - Clone from source branch
3. **Setup & Validation** - Install dependencies
4. **Promotional Branch Strategy** - Create safe promotion branch
5. **Prepare Delta Package** - Identify and package changes
6. **Salesforce Org Authentication** - Authenticate to org
7. **Apex PMD Analysis** - Code quality check
8. **Delta Package Validation** - Validate without deploying
9. **Deploy Delta Package** - Deploy to target org (if enabled)
10. **Post-Deployment Merge** - Merge to target branch
11. **Cleanup** - Clean up temporary artifacts

## 🌳 Branching Strategy

### Promotional Branching

```
DEV Environment:
  develop → promote/DEV/<BUILD_ID> → (validate/deploy) → develop

QA Environment:
  develop → promote/QA/<BUILD_ID> → (validate/deploy) → main
```

**Benefits:**
- ✅ Safe deployments with pre-deployment validation
- ✅ Full audit trail in git history
- ✅ Easy rollback via git revert
- ✅ Conflict detection before merging

## 🔧 Configuration

### Pipeline Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| ENVIRONMENT | choice | DEV | Target environment (DEV/QA) |
| SOURCE_BRANCH | string | develop | Branch with changes |
| TEST_LEVEL | choice | RunLocalTests | Apex test level |
| SPECIFIED_TESTS | string | - | Test classes (if RunSpecifiedTests) |
| VALIDATE_ONLY | boolean | true | Validate without deploying |
| AUTO_MERGE | boolean | false | Auto-merge after success |

### Environment Variables

Configured in Jenkinsfile:
- `GIT_REPO` - GitHub repository URL
- `GIT_CREDENTIALS` - GitHub credentials ID
- `DEV_ORG_*` - DEV org credentials
- `QA_ORG_*` - QA org credentials
- `TARGET_BRANCH` - Auto-derived from ENVIRONMENT
- `PROMOTION_BRANCH` - Auto-derived (promote/<ENV>/<BUILD_ID>)

## 🔐 Security

### Credentials Management

All credentials stored in Jenkins Credentials Manager:
- Git credentials (username + PAT)
- Salesforce org credentials
- OAuth Client ID/Secret
- Security tokens

**Best Practices:**
- Use OAuth/JWT for production
- Rotate credentials monthly
- Use least-privilege accounts
- Enable credential auditing

## 📊 Deployment Results

Results available in Jenkins artifacts:

```
artifacts/
├── validation-result.json   # Validation output
├── deploy-result.json       # Deployment output
├── pmd-report.html         # Code quality report
└── delta-package/          # Deployed metadata
```

## 🐛 Troubleshooting

### Common Issues

**Authentication Failed**
- Verify credentials in Jenkins
- Check security token is current
- Confirm OAuth client ID/secret

**Delta Package Empty**
- Verify branches have commits
- Check metadata file locations
- Review git diff between branches

**Test Failures**
- Review test failure details
- Run tests locally first
- Check code coverage requirements

**Merge Conflicts**
- Resolve conflicts manually
- Commit changes
- Retry pipeline

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed troubleshooting.

## 📚 Documentation

- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Complete deployment guide
- [Jenkinsfile](Jenkinsfile) - Pipeline definition
- [scripts/delta_package_manager.py](scripts/delta_package_manager.py) - Delta package creation
- [scripts/sfdx_auth_manager.py](scripts/sfdx_auth_manager.py) - Salesforce authentication
- [scripts/run_pmd_analysis.py](scripts/run_pmd_analysis.py) - PMD code analysis

## 🎯 Usage Examples

### Example 1: DEV Validation Only
```
ENVIRONMENT: DEV
SOURCE_BRANCH: develop
TEST_LEVEL: RunLocalTests
VALIDATE_ONLY: ✓ (checked)
AUTO_MERGE: ☐ (unchecked)

Result: Validates without deploying
```

### Example 2: QA Full Deployment
```
ENVIRONMENT: QA
SOURCE_BRANCH: develop
TEST_LEVEL: RunAllTestsInOrg
VALIDATE_ONLY: ☐ (unchecked)
AUTO_MERGE: ✓ (checked)

Result: Deploys to QA and auto-merges to main
```

### Example 3: Feature Testing
```
ENVIRONMENT: DEV
SOURCE_BRANCH: feature/new-feature
TEST_LEVEL: RunSpecifiedTests
SPECIFIED_TESTS: FeatureControllerTest,FeatureTriggerTest
VALIDATE_ONLY: ☐ (unchecked)
AUTO_MERGE: ☐ (unchecked)

Result: Deploys feature with specific tests
```

## 🔄 Continuous Integration

### GitHub Webhook Setup

1. Go to GitHub repo → Settings → Webhooks
2. Add webhook:
   - **Payload URL**: https://jenkins-url/github-webhook/
   - **Content type**: application/json
   - **Events**: Push events
   - Click "Add webhook"

3. Jenkins auto-triggers on push to monitored branch

## 📈 Monitoring

### Pipeline Metrics

Monitor in Jenkins:
- Build duration
- Failure rate
- Test coverage
- Deployment frequency
- Lead time for changes

### Logs

Access logs:
- **Console Output**: Full pipeline logs
- **Stage View**: Visual stage execution
- **Artifacts**: Deployment artifacts and reports

## 🚦 Best Practices

✅ **DO:**
- Use feature branches for development
- Write comprehensive tests
- Validate before deploying
- Review PMD reports
- Document changes

❌ **DON'T:**
- Deploy directly to production
- Skip validation
- Ignore test failures
- Use shared accounts
- Hardcode credentials

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#best-practices) for complete guidelines.

## 📞 Support

### Getting Help

1. Review [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#troubleshooting)
2. Check Jenkins console logs
3. Contact DevOps team

### Reporting Issues

1. Go to GitHub Issues
2. Describe the problem
3. Include:
   - Build number
   - Error messages
   - Pipeline parameters
   - Steps to reproduce

## 📝 Changelog

### Version 1.0 (2026-06-28)
- Initial release
- Promotional branching strategy
- Delta package deployment
- PMD code analysis
- Multi-environment support
- OAuth/JWT authentication
- Auto-merge capability

## 📄 License

InternalUse Only

## 👥 Contributors

- DevOps Team
- Salesforce Admin
- Development Team

---

**Last Updated**: 2026-06-28  
**Maintained By**: DevOps Team  
**Status**: Production Ready ✓
