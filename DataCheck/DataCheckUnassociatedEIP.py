import boto3
import os

sns = boto3.client('sns')
ec2 = boto3.client('ec2')

# 通知先SNSトピックのARNを取得
TOPIC_ARN = os.environ['SNS_TOPIC']

def lambda_handler(event, context):
    unassociated_addresses = filter_unassociated_addresses()

    if unassociated_addresses:
        publish_sns_message(unassociated_addresses)
    else:
        print(f"すべてのEIPが利用されています")

def filter_unassociated_addresses():
    addresses = ec2.describe_addresses()
    filtered_data = []
    for address in addresses['Addresses']:
        if 'InstanceId' not in address:
            filtered_data.append(address)
    return filtered_data

def publish_sns_message(unassociated_addresses):
    message = "関連付けのないEIPが存在します\n\nEIP"
    public_ip = ""
    for address in unassociated_addresses:
        public_ip += address['PublicIp'] + "\n"
    content = message + "\n" + public_ip
    sns.publish(
        TopicArn=TOPIC_ARN,
        Message=content
    )