import boto3
import os

sns = boto3.client('sns')
ec2 = boto3.client('ec2')

def lambda_handler(event, context):

    # Elastic IPの一覧を取得する
    response = ec2.describe_addresses()

    # 関連付けのないEIPをフィルタリングする
    unassociated_addresses = [address for address in response['Addresses'] if 'InstanceId' not in address]

    #SNSトピックを指定
    topic_arn = os.environ['SNS_TOPIC']

    # 関連付けのないEIPの有無を判定
    if unassociated_addresses:
        message = (f"関連付けのないEIPが存在します\n\nEIP")
        PublicIp = ""
        for address in unassociated_addresses:
            PublicIp += address['PublicIp'] + "\n"
        content = message + "\n" + PublicIp
        response = sns.publish(
            TopicArn=topic_arn,
            Message=content
        )
    else:
        print(f"すべてのEIPが利用されています")

    return {
        'statusCode': 200,
        'body': '関連付けのないEIPの確認が完了しました。'
    }