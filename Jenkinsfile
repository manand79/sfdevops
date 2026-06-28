// Salesforce Deployment Pipeline
// Branch Strategy: Promotional Branching (develop -> QA, main -> Prod)
// Environments: Dev (develop branch), QA (main branch)

@Library('shared-library') _

pipeline {
    agent any
    
    parameters {
        choice(
            name: 'ENVIRONMENT',
            choices: ['DEV', 'QA'],
            description: 'Target deployment environment'
        )
        string(
            name: 'SOURCE_BRANCH',
            defaultValue: 'develop',
            description: 'Source branch for deployment'
        )
        choice(
            name: 'TEST_LEVEL',
            choices: ['NoTestRun', 'RunSpecifiedTests', 'RunLocalTests', 'RunAllTestsInOrg'],
            description: 'Apex test level for validation'
        )
        string(
            name: 'SPECIFIED_TESTS',
            defaultValue: '',
            description: 'Comma-separated test class names (required if TEST_LEVEL is RunSpecifiedTests)'
        )
        booleanParam(
            name: 'VALIDATE_ONLY',
            defaultValue: true,
            description: 'Validate without deploying (set to false to deploy)'
        )
        booleanParam(
            name: 'AUTO_MERGE',
            defaultValue: false,
            description: 'Auto-merge to target branch after successful deployment'
        )
    }
    
    environment {
        // Git Configuration
        GIT_REPO = credentials('SFDEVOPS_GIT_REPO')
        GIT_CREDENTIALS = credentials('SFDEVOPS_GIT_CREDENTIALS')
        GIT_USER_EMAIL = credentials('GIT_USER_EMAIL')
        GIT_USER_NAME = credentials('GIT_USER_NAME')
        
        // Salesforce Org Credentials
        DEV_ORG_USERNAME = credentials('DEV_ORG_USERNAME')
        DEV_ORG_PASSWORD = credentials('DEV_ORG_PASSWORD')
        DEV_SECURITY_TOKEN = credentials('DEV_SECURITY_TOKEN')
        DEV_CLIENT_ID = credentials('DEV_CLIENT_ID')
        DEV_CLIENT_SECRET = credentials('DEV_CLIENT_SECRET')
        
        QA_ORG_USERNAME = credentials('QA_ORG_USERNAME')
        QA_ORG_PASSWORD = credentials('QA_ORG_PASSWORD')
        QA_SECURITY_TOKEN = credentials('QA_SECURITY_TOKEN')
        QA_CLIENT_ID = credentials('QA_CLIENT_ID')
        QA_CLIENT_SECRET = credentials('QA_CLIENT_SECRET')
        
        // Pipeline Configuration
        WORKSPACE_DIR = "${WORKSPACE}"
        SCRIPTS_DIR = "${WORKSPACE}/scripts"
        CONFIG_DIR = "${WORKSPACE}/config"
        DEPLOY_DIR = "${WORKSPACE}/deploy"
        DELTA_PKG_DIR = "${WORKSPACE}/delta-package"
        PMD_REPORT = "${WORKSPACE}/pmd-report.html"
        SFDX_CLI_VERSION = "2.47.0"
        NODE_AUTH_TOKEN = credentials('NPM_AUTH_TOKEN')
        
        // Derived Environment Variables
        TARGET_BRANCH = "${ENVIRONMENT == 'QA' ? 'main' : 'develop'}"
        PROMOTION_BRANCH = "promote/${ENVIRONMENT}/${BUILD_ID}"
        ORG_USERNAME = "${ENVIRONMENT == 'QA' ? QA_ORG_USERNAME : DEV_ORG_USERNAME}"
        ORG_PASSWORD = "${ENVIRONMENT == 'QA' ? QA_ORG_PASSWORD : DEV_ORG_PASSWORD}"
        SECURITY_TOKEN = "${ENVIRONMENT == 'QA' ? QA_SECURITY_TOKEN : DEV_SECURITY_TOKEN}"
        CLIENT_ID = "${ENVIRONMENT == 'QA' ? QA_CLIENT_ID : DEV_CLIENT_ID}"
        CLIENT_SECRET = "${ENVIRONMENT == 'QA' ? QA_CLIENT_SECRET : DEV_CLIENT_SECRET}"
    }
    
    options {
        timeout(time: 2, unit: 'HOURS')
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '30'))
        skipDefaultCheckout()
    }
    
    stages {
        stage('Initialize') {
            steps {
                script {
                    echo "=== Salesforce Deployment Pipeline ==="
                    echo "Environment: ${ENVIRONMENT}"
                    echo "Source Branch: ${SOURCE_BRANCH}"
                    echo "Target Branch: ${TARGET_BRANCH}"
                    echo "Promotion Branch: ${PROMOTION_BRANCH}"
                    echo "Test Level: ${TEST_LEVEL}"
                    echo "Validate Only: ${VALIDATE_ONLY}"
                    echo "Build ID: ${BUILD_ID}"
                    echo "Build Number: ${BUILD_NUMBER}"
                }
            }
        }
        
        stage('Code Checkout') {
            steps {
                script {
                    echo "[Stage: Code Checkout] Starting code checkout..."
                    deleteDir()
                    
                    withCredentials([usernamePassword(credentialsId: 'SFDEVOPS_GIT_CREDENTIALS', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
                        checkout([
                            $class: 'GitSCM',
                            branches: [[name: "*/${SOURCE_BRANCH}"]],
                            userRemoteConfigs: [[url: "${GIT_REPO}", credentialsId: 'SFDEVOPS_GIT_CREDENTIALS']]
                        ])
                    }
                    
                    echo "[Stage: Code Checkout] Code checked out successfully"
                }
            }
        }
        
        stage('Setup & Validation') {
            steps {
                script {
                    echo "[Stage: Setup & Validation] Setting up environment..."
                    
                    sh '''
                        # Create necessary directories
                        mkdir -p ${DEPLOY_DIR}
                        mkdir -p ${DELTA_PKG_DIR}
                        mkdir -p ${SCRIPTS_DIR}
                        mkdir -p ${CONFIG_DIR}
                        
                        # Display directory structure
                        echo "Current working directory: $(pwd)"
                        echo "Environment setup:"
                        ls -la
                    '''
                    
                    // Validate SFDX CLI installation
                    sh '''
                        echo "Validating SFDX CLI installation..."
                        sfdx --version || {
                            echo "Installing SFDX CLI..."
                            npm install -g @salesforce/cli
                        }
                        sfdx --version
                    '''
                    
                    echo "[Stage: Setup & Validation] Environment setup completed"
                }
            }
        }
        
        stage('Promotional Branch Strategy') {
            steps {
                script {
                    echo "[Stage: Promotional Branch Strategy] Setting up promotion workflow..."
                    
                    withCredentials([usernamePassword(credentialsId: 'SFDEVOPS_GIT_CREDENTIALS', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
                        sh '''
                            cd ${WORKSPACE}
                            
                            # Configure Git
                            git config user.email "${GIT_USER_EMAIL}"
                            git config user.name "${GIT_USER_NAME}"
                            
                            # Setup remote with credentials
                            git remote set-url origin "https://${GIT_USER}:${GIT_PASS}@github.com/manand79/sfdevops.git"
                            
                            # Fetch latest from remote
                            git fetch origin
                            
                            echo "Creating promotion branch: ${PROMOTION_BRANCH}"
                            git checkout -b ${PROMOTION_BRANCH} origin/${TARGET_BRANCH}
                            
                            echo "Merging changes from ${SOURCE_BRANCH} into ${PROMOTION_BRANCH}"
                            git merge origin/${SOURCE_BRANCH} --no-edit
                            
                            git log --oneline -5
                        '''
                    }
                    
                    echo "[Stage: Promotional Branch Strategy] Promotion branch created and merged successfully"
                }
            }
        }
        
        stage('Prepare Delta Package') {
            steps {
                script {
                    echo "[Stage: Prepare Delta Package] Creating delta package..."
                    
                    sh '''
                        python3 ${SCRIPTS_DIR}/delta_package_manager.py \
                            --workspace ${WORKSPACE} \
                            --source-branch ${SOURCE_BRANCH} \
                            --target-branch ${TARGET_BRANCH} \
                            --delta-output ${DELTA_PKG_DIR} \
                            --action prepare
                    '''
                    
                    // Verify delta package was created
                    sh '''
                        if [ ! -f "${DELTA_PKG_DIR}/package.xml" ]; then
                            echo "ERROR: Delta package.xml not found"
                            exit 1
                        fi
                        
                        echo "Delta package contents:"
                        ls -la ${DELTA_PKG_DIR}/
                        echo "\nPackage.xml:"
                        head -50 ${DELTA_PKG_DIR}/package.xml
                    '''
                    
                    echo "[Stage: Prepare Delta Package] Delta package created successfully"
                }
            }
        }
        
        stage('Salesforce Org Authentication') {
            steps {
                script {
                    echo "[Stage: Salesforce Org Authentication] Authenticating to ${ENVIRONMENT} org..."
                    
                    sh '''
                        # Create auth configuration file
                        python3 ${SCRIPTS_DIR}/sfdx_auth_manager.py \
                            --action authenticate \
                            --org-username "${ORG_USERNAME}" \
                            --client-id "${CLIENT_ID}" \
                            --client-secret "${CLIENT_SECRET}" \
                            --org-alias "${ENVIRONMENT}-org" \
                            --auth-type oauth \
                            --workspace ${WORKSPACE}
                    '''
                    
                    echo "[Stage: Salesforce Org Authentication] Authentication completed"
                }
            }
        }
        
        stage('Apex PMD Analysis') {
            steps {
                script {
                    echo "[Stage: Apex PMD Analysis] Running PMD analysis on Apex code..."
                    
                    sh '''
                        # Run PMD analysis
                        python3 ${SCRIPTS_DIR}/run_pmd_analysis.py \
                            --workspace ${WORKSPACE} \
                            --delta-package ${DELTA_PKG_DIR} \
                            --report-output ${PMD_REPORT} \
                            --fail-on-violation false
                    '''
                    
                    // Archive PMD report
                    archiveArtifacts artifacts: 'pmd-report.html', allowEmptyArchive: true
                    
                    // Publish PMD findings (optional - requires PMD plugin)
                    // publishHTML([
                    //     reportDir: '.',
                    //     reportFiles: 'pmd-report.html',
                    //     reportName: 'PMD Report'
                    // ])
                    
                    echo "[Stage: Apex PMD Analysis] PMD analysis completed"
                }
            }
        }
        
        stage('Delta Package Validation') {
            steps {
                script {
                    echo "[Stage: Delta Package Validation] Validating delta package with ${TEST_LEVEL} test level..."
                    
                    sh '''
                        # Prepare validation command
                        VALIDATION_CMD="sfdx force:mdapi:deploy \
                            --deploydir ${DELTA_PKG_DIR} \
                            -u ${ENVIRONMENT}-org \
                            --checkonly \
                            --testlevel ${TEST_LEVEL}"
                        
                        # Add specified tests if provided
                        if [ "${TEST_LEVEL}" = "RunSpecifiedTests" ] && [ -n "${SPECIFIED_TESTS}" ]; then
                            VALIDATION_CMD="$VALIDATION_CMD --runtests ${SPECIFIED_TESTS}"
                        fi
                        
                        # Add additional flags
                        VALIDATION_CMD="$VALIDATION_CMD \
                            --singlepackage \
                            --wait 60 \
                            --json"
                        
                        echo "Executing validation command..."
                        eval $VALIDATION_CMD | tee ${WORKSPACE}/validation-result.json
                        
                        # Check validation result
                        VALIDATION_STATUS=$(cat ${WORKSPACE}/validation-result.json | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
                        if [ "$VALIDATION_STATUS" != "Succeeded" ]; then
                            echo "Validation failed. Exit code: $?"
                            cat ${WORKSPACE}/validation-result.json
                            exit 1
                        fi
                        
                        echo "Validation successful!"
                    '''
                    
                    // Archive validation results
                    archiveArtifacts artifacts: 'validation-result.json', allowEmptyArchive: true
                    
                    echo "[Stage: Delta Package Validation] Delta package validation completed successfully"
                }
            }
        }
        
        stage('Deploy Delta Package') {
            when {
                expression { params.VALIDATE_ONLY == false }
            }
            steps {
                script {
                    echo "[Stage: Deploy Delta Package] Deploying delta package to ${ENVIRONMENT} org..."
                    
                    sh '''
                        # Execute deployment
                        DEPLOY_CMD="sfdx force:mdapi:deploy \
                            --deploydir ${DELTA_PKG_DIR} \
                            -u ${ENVIRONMENT}-org \
                            --testlevel ${TEST_LEVEL}"
                        
                        # Add specified tests if provided
                        if [ "${TEST_LEVEL}" = "RunSpecifiedTests" ] && [ -n "${SPECIFIED_TESTS}" ]; then
                            DEPLOY_CMD="$DEPLOY_CMD --runtests ${SPECIFIED_TESTS}"
                        fi
                        
                        # Add additional flags
                        DEPLOY_CMD="$DEPLOY_CMD \
                            --singlepackage \
                            --wait 60 \
                            --json"
                        
                        echo "Executing deployment command..."
                        eval $DEPLOY_CMD | tee ${WORKSPACE}/deploy-result.json
                        
                        # Check deployment result
                        DEPLOY_STATUS=$(cat ${WORKSPACE}/deploy-result.json | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
                        if [ "$DEPLOY_STATUS" != "Succeeded" ]; then
                            echo "Deployment failed. Exit code: $?"
                            cat ${WORKSPACE}/deploy-result.json
                            exit 1
                        fi
                        
                        echo "Deployment successful!"
                    '''
                    
                    // Archive deployment results
                    archiveArtifacts artifacts: 'deploy-result.json', allowEmptyArchive: true
                    
                    echo "[Stage: Deploy Delta Package] Delta package deployed successfully"
                }
            }
        }
        
        stage('Post-Deployment: Merge to Target Branch') {
            when {
                expression { params.VALIDATE_ONLY == false && params.AUTO_MERGE == true }
            }
            steps {
                script {
                    echo "[Stage: Post-Deployment] Merging promotion branch to target branch..."
                    
                    withCredentials([usernamePassword(credentialsId: 'SFDEVOPS_GIT_CREDENTIALS', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
                        sh '''
                            cd ${WORKSPACE}
                            
                            # Configure Git
                            git config user.email "${GIT_USER_EMAIL}"
                            git config user.name "${GIT_USER_NAME}"
                            
                            # Setup remote with credentials
                            git remote set-url origin "https://${GIT_USER}:${GIT_PASS}@github.com/manand79/sfdevops.git"
                            
                            # Checkout target branch
                            echo "Checking out ${TARGET_BRANCH}..."
                            git fetch origin
                            git checkout ${TARGET_BRANCH}
                            
                            # Merge promotion branch
                            echo "Merging ${PROMOTION_BRANCH} into ${TARGET_BRANCH}..."
                            git merge ${PROMOTION_BRANCH} --no-edit
                            
                            # Push changes
                            echo "Pushing changes to origin..."
                            git push origin ${TARGET_BRANCH}
                            
                            echo "Merge completed successfully"
                        '''
                    }
                    
                    echo "[Stage: Post-Deployment] Merge completed"
                }
            }
        }
        
        stage('Cleanup') {
            when {
                expression { params.AUTO_MERGE == true }
            }
            steps {
                script {
                    echo "[Stage: Cleanup] Cleaning up promotion branch..."
                    
                    withCredentials([usernamePassword(credentialsId: 'SFDEVOPS_GIT_CREDENTIALS', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
                        sh '''
                            cd ${WORKSPACE}
                            
                            # Setup remote with credentials
                            git remote set-url origin "https://${GIT_USER}:${GIT_PASS}@github.com/manand79/sfdevops.git"
                            
                            # Delete promotion branch locally
                            git branch -D ${PROMOTION_BRANCH} || true
                            
                            # Delete promotion branch on remote
                            git push origin --delete ${PROMOTION_BRANCH} || true
                            
                            echo "Cleanup completed"
                        '''
                    }
                    
                    // Revoke SFDX authentication
                    sh '''
                        sfdx org logout --target-org ${ENVIRONMENT}-org --no-prompt || true
                    '''
                    
                    echo "[Stage: Cleanup] Cleanup completed"
                }
            }
        }
    }
    
    post {
        always {
            script {
                echo "[Post] Pipeline execution completed"
                
                // Collect artifacts
                sh '''
                    echo "Collecting deployment artifacts..."
                    mkdir -p ${WORKSPACE}/artifacts
                    
                    cp -r ${DELTA_PKG_DIR}/* ${WORKSPACE}/artifacts/ || true
                    cp ${WORKSPACE}/validation-result.json ${WORKSPACE}/artifacts/ || true
                    cp ${WORKSPACE}/deploy-result.json ${WORKSPACE}/artifacts/ || true
                    cp ${PMD_REPORT} ${WORKSPACE}/artifacts/ || true
                '''
            }
        }
        success {
            script {
                echo "[Post] Pipeline completed successfully"
                // Add success notification here (email, Slack, etc.)
            }
        }
        failure {
            script {
                echo "[Post] Pipeline failed"
                // Add failure notification here (email, Slack, etc.)
            }
        }
        unstable {
            script {
                echo "[Post] Pipeline is unstable"
                // Add unstable notification here
            }
        }
        cleanup {
            script {
                echo "[Post] Performing final cleanup"
                deleteDir()
            }
        }
    }
}
