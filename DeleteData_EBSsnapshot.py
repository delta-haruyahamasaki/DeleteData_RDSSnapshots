import boto3
import os
from datetime import datetime, timedelta, timezone

sns = boto3.client('sns')
rds = boto3.client('rds')

def lambda_handler(event, context):

    #DBCluster手動スナップショット一覧を取得
    cluster_response = rds.describe_db_cluster_snapshots(
        SnapshotType='manual'
    )
    
    #DBInstance手動スナップショット一覧を取得
    instance_response = rds.describe_db_snapshots(
        SnapshotType='manual'
    )
    
    cluster_snapshots = cluster_response['DBClusterSnapshots']
    instance_snapshots = instance_response['DBSnapshots']
    
    # cluster/instanceスナップショット一覧 key名統一
    for item in cluster_snapshots:
        item["DBIdentifier"] = item.pop("DBClusterIdentifier")
        item["DBSnapshotIdentifier"] = item.pop("DBClusterSnapshotIdentifier")

    for item in instance_snapshots:
        item["DBIdentifier"] = item.pop("DBInstanceIdentifier")
        item["DBSnapshotIdentifier"] = item.pop("DBSnapshotIdentifier")
    
    #cluster/instanceスナップショット 結合
    snapshots = cluster_snapshots + instance_snapshots
    
    #スナップショット作成日降順に並べ替え(最新スナップショット以前の重複をリストアップするため)
    sorted_snapshots = sorted(snapshots, key=lambda x: x["SnapshotCreateTime"], reverse=True)

    # 重複するDBクラスタースナップショットの有無を確認
    cluster_identifiers = set()
    duplicates = []
    for item in sorted_snapshots:
        if item["DBIdentifier"] in cluster_identifiers:
            duplicates.append(item)
        else:
            cluster_identifiers.add(item["DBIdentifier"])

    # 現在の日付を取得
    current_date = datetime.now(timezone.utc)

    #指定された日数を取得
    Reference_date = int(os.environ['REFERENCE_DATE'])

    # 半年前の日付を計算
    Reference_date_ago= current_date - timedelta(days=Reference_date)

    # Create Timeが半年より前のデータをフィルタリング
    filtered_data = [item for item in duplicates if item["SnapshotCreateTime"] < Reference_date_ago]

    #SNSトピックを指定
    topic_arn = os.environ['SNS_TOPIC']

    # 重複があり、かつCreate Timeが半年より前のデータがあるかどうかを判定
    if duplicates and filtered_data:
        message = (f"重複したDBインスタンスまたはクラスター識別子があり、かつCreate Timeが{Reference_date}日より前のデータが存在します\n\nスナップショット識別子")
        SnapshotIdentifier = ""
        for snapshot in filtered_data:
            SnapshotIdentifier += snapshot['DBSnapshotIdentifier'] + "\n"
        content = message + "\n" + SnapshotIdentifier
        response = sns.publish(
            TopicArn=topic_arn,
            Message=content
        )
    else:
        print(f"重複したDBインスタンスまたはクラスター識別子があり、かつCreate Timeが{Reference_date}日より前のデータが存在しません")

    return {
        'statusCode': 200,
        'body': 'メッセージが発行されました。'
    }