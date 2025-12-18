# Flask Migration Test Plan

## Pre-Deployment Validation

### ✅ Completed
- [x] Flask dependencies added to Lambda layer
- [x] Flask auth utilities created
- [x] Admin Flask app created with all 14 endpoints
- [x] Player Flask app created with all 7 endpoints
- [x] CDK stack updated to use 2 Lambda functions
- [x] CDK synthesis successful
- [x] Old Lambda handlers archived to `legacy/` directory

## Deployment Steps

### 1. Deploy Updated Infrastructure

```bash
cd aws
./deploy.sh
```

Or deploy just the API stack:
```bash
cdk deploy ConsistencyTracker-API
```

**Expected Changes:**
- 2 new Lambda functions created (AdminAppFunction, PlayerAppFunction)
- 19 old Lambda functions will be deleted (replaced by Flask apps)
- API Gateway routes updated to use proxy integration

### 2. Verify Deployment

After deployment, verify:

```bash
# Check Lambda functions exist
aws lambda list-functions --query 'Functions[?contains(FunctionName, `AdminApp`) || contains(FunctionName, `PlayerApp`)].FunctionName'

# Check API Gateway routes
aws apigateway get-rest-apis --query 'items[?name==`Consistency Tracker API`].id' --output text
```

## Post-Deployment Testing

### Test Admin Endpoints (Requires Authentication)

All admin endpoints require Cognito JWT token in Authorization header.

#### 1. Authentication Test
```bash
# Get API endpoint
API_URL=$(aws cloudformation describe-stacks \
  --stack-name ConsistencyTracker-API \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

# Test check-role endpoint (requires valid JWT)
curl -X GET "${API_URL}/admin/check-role" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

**Expected:** Returns user info and admin status

#### 2. Club Management
```bash
# List clubs
curl -X GET "${API_URL}/admin/clubs" \
  -H "Authorization: Bearer <JWT_TOKEN>"

# Get specific club
curl -X GET "${API_URL}/admin/clubs/{clubId}" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

#### 3. Player Management
```bash
# List players
curl -X GET "${API_URL}/admin/players" \
  -H "Authorization: Bearer <JWT_TOKEN>"

# Create player
curl -X POST "${API_URL}/admin/players" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Player", "teamId": "test-team-id"}'
```

#### 4. Content Management
```bash
# List content
curl -X GET "${API_URL}/admin/content" \
  -H "Authorization: Bearer <JWT_TOKEN>"

# Image upload URL
curl -X POST "${API_URL}/admin/content/image-upload-url" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"fileName": "test.jpg", "contentType": "image/jpeg"}'
```

### Test Player Endpoints (No Authentication)

#### 1. Get Player Data
```bash
curl -X GET "${API_URL}/player/{uniqueLink}"
```

**Expected:** Returns player data and current week activities

#### 2. Check-in
```bash
curl -X POST "${API_URL}/player/{uniqueLink}/checkin" \
  -H "Content-Type: application/json" \
  -d '{"activityId": "test-activity-id", "date": "2024-01-15", "completed": true}'
```

#### 3. Get Leaderboard
```bash
curl -X GET "${API_URL}/leaderboard/2024-03?uniqueLink={uniqueLink}&scope=team"
```

#### 4. Get Content
```bash
curl -X GET "${API_URL}/content?uniqueLink={uniqueLink}"
curl -X GET "${API_URL}/content/test-slug?uniqueLink={uniqueLink}"
```

## Validation Checklist

### Functionality
- [ ] All 14 admin endpoints respond correctly
- [ ] All 7 player endpoints respond correctly
- [ ] Cognito authentication works on admin endpoints
- [ ] Multi-tenancy validation (club/team access control) works
- [ ] Response format matches existing API format
- [ ] Error handling returns correct status codes

### Performance
- [ ] Cold start times acceptable (< 3 seconds)
- [ ] Warm requests respond quickly (< 500ms)
- [ ] Memory usage within limits
- [ ] No timeout errors

### Security
- [ ] Admin endpoints reject unauthenticated requests (401)
- [ ] Admin endpoints reject non-admin users (403)
- [ ] Club/team access control prevents cross-club access
- [ ] CORS headers correct
- [ ] Input validation working

## Rollback Plan

If issues are found:

1. **Quick Rollback:**
   ```bash
   # Restore old handlers
   cd aws/lambda
   cp legacy/admin/*.py admin/
   cp legacy/player/*.py .
   
   # Revert CDK changes
   git checkout aws/stacks/api_stack.py
   
   # Redeploy
   cdk deploy ConsistencyTracker-API
   ```

2. **Full Rollback:**
   - Restore from git commit before Flask migration
   - Redeploy all stacks

## Monitoring

After deployment, monitor:

1. **CloudWatch Logs:**
   - `/aws/lambda/AdminAppFunction`
   - `/aws/lambda/PlayerAppFunction`

2. **CloudWatch Metrics:**
   - Lambda invocations
   - Lambda errors
   - Lambda duration
   - API Gateway 4xx/5xx errors

3. **Key Metrics to Watch:**
   - Error rate should be < 1%
   - Average duration should be similar to before
   - Cold start frequency

## Success Criteria

✅ All endpoints functional  
✅ Authentication/authorization working  
✅ Multi-tenancy validation working  
✅ Response format compatible  
✅ Performance acceptable  
✅ No increase in error rate  

## Post-Migration Cleanup

After 1-2 weeks of successful operation:

1. Delete legacy Lambda handler files
2. Update documentation
3. Remove old Lambda function CloudWatch log groups (optional)

