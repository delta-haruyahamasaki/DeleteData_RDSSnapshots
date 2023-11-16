import boto3
import os

sns = boto3.client('sns')
ec2 = boto3.client('ec2')

# 通知先SNSトピックのARNを取得
topic_arn = os.environ['SNS_TOPIC']

def lambda_handler(event, context):

    volumes = collect_ebs_volume_status_available()

    if volumes:
        notify_volume_list_by_email(volumes)
    else:
        print("すべてのEBSボリュームが利用されています")

def collect_ebs_volume_status_available():
    response = ec2.describe_volumes(Filters=[{'Name': 'status', 'Values': ['available']}])
    volumes = response['Volumes']
    return volumes

def notify_volume_list_by_email(volumes):
    message = "利用されていないEBSボリュームが存在します\n\nEBSボリュームID"
    volume_id = ""
    for volume in volumes:
        volume_id += volume['VolumeId'] + "\n"
    content = message + "\n" + volume_id
    sns.publish(
        TopicArn=topic_arn,
        Message=content
    )

