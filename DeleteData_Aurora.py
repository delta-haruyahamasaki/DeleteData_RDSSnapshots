import boto3
import os
from datetime import datetime, timedelta, timezone

sns = boto3.client('sns')
rds = boto3.client('rds')

def lambda_handler(event, context):

    #DBCluster手動スナップショット一覧を取得
    response = rds.describe_db_cluster_snapshots(
        SnapshotType='manual'
    )
    snapshots = response['DBClusterSnapshots']

    #スナップショット作成日降順に並べ替え(最新スナップショット以前の重複をリストアップするため)
    sorted_snapshots = sorted(snapshots, key=lambda x: x["SnapshotCreateTime"], reverse=True)

    # 重複するDBクラスタースナップショットの有無を確認
    cluster_identifiers = set()
    duplicates = []
    for item in sorted_snapshots:
        if item["DBClusterIdentifier"] in cluster_identifiers:
            duplicates.append(item)
        else:
            cluster_identifiers.add(item["DBClusterIdentifier"])

    # 現在の日付を取得
    current_date = datetime.now(timezone.utc)

    #指定された日数を取得
    Reference_date = int(os.environ['ReferenceDate'])

    # 半年前の日付を計算
    Reference_date_ago= current_date - timedelta(days=Reference_date)

    # Create Timeが半年より前のデータをフィルタリング
    filtered_data = [item for item in duplicates if item["SnapshotCreateTime"] < Reference_date_ago]

    #SNSトピックを指定
    topic_arn = os.environ['SNSTopicArn']

    # 重複があり、かつCreate Timeが半年より前のデータがあるかどうかを判定
    if duplicates and filtered_data:
        message = (f"重複したクラスター識別子があり、かつCreate Timeが{Reference_date}日より前のデータが存在します\n\nスナップショット識別子")
        filtered_Snapshots = ""
        for snapshot in filtered_data:
            filtered_Snapshots += snapshot['DBClusterSnapshotIdentifier'] + "\n"
        mail_content = message + "\n" + filtered_Snapshots
        response = sns.publish(
            TopicArn=topic_arn,
            Message=mail_content
        )
    else:
        print(f"重複したクラスター識別子があり、かつCreate Timeが{Reference_date}日より前のデータが存在しません")

    return {
        'statusCode': 200,
        'body': 'AuroraSnapshotCheckeが完了しました'
    }