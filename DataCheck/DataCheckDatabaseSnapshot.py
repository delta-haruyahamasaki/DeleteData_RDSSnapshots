import boto3
import os
from datetime import datetime, timedelta, timezone

sns = boto3.client('sns')
rds = boto3.client('rds')

# 通知先SNSトピックのARNを取得
topic_arn = os.environ['SNS_TOPIC']
#データ保存日数を取得
data_lifespan = int(os.environ['REFERENCE_DATE'])

def lambda_handler(event, context):
    expiration_date = get_expiration_date(data_lifespan)
    duplicate_snapshots = collect_duplicate_snapshots()
    filtered_data = filter_old_data(duplicate_snapshots, expiration_date)

    if duplicate_snapshots and filtered_data:
        notify_snapshot_list_by_email(filtered_data, expiration_date)
    else:
        print(f"{expiration_date}日より前に作成されたデータで、同じDBインスタンスまたはクラスター識別子を持つ重複したスナップショットはありません。")

def collect_duplicate_snapshots():
    snapshots = collect_snapshots()
    snapshot_identifiers = set()
    duplicates = []
    for snapshot in snapshots:
        if snapshot["DBIdentifier"] in snapshot_identifiers:
            duplicates.append(snapshot)
        else:
            snapshot_identifiers.add(snapshot["DBIdentifier"])
    return duplicates

def collect_snapshots():
    cluster_snapshots = get_manual_snapshots_list("cluster")
    instance_snapshots = get_manual_snapshots_list("instance")
    snapshots = merge_snapshots(cluster_snapshots, instance_snapshots)
    return snapshots

def get_manual_snapshots_list(type):
    if type == "cluster":
        cluster_snapshots = rds.describe_db_cluster_snapshots(SnapshotType='manual')['DBClusterSnapshots']
        return cluster_snapshots
    elif type == "instance":
        instance_snapshots = rds.describe_db_snapshots(SnapshotType='manual')['DBSnapshots']
        return instance_snapshots

def merge_snapshots(cluster_snapshots, instance_snapshots):
    for item in cluster_snapshots:
        item["DBIdentifier"] = item.pop("DBClusterIdentifier")
        item["DBSnapshotIdentifier"] = item.pop("DBClusterSnapshotIdentifier")

    for item in instance_snapshots:
        item["DBIdentifier"] = item.pop("DBInstanceIdentifier")
        item["DBSnapshotIdentifier"] = item.pop("DBSnapshotIdentifier")

    snapshots = cluster_snapshots + instance_snapshots
    sorted_snapshots = sorted(snapshots, key=lambda x: x["SnapshotCreateTime"], reverse=True)
    return sorted_snapshots

def get_expiration_date(data_lifespan):
    current_date = datetime.now(timezone.utc)
    expiration_date= current_date - timedelta(days=data_lifespan)
    return expiration_date

def filter_old_data(duplicate_snapshots, expiration_date):
    filtered_data = []
    for snapshot in duplicate_snapshots:
        if snapshot["SnapshotCreateTime"] < expiration_date:
            filtered_data.append(snapshot)
    return filtered_data

def notify_snapshot_list_by_email(filtered_data, expiration_date):
    message = (f"DBインスタンスまたはクラスター識別子が重複したスナップショットあり、かつCreate Timeが{expiration_date}日より前のデータが存在します\n\nスナップショット識別子")
    snapshot_identifier = ""
    for snapshot in filtered_data:
        snapshot_identifier += snapshot['DBSnapshotIdentifier'] + "\n"
    content = message + "\n" + snapshot_identifier
    sns.publish(
        TopicArn=topic_arn,
        Message=content
    )