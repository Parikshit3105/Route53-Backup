import boto3
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
