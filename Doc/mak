# Route 53 DNS Records Restoration Guide

## Overview
This guide provides step-by-step instructions for restoring Route 53 DNS records from backups. Follow these procedures carefully to ensure a successful restoration.

## Pre-Restoration Checklist

1. **Verify Access**
   - [ ] AWS Console access with appropriate permissions
   - [ ] Access to S3 backup bucket
   - [ ] Route 53 administrative access
   - [ ] Lambda function access

2. **Backup Identification**
   - [ ] Identify correct backup timestamp
   - [ ] Verify backup file exists
   - [ ] Review backup content before restoration

3. **Environment Preparation**
   - [ ] Note current DNS configuration
   - [ ] Prepare rollback plan
   - [ ] Notify stakeholders

## Restoration Process

### 1. Locate Backup File

1. Navigate to S3 bucket:
```bash
aws s3 ls s3://YOUR_BUCKET_NAME/YYYY-MM-DD/
```

2. Download and verify backup content:
```bash
aws s3 cp s3://YOUR_BUCKET_NAME/YYYY-MM-DD/example.com/route53_backup.json .
cat route53_backup.json
```

### 2. Initiate Restoration

#### Method 1: Using AWS Lambda Console

1. Open AWS Lambda Console
2. Navigate to the restore function
3. Create test event with payload:
```json
{
    "backup_key": "YYYYMMDD_HHMMSS/example.com/route53_backup.json",
    "hosted_zone_id": "/hostedzone/YOUR_ZONE_ID"
}
```
4. Execute test

#### Method 2: Using AWS CLI

```bash
aws lambda invoke \
    --function-name Route53Restore \
    --payload '{"backup_key":"YYYYMMDD_HHMMSS/example.com/route53_backup.json","hosted_zone_id":"/hostedzone/YOUR_ZONE_ID"}' \
    response.json
```

### 3. Verification Steps

1. **Check Route 53 Console**
   - Verify record sets are restored
   - Compare record count with backup

2. **DNS Resolution Testing**
```bash
# Test DNS resolution
dig @ns-XXXX.awsdns-XX.com example.com
dig @ns-XXXX.awsdns-XX.com example.com MX
```

3. **Application Testing**
   - Test all critical services
   - Verify SSL/TLS certificates
   - Check email delivery (if MX records involved)

### 4. Post-Restoration Tasks

1. **Documentation**
   - Record restoration date/time
   - Document any issues encountered
   - Update DNS inventory

2. **Monitoring**
   - Monitor DNS resolution
   - Check application health
   - Watch for any propagation issues

## Rollback Procedure

If restoration fails or causes issues:

1. **Stop Restoration**
```bash
# Note: Lambda will automatically timeout, but you can update records manually
```

2. **Restore Previous Configuration**
   - Use previous backup
   - Or use documented DNS configuration

3. **Document Issues**
   - Record error messages
   - Note any unexpected behavior
   - Update runbooks if needed

## Troubleshooting

### Common Restoration Issues

1. **Permission Errors**
   - Verify IAM roles
   - Check S3 bucket permissions
   - Validate Route 53 access

2. **Invalid Backup Format**
   - Verify JSON structure
   - Check for backup corruption
   - Validate record formats

3. **Timeout Issues**
   - Increase Lambda timeout
   - Break restoration into smaller batches

## Best Practices

1. **Testing**
   - Regularly test restoration process
   - Maintain test domains for practice
   - Document test results

2. **Documentation**
   - Keep detailed restoration logs
   - Document any modifications needed
   - Update procedures based on learnings

3. **Communication**
   - Notify stakeholders before restoration
   - Provide status updates
   - Report completion and issues

## Emergency Contacts

Maintain a list of contacts for emergency support:
- DNS Administrator
- Application Owner
- Cloud Infrastructure Team
- Security Team

## Additional Resources

1. AWS Documentation
2. Internal runbooks
3. Vendor support contacts
4. Monitoring tools documentation

