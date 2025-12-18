# Flask Migration - Deployment Readiness

## ✅ Pre-Deployment Checklist

### Code Changes
- [x] Flask dependencies added to Lambda layer
- [x] Admin Flask app created (14 endpoints)
- [x] Player Flask app created (7 endpoints)
- [x] Flask auth utilities created
- [x] CDK stack updated for 2 Lambda functions
- [x] Old handlers archived to `legacy/` directory

### Validation
- [x] CDK synthesis successful
- [x] All required files exist
- [x] Flask apps syntactically correct
- [x] Lambda functions configured correctly

### Documentation
- [x] Test plan created (`FLASK_MIGRATION_TEST_PLAN.md`)
- [x] Migration summary created (`FLASK_MIGRATION_SUMMARY.md`)
- [x] Legacy files documented (`lambda/legacy/README.md`)

## 🚀 Deployment Command

```bash
cd aws
./deploy.sh
```

Or deploy just the API stack:
```bash
cd aws
source .venv/bin/activate
cdk deploy ConsistencyTracker-API
```

## 📊 Expected Changes

### Lambda Functions
- **Will Create:** 2 new functions (AdminAppFunction, PlayerAppFunction)
- **Will Delete:** 19 old Lambda functions (replaced by Flask apps)
- **Will Update:** 2 existing functions (if any remain)

### API Gateway
- Routes updated to use proxy integration
- All `/admin/*` routes → AdminAppFunction
- All `/player/*`, `/leaderboard/*`, `/content/*` routes → PlayerAppFunction
- Cognito authorizer still attached to admin routes

### No Data Impact
- ✅ DynamoDB tables unchanged
- ✅ Cognito User Pool unchanged
- ✅ S3 buckets unchanged
- ✅ All data preserved

## ⚠️ Important Notes

1. **Deployment Time:** ~10-15 minutes for API stack update
2. **Downtime:** Minimal (API Gateway will route to new functions)
3. **Rollback:** Available via `legacy/` directory files
4. **Testing:** Test all endpoints after deployment

## 🔍 Post-Deployment Verification

1. **Check Lambda Functions:**
   ```bash
   aws lambda list-functions --query 'Functions[?contains(FunctionName, `App`)].FunctionName'
   ```

2. **Test Admin Endpoint:**
   ```bash
   curl -X GET "${API_URL}/admin/check-role" \
     -H "Authorization: Bearer <JWT_TOKEN>"
   ```

3. **Test Player Endpoint:**
   ```bash
   curl -X GET "${API_URL}/player/{uniqueLink}"
   ```

4. **Monitor CloudWatch Logs:**
   - Check for errors in `/aws/lambda/AdminAppFunction`
   - Check for errors in `/aws/lambda/PlayerAppFunction`

## 📝 Next Actions

1. **Deploy** the updated infrastructure
2. **Test** all endpoints (see test plan)
3. **Monitor** for 24-48 hours
4. **Validate** all functionality
5. **Cleanup** legacy files after 1-2 weeks

## 🆘 Support

If issues occur:
1. Check CloudWatch logs for errors
2. Review test plan for validation steps
3. Use rollback plan if needed
4. All original code preserved in `lambda/legacy/`

