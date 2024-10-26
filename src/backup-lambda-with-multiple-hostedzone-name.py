import boto3
import json
import os
import datetime
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    """
    Lambda function to backup Route 53 DNS records to an S3 bucket.
    Handles multiple hosted zones with the same name by incorporating zone IDs in the backup path.
    
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
        current_date = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        
        # Dictionary to keep track of zones with same name
        zone_name_count = {}
        
        for zone in hosted_zones:
            zone_id = zone['Id'].split('/')[-1]
            zone_name = zone['Name'].rstrip('.')
            
            # Keep track of zones with same name
            if zone_name in zone_name_count:
                zone_name_count[zone_name] += 1
            else:
                zone_name_count[zone_name] = 1
            
            # Retrieve DNS records from the hosted zone
            records = []
            paginator = route53.get_paginator('list_resource_record_sets')
            for page in paginator.paginate(HostedZoneId=zone_id):
                records.extend(page['ResourceRecordSets'])
            
            # Prepare backup data with additional zone information
            backup_data = {
                "zone": {
                    "Id": zone_id,
                    "Name": zone_name,
                    "RecordCount": len(records)
                },
                "records": records
            }
            
            # Define backup file path including zone ID
            # Format: date/zone_name/zone_id/route53_backup.json
            backup_file_key = f"{current_date}/{zone_name}/{zone_id}/route53_backup.json"
            
            # Save detailed backup to S3
            s3.put_object(
                Bucket=backup_bucket,
                Key=backup_file_key,
                Body=json.dumps(backup_data, indent=4).encode('utf-8')
            )
            
            # If there are multiple zones with the same name, create a summary file
            if zone_name_count[zone_name] > 1:
                summary_data = {
                    "zone_name": zone_name,
                    "zone_id": zone_id,
                    "record_count": len(records),
                    "backup_path": backup_file_key
                }
                
                summary_file_key = f"{current_date}/{zone_name}/zone_summary.json"
                
                # Append to or create summary file
                try:
                    # Try to get existing summary file
                    existing_summary = s3.get_object(
                        Bucket=backup_bucket,
                        Key=summary_file_key
                    )
                    summary_content = json.loads(existing_summary['Body'].read().decode('utf-8'))
                    if isinstance(summary_content, list):
                        summary_content.append(summary_data)
                    else:
                        summary_content = [summary_content, summary_data]
                except ClientError as e:
                    if e.response['Error']['Code'] == 'NoSuchKey':
                        summary_content = [summary_data]
                    else:
                        raise
                
                # Save or update summary file
                s3.put_object(
                    Bucket=backup_bucket,
                    Key=summary_file_key,
                    Body=json.dumps(summary_content, indent=4).encode('utf-8')
                )
            
            print(f"Backup for hosted zone {zone_name} (ID: {zone_id}) stored at {backup_file_key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Backup operation completed',
                'backup_bucket': backup_bucket,
                'date': current_date,
                'zones_backed_up': [
                    f"{zone['Name'].rstrip('.')} (ID: {zone['Id'].split('/')[-1]})"
                    for zone in hosted_zones
                ]
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
