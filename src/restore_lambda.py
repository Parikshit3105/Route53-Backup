import boto3
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
