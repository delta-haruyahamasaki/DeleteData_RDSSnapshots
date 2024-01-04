import boto3
import os

sns = boto3.client('sns')
ec2 = boto3.client('ec2')

# 通知先SNSトピックのARNを取得
TOPIC_ARN = os.environ['SNS_TOPIC']

def lambda_handler(event, context):

    volumes = collect_ebs_volume_status_available()

    if volumes:
        publish_sns_message(volumes)
    else:
        print("すべてのEBSボリュームが利用されています")

def collect_ebs_volume_status_available():
    response = ec2.describe_volumes(Filters=[{'Name': 'status', 'Values': ['available']}])
    volumes = response['Volumes']
    return volumes

def publish_sns_message(volumes):
    message = "利用されていないEBSボリュームが存在します\n\nEBSボリュームID"
    volume_id = ""
    for volume in volumes:
        volume_id += volume['VolumeId'] + "\n"
    content = message + "\n" + volume_id
    sns.publish(
        TopicArn=TOPIC_ARN,
        Message=content
    )
