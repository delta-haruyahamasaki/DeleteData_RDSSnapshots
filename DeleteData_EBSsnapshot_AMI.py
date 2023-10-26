import boto3
import os
from datetime import datetime, timedelta, timezone

sns = boto3.client('sns')
ec2 = boto3.client('ec2')

def lambda_handler(event, context):

    #DBCluster手動スナップショット一覧を取得
    response = ec2.describe_snapshots(OwnerIds=['self'])
    snapshots = response['Snapshots']

    # 現在の日付を取得
    current_date = datetime.now(timezone.utc)

    #指定された日数を取得
    Reference_date = int(os.environ['REFERENCE_DATE'])

    # 指定された日数から日付を計算
    Reference_date_ago= current_date - timedelta(days=Reference_date)

    # Create Timeが指定された日数より前のデータをフィルタリング
    filtered_data = [item for item in snapshots if item["StartTime"] < Reference_date_ago]

    print(filtered_data)

    #SNSトピックを指定
    topic_arn = os.environ['SNS_TOPIC']

    # Create Timeが指定日より前のデータがあるかどうかを判定
    if filtered_data:
        message = (f"Create Timeが{Reference_date}日より前のデータが存在します\n\nスナップショット識別子")
        SnapshotId = ""
        for snapshot in filtered_data:
            SnapshotId += snapshot['SnapshotId'] + "\n"
        content = message + "\n" + SnapshotId
        response = sns.publish(
            TopicArn=topic_arn,
            Message=content
        )
    else:
        print(f"Create Timeが{Reference_date}日より前のデータが存在しません")

    return {
        'statusCode': 200,
        'body': 'メッセージが発行されました。'
    }