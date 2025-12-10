import { Amplify } from 'aws-amplify'

const cognitoUserPoolId = import.meta.env.VITE_COGNITO_USER_POOL_ID
const cognitoUserPoolClientId = import.meta.env.VITE_COGNITO_USER_POOL_CLIENT_ID

if (!cognitoUserPoolId || !cognitoUserPoolClientId) {
  console.warn('Cognito configuration missing. Please set VITE_COGNITO_USER_POOL_ID and VITE_COGNITO_USER_POOL_CLIENT_ID environment variables.')
}

const amplifyConfig = {
  Auth: {
    Cognito: {
      userPoolId: cognitoUserPoolId || '',
      userPoolClientId: cognitoUserPoolClientId || '',
    },
  },
}

Amplify.configure(amplifyConfig)

export default amplifyConfig

