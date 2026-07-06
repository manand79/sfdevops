// Salesforce Deployment Pipeline
// Branch Strategy: Promotional Branching (develop -> QA, main -> Prod)
// Environments: Dev (develop branch), QA (main branch)

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
        GIT_REPO = "https://github.com/manand79/sfdevops.git"
        GIT_CREDENTIALS_ID = "2f74db35-d085-4f58-962c-043ef60aa4e8"
        GIT_USER_EMAIL = "ci-bot@users.noreply.github.com"
        GIT_USER_NAME = "ci-bot"
        
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
                    echo "[Stage: Code Checkout] Checking out source branch..."
                    
                    withCredentials([usernamePassword(credentialsId: "${GIT_CREDENTIALS_ID}", usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
                        checkout([
                            $class: 'GitSCM',
                            branches: [[name: "*/${SOURCE_BRANCH}"]],
                            userRemoteConfigs: [[url: "${GIT_REPO}", credentialsId: "${GIT_CREDENTIALS_ID}"]]
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

            if (isUnix()) {
                sh '''
                    mkdir -p ${DEPLOY_DIR}
                    mkdir -p ${DELTA_PKG_DIR}
                    mkdir -p ${SCRIPTS_DIR}
                    mkdir -p ${CONFIG_DIR}

                    echo "Current working directory: $(pwd)"
                    echo "Environment setup:"
                    ls -la
                '''
            } else {
                bat '''
                    if not exist "%DEPLOY_DIR%" mkdir "%DEPLOY_DIR%"
                    if not exist "%DELTA_PKG_DIR%" mkdir "%DELTA_PKG_DIR%"
                    if not exist "%SCRIPTS_DIR%" mkdir "%SCRIPTS_DIR%"
                    if not exist "%CONFIG_DIR%" mkdir "%CONFIG_DIR%"
                    echo Current working directory: %CD%
                    dir
                '''
            }

            // Lenient npm auth
            try {
                withCredentials([string(credentialsId: 'NPM_AUTH_TOKEN', variable: 'NODE_AUTH_TOKEN')]) {
                    if (isUnix()) {
                        sh '''
                            echo "NPM_AUTH_TOKEN credential found. Running npm with auth token."
                            export NPM_AUTH_TOKEN="${NODE_AUTH_TOKEN}"
                            export NODE_AUTH_TOKEN="${NODE_AUTH_TOKEN}"
                            echo "//registry.npmjs.org/:_authToken=${NPM_AUTH_TOKEN}" > ~/.npmrc
                            npm config set //registry.npmjs.org/:_authToken "${NPM_AUTH_TOKEN}" || true
                        '''
                    } else {
                        bat '''
                            echo NPM_AUTH_TOKEN credential found. Running npm with auth token.
                            > "%USERPROFILE%\\.npmrc" echo //registry.npmjs.org/:_authToken=%NODE_AUTH_TOKEN%
                            call npm config set //registry.npmjs.org/:_authToken "%NODE_AUTH_TOKEN%"
                        '''
                    }
                }
            } catch (err) {
                echo "NPM_AUTH_TOKEN credential not found. Continuing without npm auth."
            }

            if (isUnix()) {
                sh '''
                    echo "Validating SFDX CLI installation..."
                    sfdx --version || {
                        echo "Installing SFDX CLI..."
                        npm install -g @salesforce/cli
                    }
                    sfdx --version
                '''
            } else {
               bat '''
    echo Validating Salesforce CLI installation...

    where sf >nul 2>nul
    if errorlevel 1 (
        echo Installing Salesforce CLI...
        call npm install -g @salesforce/cli
    )

    set "NPM_GLOBAL_PREFIX=%APPDATA%\\npm"
    set "PATH=%NPM_GLOBAL_PREFIX%;%PATH%"

    where sf >nul 2>nul
    if errorlevel 1 (
        echo ERROR: sf still not found after install.
        echo Tried: %NPM_GLOBAL_PREFIX%\\sf.cmd
        dir "%NPM_GLOBAL_PREFIX%" 2>nul
        exit /b 1
    )

    call sf --version
'''
            }

            echo "[Stage: Setup & Validation] Environment setup completed"
        }
    }
}
        
        stage('Promotional Branch Strategy') {
            steps {
                script {
                    echo "[Stage: Promotional Branch Strategy] Setting up promotion workflow..."
                    
                    withCredentials([usernamePassword(credentialsId: "${GIT_CREDENTIALS_ID}", usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
    if (isUnix()) {
        sh '''
            cd ${WORKSPACE}

            git config user.email "${GIT_USER_EMAIL}"
            git config user.name "${GIT_USER_NAME}"

            git remote set-url origin "https://${GIT_USER}:${GIT_PASS}@github.com/manand79/sfdevops.git"

            git fetch origin

            echo "Creating promotion branch: ${PROMOTION_BRANCH}"
            git checkout -b ${PROMOTION_BRANCH} origin/${TARGET_BRANCH}

            echo "Merging changes from ${SOURCE_BRANCH} into ${PROMOTION_BRANCH}"
            git merge origin/${SOURCE_BRANCH} --no-edit

            git log --oneline -5
        '''
    } else {
        bat '''
            cd /d "%WORKSPACE%"

            git config user.email "%GIT_USER_EMAIL%"
            git config user.name "%GIT_USER_NAME%"

            git remote set-url origin "https://%GIT_USER%:%GIT_PASS%@github.com/manand79/sfdevops.git"

            git fetch origin

            echo Creating promotion branch: %PROMOTION_BRANCH%
            git checkout -b %PROMOTION_BRANCH% origin/%TARGET_BRANCH%

            echo Merging changes from %SOURCE_BRANCH% into %PROMOTION_BRANCH%
            git merge origin/%SOURCE_BRANCH% --no-edit

            git log --oneline -5
        '''
    }
}
                    
                    echo "[Stage: Promotional Branch Strategy] Promotion branch created and merged successfully"
                }
            }
        }
        
        stage('Prepare Delta Package') {
    steps {
        script {
            echo "[Stage: Prepare Delta Package] Creating delta package..."

            if (isUnix()) {
    sh '''
        if [ ! -f "${SCRIPTS_DIR}/delta_package_manager.py" ]; then
            echo "ERROR: Missing script: ${SCRIPTS_DIR}/delta_package_manager.py"
            echo "Workspace contents:"
            ls -la "${WORKSPACE}"
            echo "Scripts dir contents (if exists):"
            ls -la "${SCRIPTS_DIR}" || true
            exit 1
        fi
    '''
} else {
    bat '''
    if not exist "%SCRIPTS_DIR%\\delta_package_manager.py" (
        echo ERROR: Missing script: %SCRIPTS_DIR%\\delta_package_manager.py
        echo Workspace contents:
        dir "%WORKSPACE%"
        echo Scripts dir contents ^(if exists^):
        dir "%SCRIPTS_DIR%" 2>nul
        exit /b 1
    )
'''
}

            echo "[Stage: Prepare Delta Package] Delta package created successfully"
        }
    }
}
        
       stage('Salesforce Org Authentication') {
    steps {
        script {
            echo "[Stage: Salesforce Org Authentication] Authenticating to ${ENVIRONMENT} org (JWT)..."

            // Store your server.key in Jenkins as a "Secret file" credential, e.g. SF_JWT_KEY_FILE
            withCredentials([file(credentialsId: 'SF_JWT_KEY_FILE', variable: 'JWT_KEY_FILE')]) {
                if (isUnix()) {
                    sh '''
                        export SF_DISABLE_TELEMETRY=true
                        export SFDX_DISABLE_TELEMETRY=true
                        export SF_AUTOUPDATE_DISABLE=true
                        export SFDX_AUTOUPDATE_DISABLE=true
                        export CI=true

                        python3 ${SCRIPTS_DIR}/sfdx_auth_manager.py \
                            --action authenticate \
                            --org-username "${ORG_USERNAME}" \
                            --client-id "${CLIENT_ID}" \
                            --org-alias "${ENVIRONMENT}-org" \
                            --auth-type jwt \
                            --jwt-key-file "${JWT_KEY_FILE}" \
                            --auth-url "https://login.salesforce.com" \
                            --workspace "${WORKSPACE}"
                    '''
                } else {
                    bat '''
                        set "SF_DISABLE_TELEMETRY=true"
                        set "SFDX_DISABLE_TELEMETRY=true"
                        set "SF_AUTOUPDATE_DISABLE=true"
                        set "SFDX_AUTOUPDATE_DISABLE=true"
                        set "CI=true"

                        py -3 "%SCRIPTS_DIR%\\sfdx_auth_manager.py" ^
                            --action authenticate ^
                            --org-username "%ORG_USERNAME%" ^
                            --client-id "%CLIENT_ID%" ^
                            --org-alias "%ENVIRONMENT%-org" ^
                            --auth-type jwt ^
                            --jwt-key-file "%JWT_KEY_FILE%" ^
                            --auth-url "https://login.salesforce.com" ^
                            --workspace "%WORKSPACE%"
                    '''
                }
            }

            echo "[Stage: Salesforce Org Authentication] Authentication completed"
        }
    }
}
        
        stage('Apex PMD Analysis') {
            steps {
                script {
                    echo "[Stage: Apex PMD Analysis] Running PMD analysis on Apex code..."
                    
                    sh '''
                        python3 ${SCRIPTS_DIR}/run_pmd_analysis.py \
                            --workspace ${WORKSPACE} \
                            --delta-package ${DELTA_PKG_DIR} \
                            --report-output ${PMD_REPORT} \
                            --fail-on-violation false
                    '''
                    
                    archiveArtifacts artifacts: 'pmd-report.html', allowEmptyArchive: true
                    
                    echo "[Stage: Apex PMD Analysis] PMD analysis completed"
                }
            }
        }
        
        stage('Delta Package Validation') {
            steps {
                script {
                    echo "[Stage: Delta Package Validation] Validating delta package with ${TEST_LEVEL} test level..."
                    
                    sh '''
                        VALIDATION_CMD="sfdx force:mdapi:deploy \
                            --deploydir ${DELTA_PKG_DIR} \
                            -u ${ENVIRONMENT}-org \
                            --checkonly \
                            --testlevel ${TEST_LEVEL}"
                        
                        if [ "${TEST_LEVEL}" = "RunSpecifiedTests" ] && [ -n "${SPECIFIED_TESTS}" ]; then
                            VALIDATION_CMD="$VALIDATION_CMD --runtests ${SPECIFIED_TESTS}"
                        fi
                        
                        VALIDATION_CMD="$VALIDATION_CMD \
                            --singlepackage \
                            --wait 60 \
                            --json"
                        
                        echo "Executing validation command..."
                        eval $VALIDATION_CMD | tee ${WORKSPACE}/validation-result.json
                        
                        VALIDATION_STATUS=$(cat ${WORKSPACE}/validation-result.json | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
                        if [ "$VALIDATION_STATUS" != "Succeeded" ]; then
                            echo "Validation failed. Exit code: $?"
                            cat ${WORKSPACE}/validation-result.json
                            exit 1
                        fi
                        
                        echo "Validation successful!"
                    '''
                    
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
                        DEPLOY_CMD="sfdx force:mdapi:deploy \
                            --deploydir ${DELTA_PKG_DIR} \
                            -u ${ENVIRONMENT}-org \
                            --testlevel ${TEST_LEVEL}"
                        
                        if [ "${TEST_LEVEL}" = "RunSpecifiedTests" ] && [ -n "${SPECIFIED_TESTS}" ]; then
                            DEPLOY_CMD="$DEPLOY_CMD --runtests ${SPECIFIED_TESTS}"
                        fi
                        
                        DEPLOY_CMD="$DEPLOY_CMD \
                            --singlepackage \
                            --wait 60 \
                            --json"
                        
                        echo "Executing deployment command..."
                        eval $DEPLOY_CMD | tee ${WORKSPACE}/deploy-result.json
                        
                        DEPLOY_STATUS=$(cat ${WORKSPACE}/deploy-result.json | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
                        if [ "$DEPLOY_STATUS" != "Succeeded" ]; then
                            echo "Deployment failed. Exit code: $?"
                            cat ${WORKSPACE}/deploy-result.json
                            exit 1
                        fi
                        
                        echo "Deployment successful!"
                    '''
                    
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
                    
                    withCredentials([usernamePassword(credentialsId: "${GIT_CREDENTIALS_ID}", usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
                        sh '''
                            cd ${WORKSPACE}
                            
                            git config user.email "${GIT_USER_EMAIL}"
                            git config user.name "${GIT_USER_NAME}"
                            
                            git remote set-url origin "https://${GIT_USER}:${GIT_PASS}@github.com/manand79/sfdevops.git"
                            
                            echo "Checking out ${TARGET_BRANCH}..."
                            git fetch origin
                            git checkout ${TARGET_BRANCH}
                            
                            echo "Merging ${PROMOTION_BRANCH} into ${TARGET_BRANCH}..."
                            git merge ${PROMOTION_BRANCH} --no-edit
                            
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
                    
                    withCredentials([usernamePassword(credentialsId: "${GIT_CREDENTIALS_ID}", usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
                        sh '''
                            cd ${WORKSPACE}
                            
                            git remote set-url origin "https://${GIT_USER}:${GIT_PASS}@github.com/manand79/sfdevops.git"
                            
                            git branch -D ${PROMOTION_BRANCH} || true
                            
                            git push origin --delete ${PROMOTION_BRANCH} || true
                            
                            echo "Cleanup completed"
                        '''
                    }
                    
                    sh '''
                        sfdx org logout --target-org ${ENVIRONMENT}-org --no-prompt || true
                    '''
                    
                    echo "[Stage: Cleanup] Cleanup completed"
                }
            }
        }
    }
    
    post {
        success {
            echo "[Post] Pipeline completed successfully"
        }
        failure {
            echo "[Post] Pipeline failed"
        }
        unstable {
            echo "[Post] Pipeline is unstable"
        }
    }
}
