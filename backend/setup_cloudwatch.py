#!/usr/bin/env python3
"""
CloudWatch設定スクリプト
AWSコンソールで実行するためのスクリプト
"""

import boto3
import json
import time

def create_sns_topic():
    """SNSトピックを作成"""
    sns_client = boto3.client('sns', region_name='ap-northeast-1')
    
    try:
        response = sns_client.create_topic(
            Name='vendor0913-alerts',
            Attributes={
                'DisplayName': 'Vendor0913 Alerts',
                'DeliveryPolicy': json.dumps({
                    "http": {
                        "defaultHealthyRetryPolicy": {
                            "minDelayTarget": 20,
                            "maxDelayTarget": 20,
                            "numRetries": 3,
                            "numMaxDelayRetries": 0,
                            "numMinDelayRetries": 0,
                            "numNoDelayRetries": 0
                        }
                    }
                })
            }
        )
        
        print(f"✅ SNS Topic created: vendor0913-alerts")
        print(f"   ARN: {response['TopicArn']}")
        return response['TopicArn']
        
    except Exception as e:
        print(f"❌ Error creating SNS Topic: {e}")
        return None

def create_cloudwatch_dashboard():
    """CloudWatchダッシュボードを作成"""
    cloudwatch_client = boto3.client('cloudwatch', region_name='ap-northeast-1')
    
    try:
        with open('cloudwatch-dashboard.json', 'r') as f:
            dashboard_config = json.load(f)
        
        response = cloudwatch_client.put_dashboard(
            DashboardName=dashboard_config['DashboardName'],
            DashboardBody=json.dumps(dashboard_config['DashboardBody'])
        )
        
        print(f"✅ CloudWatch Dashboard created: {dashboard_config['DashboardName']}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating CloudWatch Dashboard: {e}")
        return False

def create_cloudwatch_alarms():
    """CloudWatchアラームを作成"""
    cloudwatch_client = boto3.client('cloudwatch', region_name='ap-northeast-1')
    
    try:
        with open('cloudwatch-alarms.json', 'r') as f:
            alarms_config = json.load(f)
        
        for alarm in alarms_config['Alarms']:
            response = cloudwatch_client.put_metric_alarm(
                AlarmName=alarm['AlarmName'],
                ComparisonOperator=alarm['ComparisonOperator'],
                EvaluationPeriods=alarm['EvaluationPeriods'],
                MetricName=alarm['MetricName'],
                Namespace=alarm['Namespace'],
                Period=alarm['Period'],
                Statistic=alarm['Statistic'],
                Threshold=alarm['Threshold'],
                ActionsEnabled=alarm['ActionsEnabled'],
                AlarmActions=alarm['AlarmActions'],
                AlarmDescription=alarm['AlarmDescription'],
                Dimensions=alarm['Dimensions']
            )
            
            print(f"✅ CloudWatch Alarm created: {alarm['AlarmName']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating CloudWatch Alarms: {e}")
        return False

def main():
    """メイン実行関数"""
    print("📊 Setting up CloudWatch monitoring for vendor0913 project...")
    print("=" * 60)
    
    # 1. SNSトピックを作成
    print("\n1. Creating SNS Topic...")
    topic_arn = create_sns_topic()
    
    if not topic_arn:
        print("❌ Failed to create SNS Topic. Exiting.")
        return
    
    # 2. CloudWatchダッシュボードを作成
    print("\n2. Creating CloudWatch Dashboard...")
    if not create_cloudwatch_dashboard():
        print("❌ Failed to create CloudWatch Dashboard. Exiting.")
        return
    
    # 3. CloudWatchアラームを作成
    print("\n3. Creating CloudWatch Alarms...")
    if not create_cloudwatch_alarms():
        print("❌ Failed to create CloudWatch Alarms. Exiting.")
        return
    
    print("\n✅ CloudWatch setup completed!")
    print("\n📝 Next steps:")
    print("   1. Verify CloudWatch dashboard is working correctly")
    print("   2. Test alarm notifications")
    print("   3. Monitor system metrics")

if __name__ == "__main__":
    main()
