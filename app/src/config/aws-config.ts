import { Amplify } from 'aws-amplify'

const cognitoUserPoolId = import.meta.env.VITE_COGNITO_USER_POOL_ID
const cognitoUserPoolClientId = import.meta.env.VITE_COGNITO_USER_POOL_CLIENT_ID
const awsRegion = import.meta.env.VITE_AWS_REGION || 'us-east-1'

if (!cognitoUserPoolId || !cognitoUserPoolClientId) {
  console.error('❌ Cognito configuration missing!')
  console.error('Please set the following environment variables:')
  console.error('  - VITE_COGNITO_USER_POOL_ID')
  console.error('  - VITE_COGNITO_USER_POOL_CLIENT_ID')
  console.error('')
  console.error('Create a .env file in the app/ directory with:')
  console.error('  VITE_COGNITO_USER_POOL_ID=us-east-1_1voH0LIGL')
  console.error('  VITE_COGNITO_USER_POOL_CLIENT_ID=5bqs4fe26rmer34rs564pkcdeu')
  console.error('  VITE_AWS_REGION=us-east-1')
}

// Extract region from User Pool ID if not explicitly set
// User Pool ID format: us-east-1_XXXXXXXXX
const regionFromPoolId = cognitoUserPoolId?.match(/^([a-z0-9-]+)_/)?.[1]
const finalRegion = awsRegion || regionFromPoolId || 'us-east-1'

const amplifyConfig = {
  Auth: {
    Cognito: {
      userPoolId: cognitoUserPoolId || '',
      userPoolClientId: cognitoUserPoolClientId || '',
    },
  },
  // Explicitly set the region for all AWS services
  region: finalRegion,
}

// Only configure Amplify if we have the required values
if (cognitoUserPoolId && cognitoUserPoolClientId) {
  Amplify.configure(amplifyConfig)
  console.log('✅ AWS Amplify configured successfully')
  console.log(`   Region: ${finalRegion}`)
  console.log(`   User Pool: ${cognitoUserPoolId.substring(0, 20)}...`)
} else {
  console.error('⚠️  AWS Amplify not configured - authentication will not work')
}

export default amplifyConfig

