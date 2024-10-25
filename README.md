# AWS Route 53 DNS Records Backup & Restoration Guide

## Introduction
In today's cloud infrastructure, DNS records are critical components that ensure your applications and services remain accessible. This guide demonstrates how to implement a robust backup and restoration solution for AWS Route 53 DNS records using AWS Lambda, providing disaster recovery capabilities for your DNS infrastructure.

## Why Backup Route 53 Records?
- **Disaster Recovery**: Quickly restore DNS configuration in case of accidental changes or deletion
- **Configuration Tracking**: Maintain historical records of DNS changes
- **Multi-Region Redundancy**: Store DNS configurations safely in different regions
- **Compliance Requirements**: Meet regulatory requirements for infrastructure backup
- **Change Management**: Track and audit DNS changes over time

## Solution Architecture
The solution consists of two Lambda functions:
1. **Backup Function**: Automatically exports all DNS records to S3
2. **Restore Function**: Restores DNS records from S3 backups when needed

### Key Features
- Automated daily backups
- JSON-formatted backup files
- Organized backup structure with timestamps
- Selective restoration capability
- Excludes NS and SOA records during restoration
- Error handling and logging

## Implementation Guide

### Step 1: Create S3 Bucket
1. Create an S3 bucket for storing backups
2. Enable versioning (recommended)
3. Configure appropriate encryption settings

### Step 2: Create IAM Role
Create an IAM role with the following policy:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "route53:ListHostedZones",
                "route53:ListResourceRecordSets",
                "route53:CreateHostedZone",
                "route53:ChangeResourceRecordSets"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject"
            ],
            "Resource": "arn:aws:s3:::/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }
    ]
}
```

### Step 3: Create Backup Lambda Function
1. Create a new Lambda function
2. Set environment variable: `BACKUP_BUCKET`
3. Use the following code:

```python
[import boto3
import json
import os
import datetime
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    """
    Lambda function to backup Route 53 DNS records to an S3 bucket.
    
    Required environment variables:
    - BACKUP_BUCKET: S3 bucket where the backup will be stored.
    """
    try:
        # Initialize AWS clients
        route53 = boto3.client('route53')
        s3 = boto3.client('s3')
        
        # Get environment variable for S3 bucket
        backup_bucket = os.environ['BACKUP_BUCKET']
        
        # Get list of hosted zones
        hosted_zones = route53.list_hosted_zones()['HostedZones']
        
        # Set current date for folder structure
        current_date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for zone in hosted_zones:
            zone_id = zone['Id'].split('/')[-1]
            zone_name = zone['Name'].rstrip('.')
            
            # Retrieve DNS records from the hosted zone
            records = []
            paginator = route53.get_paginator('list_resource_record_sets')
            for page in paginator.paginate(HostedZoneId=zone_id):
                records.extend(page['ResourceRecordSets'])
            
            # Prepare backup data
            backup_data = {
                "zone": {
                    "Id": zone_id,
                    "Name": zone_name
                },
                "records": records
            }
            
            # Define backup file path (folder structure: date/zone_name/backup.json)
            backup_file_key = f"{current_date}/{zone_name}/route53_backup.json"
            
            # Save backup to S3
            s3.put_object(
                Bucket=backup_bucket,
                Key=backup_file_key,
                Body=json.dumps(backup_data, indent=4).encode('utf-8')
            )
            
            print(f"Backup for hosted zone {zone_name} stored at {backup_file_key} in bucket {backup_bucket}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Backup operation completed',
                'backup_bucket': backup_bucket,
                'date': current_date
            })
        }
        
    except Exception as e:
        print(f"Backup failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Backup operation failed',
                'error': str(e)
            })
        }
]
```

### Step 4: Create Restore Lambda Function
1. Create another Lambda function
2. Set environment variable: `BACKUP_BUCKET`
3. Use the following code:

```python
[import boto3
import json
import os
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Restore DNS records from an S3 backup to a Route 53 hosted zone.
    """

    try:
        # Fetch environment variables and event parameters
        backup_bucket = os.environ['BACKUP_BUCKET']
        backup_key = event['backup_key']
        hosted_zone_id = event['hosted_zone_id']
        
        # Initialize AWS clients
        route53 = boto3.client('route53')
        s3 = boto3.client('s3')
        
        # Fetch the backup file from S3
        response = s3.get_object(Bucket=backup_bucket, Key=backup_key)
        backup_data = json.loads(response['Body'].read().decode('utf-8'))
        
        # Extract and filter records (excluding NS and SOA)
        records = backup_data['records']
        filtered_records = [r for r in records if r['Type'] not in ['NS', 'SOA']]
        
        # Restore records in batches of 100
        batch_size = 100
        for i in range(0, len(filtered_records), batch_size):
            batch = filtered_records[i:i + batch_size]
            changes = [{'Action': 'CREATE', 'ResourceRecordSet': record} for record in batch]
            
            route53.change_resource_record_sets(
                HostedZoneId=hosted_zone_id,
                ChangeBatch={'Changes': changes}
            )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Restore operation completed',
                'restored_zone_id': hosted_zone_id
            })
        }
        
    except ClientError as e:
        logger.error(f"Restore failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Restore operation failed',
                'error': str(e)
            })
        }
]
```

### Step 5: Schedule Backup
1. Create an EventBridge rule
2. Set schedule (e.g., `cron(0 0 * * ? *)` for daily backup)
3. Set target as the backup Lambda function

## Restoration Process
To restore DNS records:
1. Identify the backup file path in S3
2. Invoke the restore Lambda function with payload:
```json
{
    "backup_key": "YYYYMMDD_HHMMSS/example.com/route53_backup.json",
    "hosted_zone_id": "/hostedzone/YOUR_ZONE_ID"
}
```

## Best Practices
1. **Regular Testing**: Periodically test the restoration process
2. **Backup Retention**: Implement lifecycle policies for backups
3. **Monitoring**: Set up CloudWatch alarms for backup failures
4. **Version Control**: Use S3 versioning for additional safety
5. **Documentation**: Maintain restoration procedures documentation

## GitHub Repository Structure
```
route53-backup/
├── README.md
├── src/
│   ├── backup_lambda.py
│   └── restore_lambda.py
├── iam/
│   └── lambda_policy.json
├── docs/
│   ├── setup_guide.md
│   └── restoration_guide.md
└── tests/
    └── test_backup_restore.py
```

## Contribution Guidelines
1. Fork the repository
2. Create a feature branch
3. Submit pull request with detailed description
4. Ensure tests pass
5. Follow coding standards

## License
MIT License

## Support
For issues and feature requests, please use the GitHub issues section.

---

Happy DNS Backup! 🚀
