# Cognito Configuration Fix

## Issue
Multiple 400 errors from `cognito-idp.us-east-1.amazonaws.com` indicating AWS Cognito authentication configuration problems.

## Root Causes
1. **Missing AWS Region**: The Amplify configuration was missing the `region` parameter
2. **Missing Environment Variables**: No `.env` file with Cognito credentials for local development
3. **Incomplete Configuration**: Amplify v6 requires explicit region configuration

## Fixes Applied

### 1. Updated `app/src/config/aws-config.ts`
- ✅ Added region configuration (extracts from User Pool ID or uses `VITE_AWS_REGION`)
- ✅ Added better error messages when configuration is missing
- ✅ Added validation to only configure Amplify when credentials are present
- ✅ Added success logging when configuration is valid

### 2. Created `.env` file
Created `/app/.env` with:
```env
VITE_COGNITO_USER_POOL_ID=us-east-1_1voH0LIGL
VITE_COGNITO_USER_POOL_CLIENT_ID=5bqs4fe26rmer34rs564pkcdeu
VITE_AWS_REGION=us-east-1
VITE_API_URL=https://api.repwarrior.net
```

## Next Steps

### ⚠️ IMPORTANT: Restart Dev Server
The Vite dev server needs to be restarted to pick up the new `.env` file:

1. **Stop the current dev server** (Ctrl+C in the terminal where it's running)
2. **Restart the dev server**:
   ```bash
   cd app
   npm run dev
   ```
3. **Check the browser console** - you should now see:
   ```
   ✅ AWS Amplify configured successfully
      Region: us-east-1
      User Pool: us-east-1_1voH0LIGL...
   ```

### Verify the Fix
After restarting, check:
1. ✅ No more 400 errors from Cognito
2. ✅ Console shows "AWS Amplify configured successfully"
3. ✅ Login form can communicate with Cognito
4. ✅ Authentication attempts work (even if credentials are wrong, you shouldn't see 400 errors)

## Configuration Details

### Environment Variables
- `VITE_COGNITO_USER_POOL_ID`: Your Cognito User Pool ID
- `VITE_COGNITO_USER_POOL_CLIENT_ID`: Your Cognito App Client ID
- `VITE_AWS_REGION`: AWS region (defaults to us-east-1)
- `VITE_API_URL`: API endpoint URL

### Region Detection
The configuration now:
1. Uses `VITE_AWS_REGION` if set
2. Extracts region from User Pool ID (format: `us-east-1_XXXXXXXXX`)
3. Falls back to `us-east-1` as default

## Troubleshooting

If you still see errors after restarting:

1. **Check .env file exists**:
   ```bash
   ls -la app/.env
   cat app/.env
   ```

2. **Verify environment variables are loaded**:
   - Check browser console for configuration messages
   - Look for "Cognito configuration missing" warnings

3. **Check User Pool ID format**:
   - Should be: `us-east-1_XXXXXXXXX` (region_prefix)
   - Verify in AWS Console: Cognito → User Pools → Your Pool → General Settings

4. **Verify Client ID**:
   - Check in AWS Console: Cognito → User Pools → Your Pool → App Integration → App Clients

5. **Check network requests**:
   - Open browser DevTools → Network tab
   - Look for requests to `cognito-idp.us-east-1.amazonaws.com`
   - Check if they're now returning 200 instead of 400

## Related Files
- `app/src/config/aws-config.ts` - Amplify configuration
- `app/.env` - Environment variables (not in git)
- `API_CONFIGURATION.md` - API and Cognito configuration documentation

