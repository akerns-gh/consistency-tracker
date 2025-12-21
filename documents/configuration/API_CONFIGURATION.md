# API Configuration

## Custom Domain Setup

The API is configured to use a custom domain: `https://api.repwarrior.net`

### Frontend Configuration

The frontend automatically uses the custom domain. The API base URL is configured in:

- **File:** `app/src/services/api.ts`
- **Default:** `https://api.repwarrior.net`
- **Environment Variable:** `VITE_API_URL` (optional, defaults to custom domain)

### Deployment Script

The deployment script (`scripts-frontend/deploy-frontend.sh`) is configured to:
1. Use the custom domain `https://api.repwarrior.net` by default
2. Fall back to direct API Gateway URL if custom domain is unavailable
3. Automatically set `VITE_API_URL` during build

### API Endpoints

**Custom Domain (Recommended):**
- Base URL: `https://api.repwarrior.net`
- Player endpoints: `https://api.repwarrior.net/player/...`
- Admin endpoints: `https://api.repwarrior.net/admin/...`

**Direct API Gateway (Fallback):**
- Base URL: `https://tnobyn4jbf.execute-api.us-east-1.amazonaws.com/prod`
- Note: Requires `/prod` stage path in URL

### Testing

Test the custom domain:
```bash
curl https://api.repwarrior.net/player/test-link
```

### Configuration Files

- `app/src/services/api.ts` - Frontend API client configuration
- `scripts-frontend/deploy-frontend.sh` - Deployment script with API URL configuration
- `app/src/config/aws-config.ts` - AWS Amplify/Cognito configuration

### Environment Variables

For local development, create `.env` in the `app/` directory:
```env
VITE_API_URL=https://api.repwarrior.net
VITE_COGNITO_USER_POOL_ID=us-east-1_1voH0LIGL
VITE_COGNITO_USER_POOL_CLIENT_ID=5bqs4fe26rmer34rs564pkcdeu
```

