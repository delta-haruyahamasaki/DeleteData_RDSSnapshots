import boto3
import os
from datetime import datetime, timedelta, timezone

sns = boto3.client('sns')
ec2 = boto3.client('ec2')

def lambda_handler(event, context):

    #利用可能ボリュームを取得
    response = ec2.describe_volumes(Filters=[{'Name': 'status', 'Values': ['available']}])
    volumes = response['Volumes']

    #SNSトピックを指定
    topic_arn = os.environ['SNS_TOPIC']

    # 利用可能ボリュームがあるかどうかを判定
    if volumes:
        message = (f"利用されていないEBSが存在します\n\nスナップショット識別子")
        VolumeId = ""
        for volume in volumes:
            VolumeId += volume['VolumeId'] + "\n"
        content = message + "\n" + VolumeId
        response = sns.publish(
            TopicArn=topic_arn,
            Message=content
        )
    else:
        print(f"すべてのEBSが利用されています")

    return {
        'statusCode': 200,
        'body': 'メッセージが発行されました。'
    }





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

    