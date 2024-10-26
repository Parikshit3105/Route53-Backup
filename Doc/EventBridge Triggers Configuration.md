# Route53 DNS Records Backup Event Bridge Triggure

This solution automatically backs up Amazon Route53 DNS records to an S3 bucket using two EventBridge triggers: a monthly schedule and on DNS record changes.

## EventBridge Triggers Configuration

### 1. Monthly Schedule Trigger

This trigger runs the backup on the 26th of every month at 11:00 PM IST (17:30 UTC).

```json
{
    "name": "route53-monthly-backup",
    "description": "Triggers Route53 backup Lambda function monthly on 26th at 11:00 PM IST",
    "scheduleExpression": "cron(30 17 26 * ? *)"
}
```

Setup Steps:
1. Go to Amazon EventBridge → Create rule
2. Choose "Schedule"
3. Enter the cron expression: `cron(30 17 26 * ? *`
4. Select the Lambda function as target
5. Create the rule

### 2. DNS Changes Trigger

This trigger runs the backup whenever Route53 DNS records are modified.

```json
{
    "source": ["aws.route53"],
    "detail-type": ["AWS API Call via CloudTrail"],
    "detail": {
        "eventSource": ["route53.amazonaws.com"],
        "eventName": [
            "ChangeResourceRecordSets",
            "CreateResourceRecordSet",
            "DeleteResourceRecordSet",
            "UpsertResourceRecordSet"
        ]
    }
}
```

Setup Steps:
1. Ensure CloudTrail is enabled for Route53 API calls
2. Go to Amazon EventBridge → Create rule
3. Choose "Rule with an event pattern"
4. Paste the event pattern above
5. Select the Lambda function as target
6. Create the rule

## Prerequisites

1. CloudTrail enabled to track Route53 API calls
2. Lambda function with appropriate permissions
3. EventBridge IAM role with permissions to invoke Lambda

## Required IAM Permissions

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": "arn:aws:lambda:REGION:ACCOUNT_ID:function:lm-masterproduction-route53-records-backup"
        }
    ]
}
```

## Troubleshooting

Common issues:
1. EventBridge rule not triggering:
   - Verify CloudTrail is enabled
   - Check IAM permissions
   - Verify event pattern syntax

2. Lambda not executing:
   - Check Lambda execution role permissions
   - Review CloudWatch Logs for errors
   - Verify EventBridge has permission to invoke Lambda
