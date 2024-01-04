import boto3
import os
from datetime import datetime, timedelta, timezone

sns = boto3.client('sns')
ec2 = boto3.client('ec2')

# 通知先SNSトピックのARNを取得
TOPIC_ARN = os.environ['SNS_TOPIC']
#データ保存日数を取得
DATA_LIFESPAN = int(os.environ['REFERENCE_DATE'])

def lambda_handler(event, context):
    snapshots = get_ebs_snapshots()
    expiration_date = get_expiration_date(data_lifespan)

    filtered_data = filter_old_data(snapshots, expiration_date)

    if filtered_data:
        publish_sns_message(filtered_data, expiration_date)
    else:
        print(f"作成日が{expiration_date}日より前のデータは存在しません")

def get_ebs_snapshots():
    response = ec2.describe_snapshots(OwnerIds=['self'])
    snapshots = response['Snapshots']
    return snapshots

def get_expiration_date(data_lifespan):
    current_date = datetime.now(timezone.utc)
    expiration_date= current_date - timedelta(days=data_lifespan)
    return expiration_date

def filter_old_data(snapshots, expiration_date):
    filtered_data = []
    for snapshot in snapshots:
        if snapshot["StartTime"] < expiration_date:
            filtered_data.append(snapshot)
    return filtered_data

def publish_sns_message(filtered_data, expiration_date):
    message = (f"作成日が{expiration_date}日より前のデータが存在します\n\nEBSスナップショットID")
    Snapshot_id = ""
    for snapshot in filtered_data:
        Snapshot_id += snapshot['SnapshotId'] + "\n"
    content = message + "\n" + Snapshot_id
    sns.publish(
        TopicArn=TOPIC_ARN,
        Message=content
    )

