#!/usr/bin/env python3
"""
コスト予算設定スクリプト
AWS Budgets と Cost Explorer の設定
"""

import boto3
import json
import time
from datetime import datetime, timedelta

def create_monthly_budget():
    """月次予算を作成"""
    budgets_client = boto3.client('budgets', region_name='us-east-1')
    
    try:
        budget = {
            'BudgetName': 'vendor0913-monthly-budget',
            'BudgetLimit': {
                'Amount': '100.00',
                'Unit': 'USD'
            },
            'TimeUnit': 'MONTHLY',
            'BudgetType': 'COST',
            'CostFilters': {
                'Tag': {
                    'Project': ['tak-vendor2-0912']
                }
            },
            'TimePeriod': {
                'Start': datetime.now().strftime('%Y-%m-01'),
                'End': (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
            }
        }
        
        response = budgets_client.create_budget(
            AccountId='067717894185',
            Budget=budget
        )
        
        print(f"✅ Monthly budget created: {budget['BudgetName']}")
        print(f"   Amount: ${budget['BudgetLimit']['Amount']}")
        print(f"   Time Unit: {budget['TimeUnit']}")
        return True
        
    except budgets_client.exceptions.DuplicateRecordException:
        print(f"ℹ️ Monthly budget already exists: vendor0913-monthly-budget")
        return True
    except Exception as e:
        print(f"❌ Error creating monthly budget: {e}")
        return False

def create_budget_alerts():
    """予算アラートを作成"""
    budgets_client = boto3.client('budgets', region_name='us-east-1')
    
    try:
        # 80%アラート
        response = budgets_client.create_budget_action(
            AccountId='067717894185',
            BudgetName='vendor0913-monthly-budget',
            ActionThreshold={
                'ActionThresholdValue': 80.0,
                'ActionThresholdType': 'PERCENTAGE'
            },
            ActionType='APPLY_IAM_POLICY',
            ActionDefinition={
                'IamActionDefinition': {
                    'PolicyArn': 'arn:aws:iam::aws:policy/AWSBillingReadOnlyAccess'
                }
            }
        )
        
        print(f"✅ Budget alert created: 80% threshold")
        
        # 100%アラート
        response = budgets_client.create_budget_action(
            AccountId='067717894185',
            BudgetName='vendor0913-monthly-budget',
            ActionThreshold={
                'ActionThresholdValue': 100.0,
                'ActionThresholdType': 'PERCENTAGE'
            },
            ActionType='APPLY_IAM_POLICY',
            ActionDefinition={
                'IamActionDefinition': {
                    'PolicyArn': 'arn:aws:iam::aws:policy/AWSBillingReadOnlyAccess'
                }
            }
        )
        
        print(f"✅ Budget alert created: 100% threshold")
        return True
        
    except Exception as e:
        print(f"❌ Error creating budget alerts: {e}")
        return False

def create_cost_anomaly_detection():
    """コスト異常検知を設定"""
    ce_client = boto3.client('ce', region_name='us-east-1')
    
    try:
        # コスト異常検知の設定
        response = ce_client.create_anomaly_detector(
            AnomalyDetectorName='vendor0913-cost-anomaly-detector',
            AnomalyDetectorType='DIMENSIONAL',
            Specification={
                'Dimension': 'SERVICE',
                'MatchOptions': ['EQUALS'],
                'Values': ['Amazon Elastic Compute Cloud', 'Amazon Relational Database Service', 'Amazon Simple Storage Service']
            }
        )
        
        print(f"✅ Cost anomaly detector created: {response['AnomalyDetectorArn']}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating cost anomaly detector: {e}")
        return False

def get_current_costs():
    """現在のコストを取得"""
    ce_client = boto3.client('ce', region_name='us-east-1')
    
    try:
        # 今月のコストを取得
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Granularity='MONTHLY',
            Metrics=['BlendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )
        
        print(f"\n📊 Current Month Costs ({start_date} to {end_date}):")
        total_cost = 0
        
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['BlendedCost']['Amount'])
                total_cost += cost
                if cost > 0:
                    print(f"   {service}: ${cost:.2f}")
        
        print(f"   Total: ${total_cost:.2f}")
        return total_cost
        
    except Exception as e:
        print(f"❌ Error getting current costs: {e}")
        return None

def create_cost_reports():
    """コストレポートを作成"""
    ce_client = boto3.client('ce', region_name='us-east-1')
    
    try:
        # 日次コストレポート
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Granularity='DAILY',
            Metrics=['BlendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )
        
        print(f"\n📈 Daily Cost Trend (Last 30 days):")
        daily_costs = {}
        
        for result in response['ResultsByTime']:
            date = result['TimePeriod']['Start']
            total_daily = 0
            
            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['BlendedCost']['Amount'])
                total_daily += cost
                
                if service not in daily_costs:
                    daily_costs[service] = []
                daily_costs[service].append(cost)
            
            print(f"   {date}: ${total_daily:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating cost reports: {e}")
        return False

def setup_cost_optimization():
    """コスト最適化の設定"""
    print("\n🔧 Setting up cost optimization...")
    
    try:
        # 未使用のEBSボリュームを検索
        ec2_client = boto3.client('ec2', region_name='ap-northeast-1')
        
        response = ec2_client.describe_volumes(
            Filters=[
                {
                    'Name': 'status',
                    'Values': ['available']
                },
                {
                    'Name': 'tag:Project',
                    'Values': ['tak-vendor2-0912']
                }
            ]
        )
        
        unused_volumes = response['Volumes']
        if unused_volumes:
            print(f"⚠️ Found {len(unused_volumes)} unused EBS volumes:")
            for volume in unused_volumes:
                print(f"   Volume ID: {volume['VolumeId']}, Size: {volume['Size']}GB")
        else:
            print("✅ No unused EBS volumes found")
        
        # 古いAMIを検索
        response = ec2_client.describe_images(
            Owners=['self'],
            Filters=[
                {
                    'Name': 'tag:Project',
                    'Values': ['tak-vendor2-0912']
                }
            ]
        )
        
        old_amis = response['Images']
        if old_amis:
            print(f"ℹ️ Found {len(old_amis)} custom AMIs:")
            for ami in old_amis:
                print(f"   AMI ID: {ami['ImageId']}, Created: {ami['CreationDate']}")
        else:
            print("✅ No custom AMIs found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up cost optimization: {e}")
        return False

def list_budget_resources():
    """予算関連リソースを一覧表示"""
    budgets_client = boto3.client('budgets', region_name='us-east-1')
    
    try:
        # 予算一覧
        response = budgets_client.describe_budgets(AccountId='067717894185')
        print("\n📋 AWS Budgets:")
        for budget in response['Budgets']:
            if 'vendor0913' in budget['BudgetName']:
                print(f"   - {budget['BudgetName']}")
                print(f"     Amount: ${budget['BudgetLimit']['Amount']}")
                print(f"     Time Unit: {budget['TimeUnit']}")
                print()
        
        # 予算アクション一覧
        response = budgets_client.describe_budget_actions_for_budget(
            AccountId='067717894185',
            BudgetName='vendor0913-monthly-budget'
        )
        print("📋 Budget Actions:")
        for action in response['Actions']:
            print(f"   - {action['ActionName']}")
            print(f"     Threshold: {action['ActionThreshold']['ActionThresholdValue']}%")
            print(f"     Type: {action['ActionType']}")
            print()
        
    except Exception as e:
        print(f"❌ Error listing budget resources: {e}")

def main():
    """メイン実行関数"""
    print("💰 Setting up cost management for vendor0913...")
    print("=" * 60)
    
    # 1. 現在のコストを確認
    print("\n1. Checking current costs...")
    current_cost = get_current_costs()
    
    # 2. 月次予算を作成
    print("\n2. Creating monthly budget...")
    if not create_monthly_budget():
        print("⚠️ Failed to create monthly budget, but continuing...")
    
    # 3. 予算アラートを作成
    print("\n3. Creating budget alerts...")
    if not create_budget_alerts():
        print("⚠️ Failed to create budget alerts, but continuing...")
    
    # 4. コスト異常検知を設定
    print("\n4. Setting up cost anomaly detection...")
    if not create_cost_anomaly_detection():
        print("⚠️ Failed to create cost anomaly detection, but continuing...")
    
    # 5. コストレポートを作成
    print("\n5. Creating cost reports...")
    if not create_cost_reports():
        print("⚠️ Failed to create cost reports, but continuing...")
    
    # 6. コスト最適化を設定
    print("\n6. Setting up cost optimization...")
    if not setup_cost_optimization():
        print("⚠️ Failed to setup cost optimization, but continuing...")
    
    # 7. 予算関連リソースを一覧表示
    print("\n7. Listing budget resources...")
    list_budget_resources()
    
    print("\n✅ Cost management setup completed!")
    print("\n📝 Next steps:")
    print("   1. Monitor budget alerts")
    print("   2. Review cost reports regularly")
    print("   3. Optimize resource usage")
    print("   4. Set up additional cost controls as needed")

if __name__ == "__main__":
    main()
