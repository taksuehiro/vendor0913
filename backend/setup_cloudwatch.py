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
                'DisplayName': 'Vendor0913 Alerts'
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
        # シンプルなダッシュボードを作成
        dashboard_body = {
            "widgets": [
                {
                    "type": "metric",
                    "x": 0,
                    "y": 0,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", "vendor0913-alb"],
                            [".", "TargetResponseTime", ".", "."],
                            [".", "HTTPCode_Target_2XX_Count", ".", "."],
                            [".", "HTTPCode_Target_4XX_Count", ".", "."],
                            [".", "HTTPCode_Target_5XX_Count", ".", "."]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": "ap-northeast-1",
                        "title": "ALB Metrics",
                        "period": 300
                    }
                }
            ]
        }
        
        response = cloudwatch_client.put_dashboard(
            DashboardName='vendor0913-dashboard',
            DashboardBody=json.dumps(dashboard_body)
        )
        
        print(f"✅ CloudWatch Dashboard created: vendor0913-dashboard")
        return True
        
    except Exception as e:
        print(f"❌ Error creating CloudWatch Dashboard: {e}")
        return False

def create_cloudwatch_alarms():
    """CloudWatchアラームを作成"""
    cloudwatch_client = boto3.client('cloudwatch', region_name='ap-northeast-1')
    
    try:
        # シンプルなアラームを作成
        alarms = [
            {
                'AlarmName': 'vendor0913-alb-high-error-rate',
                'ComparisonOperator': 'GreaterThanThreshold',
                'EvaluationPeriods': 2,
                'MetricName': 'HTTPCode_Target_5XX_Count',
                'Namespace': 'AWS/ApplicationELB',
                'Period': 300,
                'Statistic': 'Sum',
                'Threshold': 10.0,
                'ActionsEnabled': True,
                'AlarmActions': [],
                'AlarmDescription': 'High error rate on ALB',
                'Dimensions': [
                    {
                        'Name': 'LoadBalancer',
                        'Value': 'vendor0913-alb'
                    }
                ]
            }
        ]
        
        for alarm in alarms:
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
