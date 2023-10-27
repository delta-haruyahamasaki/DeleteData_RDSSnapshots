import boto3
import os

sns = boto3.client('sns')
ec2 = boto3.client('ec2')

def lambda_handler(event, context):

    #利用可能EBSボリュームを取得
    response = ec2.describe_volumes(Filters=[{'Name': 'status', 'Values': ['available']}])
    volumes = response['Volumes']

    #SNSトピックを指定
    topic_arn = os.environ['SNS_TOPIC']

    # 利用可能EBSボリュームがあるかどうかを判定
    if volumes:
        message = (f"利用されていないEBSボリュームが存在します\n\nEBSボリュームID")
        VolumeId = ""
        for volume in volumes:
            VolumeId += volume['VolumeId'] + "\n"
        content = message + "\n" + VolumeId
        response = sns.publish(
            TopicArn=topic_arn,
            Message=content
        )
    else:
        print(f"すべてのEBSボリュームが利用されています")

    return {
        'statusCode': 200,
        'body': '利用されていないEBSボリュームの確認が完了しました。'
    }