#!/usr/bin/env python3
"""
CodeDeploy設定スクリプト
AWSコンソールで実行するためのスクリプト
"""

import boto3
import json
import time

def create_codedeploy_service_role():
    """CodeDeployサービスロールを作成"""
    iam_client = boto3.client('iam', region_name='ap-northeast-1')
    sts_client = boto3.client('sts', region_name='ap-northeast-1')
    
    try:
        # 信頼ポリシー
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "codedeploy.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        # ロールを作成
        response = iam_client.create_role(
            RoleName='CodeDeployServiceRole',
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='CodeDeploy service role for vendor0913 project'
        )
        
        # 必要なポリシーをアタッチ
        policies = [
            'arn:aws:iam::aws:policy/service-role/CodeDeployRole',
            'arn:aws:iam::aws:policy/AmazonECS_FullAccess',
            'arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly'
        ]
        
        for policy_arn in policies:
            iam_client.attach_role_policy(
                RoleName='CodeDeployServiceRole',
                PolicyArn=policy_arn
            )
        
        print(f"✅ CodeDeploy Service Role created: CodeDeployServiceRole")
        account_id = sts_client.get_caller_identity()['Account']
        return f"arn:aws:iam::{account_id}:role/CodeDeployServiceRole"
        
    except iam_client.exceptions.EntityAlreadyExistsException:
        print(f"✅ CodeDeploy Service Role already exists: CodeDeployServiceRole")
        account_id = sts_client.get_caller_identity()['Account']
        return f"arn:aws:iam::{account_id}:role/CodeDeployServiceRole"
    except Exception as e:
        print(f"❌ Error creating CodeDeploy Service Role: {e}")
        return None

def create_codedeploy_application():
    """CodeDeployアプリケーションを作成"""
    codedeploy_client = boto3.client('codedeploy', region_name='ap-northeast-1')
    
    try:
        response = codedeploy_client.create_application(
            applicationName='vendor0913-api-app',
            computePlatform='ECS'
        )
        
        print(f"✅ CodeDeploy Application created: vendor0913-api-app")
        return True
        
    except codedeploy_client.exceptions.ApplicationAlreadyExistsException:
        print(f"✅ CodeDeploy Application already exists: vendor0913-api-app")
        return True
    except Exception as e:
        print(f"❌ Error creating CodeDeploy Application: {e}")
        return False

def create_codedeploy_deployment_group(service_role_arn):
    """CodeDeployデプロイグループを作成"""
    codedeploy_client = boto3.client('codedeploy', region_name='ap-northeast-1')
    
    try:
        response = codedeploy_client.create_deployment_group(
            applicationName='vendor0913-api-app',
            deploymentGroupName='vendor0913-api-group',
            serviceRoleArn=service_role_arn,
            deploymentConfigName='CodeDeployDefault.ECSBlueGreen',
            ecsServices=[
                {
                    'serviceName': 'vendor0913-api-service',
                    'clusterName': 'vendor0913-cluster'
                }
            ],
            loadBalancerInfo={
                'targetGroupInfoList': [
                    {
                        'name': 'vendor0913-api-tg'
                    }
                ]
            },
            blueGreenDeploymentConfiguration={
                'deploymentReadyOption': {
                    'actionOnTimeout': 'CONTINUE_DEPLOYMENT'
                },
                'greenFleetProvisioningOption': {
                    'action': 'COPY_AUTO_SCALING_GROUP'
                },
                'terminateBlueInstancesOnDeploymentSuccess': {
                    'action': 'TERMINATE',
                    'terminationWaitTimeInMinutes': 5
                }
            }
        )
        
        print(f"✅ CodeDeploy Deployment Group created: vendor0913-api-group")
        return True
        
    except Exception as e:
        print(f"❌ Error creating CodeDeploy Deployment Group: {e}")
        return False

def list_codedeploy_resources():
    """CodeDeployリソースを一覧表示"""
    codedeploy_client = boto3.client('codedeploy', region_name='ap-northeast-1')
    
    try:
        # アプリケーション一覧
        apps_response = codedeploy_client.list_applications()
        print("\n📋 CodeDeploy Applications:")
        for app in apps_response['applications']:
            print(f"   - {app}")
        
        # デプロイグループ一覧
        for app in apps_response['applications']:
            try:
                groups_response = codedeploy_client.list_deployment_groups(
                    applicationName=app
                )
                print(f"\n📋 Deployment Groups for {app}:")
                for group in groups_response['deploymentGroups']:
                    print(f"   - {group}")
            except Exception as e:
                print(f"   ❌ Error listing deployment groups for {app}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error listing CodeDeploy resources: {e}")
        return False

def main():
    """メイン実行関数"""
    print("🚀 Setting up CodeDeploy for Blue/Green deployments...")
    print("=" * 60)
    
    # 1. CodeDeployサービスロールを作成
    print("\n1. Creating CodeDeploy Service Role...")
    service_role_arn = create_codedeploy_service_role()
    
    if not service_role_arn:
        print("❌ Failed to create CodeDeploy Service Role. Exiting.")
        return
    
    # 2. CodeDeployアプリケーションを作成
    print("\n2. Creating CodeDeploy Application...")
    if not create_codedeploy_application():
        print("❌ Failed to create CodeDeploy Application. Exiting.")
        return
    
    # 3. CodeDeployデプロイグループを作成
    print("\n3. Creating CodeDeploy Deployment Group...")
    if not create_codedeploy_deployment_group(service_role_arn):
        print("⚠️ Failed to create deployment group, but continuing...")
    
    # 4. リソース一覧表示
    print("\n4. Listing created resources...")
    list_codedeploy_resources()
    
    print("\n✅ CodeDeploy setup completed!")
    print("\n Next steps:")
    print("   1. Test Blue/Green deployment")
    print("   2. Configure deployment hooks")
    print("   3. Set up monitoring and alerts")
    print("   4. Create deployment runbook")

if __name__ == "__main__":
    main()
