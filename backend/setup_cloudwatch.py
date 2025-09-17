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
                            "numNoDelayRetries": 0,
                            "numTargetDelayRetries": 0
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
            DashboardName='vendor0913-monitoring',
            DashboardBody=json.dumps(dashboard_config)
        )
        
        print(f"✅ CloudWatch Dashboard created: vendor0913-monitoring")
        return True
        
    except Exception as e:
        print(f"❌ Error creating CloudWatch Dashboard: {e}")
        return False

def create_cloudwatch_alarms(sns_topic_arn):
    """CloudWatchアラームを作成"""
    cloudwatch_client = boto3.client('cloudwatch', region_name='ap-northeast-1')
    
    try:
        with open('cloudwatch-alarms.json', 'r') as f:
            alarms_config = json.load(f)
        
        created_alarms = 0
        for alarm_config in alarms_config['alarms']:
            try:
                # SNSトピックARNを更新
                if 'AlarmActions' in alarm_config:
                    alarm_config['AlarmActions'] = [sns_topic_arn]
                if 'OKActions' in alarm_config:
                    alarm_config['OKActions'] = [sns_topic_arn]
                if 'InsufficientDataActions' in alarm_config:
                    alarm_config['InsufficientDataActions'] = [sns_topic_arn]
                
                response = cloudwatch_client.put_metric_alarm(
                    AlarmName=alarm_config['AlarmName'],
                    AlarmDescription=alarm_config['AlarmDescription'],
                    MetricName=alarm_config['MetricName'],
                    Namespace=alarm_config['Namespace'],
                    Statistic=alarm_config['Statistic'],
                    Dimensions=alarm_config['Dimensions'],
                    Period=alarm_config['Period'],
                    EvaluationPeriods=alarm_config['EvaluationPeriods'],
                    Threshold=alarm_config['Threshold'],
                    ComparisonOperator=alarm_config['ComparisonOperator'],
                    AlarmActions=alarm_config.get('AlarmActions', []),
                    OKActions=alarm_config.get('OKActions', []),
                    InsufficientDataActions=alarm_config.get('InsufficientDataActions', [])
                )
                
                print(f"✅ Alarm created: {alarm_config['AlarmName']}")
                created_alarms += 1
                
            except Exception as e:
                print(f"❌ Error creating alarm {alarm_config['AlarmName']}: {e}")
                continue
        
        print(f"✅ Created {created_alarms} alarms")
        return True
        
    except Exception as e:
        print(f"❌ Error creating CloudWatch Alarms: {e}")
        return False

def create_log_group():
    """CloudWatch Log Groupを作成"""
    logs_client = boto3.client('logs', region_name='ap-northeast-1')
    
    try:
        response = logs_client.create_log_group(
            logGroupName='/ecs/vendor0913/api',
            tags={
                'Project': 'tak-vendor2-0912',
                'Owner': 'takuya_suehiro',
                'Environment': 'production'
            }
        )
        
        print(f"✅ Log Group created: /ecs/vendor0913/api")
        
        # ログ保持期間を設定
        logs_client.put_retention_policy(
            logGroupName='/ecs/vendor0913/api',
            retentionInDays=30
        )
        
        print(f"✅ Log retention policy set: 30 days")
        return True
        
    except logs_client.exceptions.ResourceAlreadyExistsException:
        print(f"ℹ️ Log Group already exists: /ecs/vendor0913/api")
        return True
    except Exception as e:
        print(f"❌ Error creating Log Group: {e}")
        return False

def create_custom_metrics():
    """カスタムメトリクスを作成"""
    cloudwatch_client = boto3.client('cloudwatch', region_name='ap-northeast-1')
    
    try:
        # エラーカウントメトリクス
        response = cloudwatch_client.put_metric_data(
            Namespace='vendor0913/application',
            MetricData=[
                {
                    'MetricName': 'ErrorCount',
                    'Dimensions': [
                        {
                            'Name': 'LogGroup',
                            'Value': '/ecs/vendor0913/api'
                        }
                    ],
                    'Value': 0,
                    'Unit': 'Count',
                    'Timestamp': time.time()
                }
            ]
        )
        
        print(f"✅ Custom metrics created: vendor0913/application")
        return True
        
    except Exception as e:
        print(f"❌ Error creating custom metrics: {e}")
        return False

def list_cloudwatch_resources():
    """CloudWatchリソースを一覧表示"""
    cloudwatch_client = boto3.client('cloudwatch', region_name='ap-northeast-1')
    logs_client = boto3.client('logs', region_name='ap-northeast-1')
    
    try:
        # ダッシュボード
        dashboards = cloudwatch_client.list_dashboards()
        print("\n📋 CloudWatch Dashboards:")
        for dashboard in dashboards['DashboardEntries']:
            if 'vendor0913' in dashboard['DashboardName']:
                print(f"   - {dashboard['DashboardName']}")
                print(f"     Created: {dashboard['LastModified']}")
                print()
        
        # アラーム
        alarms = cloudwatch_client.describe_alarms()
        print("📋 CloudWatch Alarms:")
        for alarm in alarms['MetricAlarms']:
            if 'vendor0913' in alarm['AlarmName']:
                print(f"   - {alarm['AlarmName']}")
                print(f"     State: {alarm['StateValue']}")
                print(f"     Created: {alarm['AlarmConfigurationUpdatedTimestamp']}")
                print()
        
        # ロググループ
        log_groups = logs_client.describe_log_groups()
        print("📋 CloudWatch Log Groups:")
        for log_group in log_groups['logGroups']:
            if 'vendor0913' in log_group['logGroupName']:
                print(f"   - {log_group['logGroupName']}")
                print(f"     Retention: {log_group.get('retentionInDays', 'Never')} days")
                print(f"     Created: {log_group['creationTime']}")
                print()
                
    except Exception as e:
        print(f"❌ Error listing CloudWatch resources: {e}")

def main():
    """メイン実行関数"""
    print("📊 Setting up CloudWatch monitoring for vendor0913 project...")
    print("=" * 60)
    
    # 1. SNSトピックを作成
    print("\n1. Creating SNS Topic...")
    sns_topic_arn = create_sns_topic()
    
    if not sns_topic_arn:
        print("❌ Failed to create SNS Topic. Exiting.")
        return
    
    # 2. CloudWatchダッシュボードを作成
    print("\n2. Creating CloudWatch Dashboard...")
    if not create_cloudwatch_dashboard():
        print("⚠️ Failed to create dashboard, but continuing...")
    
    # 3. CloudWatchアラームを作成
    print("\n3. Creating CloudWatch Alarms...")
    if not create_cloudwatch_alarms(sns_topic_arn):
        print("⚠️ Failed to create some alarms, but continuing...")
    
    # 4. ロググループを作成
    print("\n4. Creating Log Group...")
    if not create_log_group():
        print("⚠️ Failed to create log group, but continuing...")
    
    # 5. カスタムメトリクスを作成
    print("\n5. Creating Custom Metrics...")
    if not create_custom_metrics():
        print("⚠️ Failed to create custom metrics, but continuing...")
    
    # 6. 作成されたリソースを一覧表示
    print("\n6. Listing created resources...")
    list_cloudwatch_resources()
    
    print("\n✅ CloudWatch monitoring setup completed!")
    print("\n📝 Next steps:")
    print("   1. Subscribe to SNS topic for alerts")
    print("   2. Verify dashboard is working correctly")
    print("   3. Test alarm conditions")
    print("   4. Monitor application performance")

if __name__ == "__main__":
    main()
