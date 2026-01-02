# Security Documentation

This document outlines the security measures implemented in the Consistency Tracker application, with a focus on email verification and API security.

## Table of Contents

1. [Overview](#overview)
2. [Email Verification Security](#email-verification-security)
3. [API Gateway Security](#api-gateway-security)
4. [Authentication & Authorization](#authentication--authorization)
5. [Data Protection](#data-protection)
6. [Monitoring & Logging](#monitoring--logging)
7. [Incident Response](#incident-response)

## Overview

The Consistency Tracker application implements multiple layers of security to protect user data and prevent abuse. This document details the security measures for email verification, API endpoints, and overall system security.

## Email Verification Security

### Token Generation

Email verification tokens are generated using HMAC-SHA256 signed tokens instead of simple UUIDs. This provides:

- **Tamper-proof tokens**: Tokens cannot be modified without invalidating the signature
- **Cryptographic security**: Uses industry-standard HMAC-SHA256 algorithm
- **Token structure**: `{base64(payload)}.{hmac_signature}`

**Token Payload:**
- `email`: Email address to verify
- `exp`: Expiration timestamp (Unix epoch)
- `iat`: Issued at timestamp
- `jti`: Unique token ID (UUID)

**Secret Management:**
- Secret key stored in `EMAIL_VERIFICATION_SECRET` environment variable
- TODO: Move to AWS Secrets Manager or Parameter Store for production

### Token Expiration

- **Expiration time**: 1 hour (reduced from 24 hours for enhanced security)
- **Automatic cleanup**: Expired tokens are automatically deleted via DynamoDB TTL
- **One-time use**: Tokens are marked as "used" after successful verification

### Token Resend

Users can request a new verification email if their token expires or is lost.

**Security measures:**
- **Rate limiting**: Maximum 1 request per 5 minutes per email address
- **Email verification check**: Does not resend if email is already verified
- **Token invalidation**: All pending tokens for the email are invalidated before generating a new one
- **Generic responses**: Does not reveal whether an email address exists in the system

**Endpoint**: `POST /resend-verification-email`

### Rate Limiting

Multiple layers of rate limiting protect the email verification system:

1. **Per-endpoint throttling** (API Gateway):
   - 10 requests per second
   - Burst limit: 20 requests

2. **WAF rate limiting**:
   - 100 requests per 5 minutes per IP address for `/verify-email` endpoint
   - Blocks requests that exceed the limit

3. **Application-level rate limiting**:
   - Resend requests: 1 per 5 minutes per email address
   - Tracked in DynamoDB with automatic TTL cleanup

### Brute-Force Protection

The email verification endpoint includes brute-force protection:

- **Failed attempt tracking**: Tracks failed verification attempts per IP address
- **Lockout threshold**: 5 failed attempts per IP address
- **Lockout duration**: 5 minutes
- **Automatic cleanup**: Failed attempt records expire after 1 hour (TTL)
- **Success clearing**: Successful verifications clear failed attempts for the IP

**Implementation:**
- DynamoDB table: `ConsistencyTracker-VerificationAttempts`
- Partition key: `ipAddress`
- Attributes: `failedAttempts`, `lastAttempt`, `lockedUntil`, `expiresAt`

## API Gateway Security

### CORS Configuration

Cross-Origin Resource Sharing (CORS) is configured to restrict access to specific domains:

- **Allowed origins**: 
  - `https://repwarrior.net`
  - `https://www.repwarrior.net`
- **Allowed methods**: GET, POST, PUT, DELETE, OPTIONS, PATCH
- **Allowed headers**: Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token
- **Credentials**: Enabled for authenticated requests

### Throttling

API Gateway implements throttling at multiple levels:

1. **Global throttling** (API Gateway stage):
   - 1000 requests per second
   - Burst limit: 2000 requests

2. **Per-endpoint throttling**:
   - `/verify-email`: 10 requests/second, burst: 20

### WAF Protection

AWS WAF (Web Application Firewall) provides additional protection:

- **Scope**: REGIONAL (for API Gateway)
- **Rate-based rules**: 
  - `/verify-email` endpoint: 100 requests per 5 minutes per IP
- **CloudWatch metrics**: Enabled for monitoring
- **Sampled requests**: Enabled for analysis

**WAF Rules:**
- Priority 1: VerifyEmailRateLimit (blocks excessive requests to `/verify-email`)

## Authentication & Authorization

### Cognito User Pool

- **User authentication**: AWS Cognito handles all user authentication
- **Email verification**: Required before users can log in
- **Password policy**: Enforced by Cognito
- **Multi-factor authentication**: Can be enabled via Cognito settings

### Role-Based Access Control

- **App Admins**: Platform-wide administrators with highest privileges
- **Club Admins**: Administrators for specific clubs
- **Coaches**: Access to team-specific data
- **Players**: Access to their own data and team leaderboards

### API Endpoints

- **Public endpoints**: 
  - `/verify-email` (POST)
  - `/resend-verification-email` (POST)
- **Authenticated endpoints**: All other endpoints require valid JWT tokens
- **Authorization**: Role-based access control enforced at the application level

## Data Protection

### Encryption

- **In transit**: All API communication uses TLS 1.2+
- **At rest**: DynamoDB encryption enabled
- **S3**: Server-side encryption for stored content

### Data Storage

- **DynamoDB**: All application data stored in DynamoDB with encryption at rest
- **TTL**: Automatic cleanup of temporary data (verification tokens, failed attempts)
- **Point-in-time recovery**: Enabled for critical tables

### PII Protection

- **Email addresses**: Stored securely, not exposed in error messages
- **Generic error responses**: Public endpoints return generic messages to prevent enumeration
- **Token security**: Tokens are signed and cannot be tampered with

## Monitoring & Logging

### CloudWatch Logs

- **Lambda functions**: All Lambda functions log to CloudWatch
- **API Gateway**: Request/response logging enabled
- **Log retention**: 7 days for Lambda functions

### Metrics

- **WAF metrics**: CloudWatch metrics for rate limiting and blocking
- **API Gateway metrics**: Request counts, latency, error rates
- **DynamoDB metrics**: Read/write capacity, throttling

### Alarms

Recommended CloudWatch alarms (to be configured):
- High error rate on verification endpoints
- WAF blocking excessive requests
- DynamoDB throttling
- Lambda function errors

## Incident Response

### Security Incident Procedures

1. **Detection**: Monitor CloudWatch logs and metrics for anomalies
2. **Investigation**: Review failed attempts, blocked requests, error patterns
3. **Response**: 
   - Block malicious IPs via WAF if needed
   - Review and rotate secrets if compromised
   - Notify affected users if data breach suspected
4. **Recovery**: 
   - Restore from backups if needed
   - Update security measures based on incident

### Security Best Practices

1. **Secret rotation**: Rotate `EMAIL_VERIFICATION_SECRET` regularly
2. **Monitoring**: Set up CloudWatch alarms for security events
3. **Updates**: Keep dependencies and AWS services up to date
4. **Audit**: Regularly review access logs and failed attempts
5. **Testing**: Perform security testing before production deployments

### Known Limitations

- **Secret storage**: Currently using environment variables; should migrate to AWS Secrets Manager
- **IP-based blocking**: May affect legitimate users behind shared IPs (NAT, corporate networks)
- **Token expiration**: 1-hour expiration may be too short for some users (mitigated by resend functionality)

## Related Documentation

- [API Configuration](configuration/API_CONFIGURATION.md)
- [Email Setup](email/EMAIL_SETUP.md)
- [Deployment Guide](deployment/DEPLOYMENT_README.md)

## Security Contact

For security concerns or to report vulnerabilities, please contact the development team.

