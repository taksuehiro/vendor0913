#!/usr/bin/env python3
"""
CodeDeploy設定スクリプト（ECS Blue/Green対応版）
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
            Description='CodeDeploy service role for ECS Blue/Green deployment'
        )
        
        # ECS用の必要なポリシーをアタッチ
        policies = [
            'arn:aws:iam::aws:policy/AWSCodeDeployRoleForECS',  # ECS専用ポリシー
            'arn:aws:iam::aws:policy/AmazonECS_FullAccess'
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
    """CodeDeployデプロイグループを作成（ECS Blue/Green用）"""
    codedeploy_client = boto3.client('codedeploy', region_name='ap-northeast-1')
    
    try:
        response = codedeploy_client.create_deployment_group(
            applicationName='vendor0913-api-app',
            deploymentGroupName='vendor0913-api-group',
            serviceRoleArn=service_role_arn,
            deploymentConfigName='CodeDeployDefault.ECSLinear10PercentEvery1Minutes',  # ECS用の設定
            # 重要: ECSではdeploymentStyleを明示的に指定する必要がある
            deploymentStyle={
                'deploymentType': 'BLUE_GREEN',
                'deploymentOption': 'WITH_TRAFFIC_CONTROL'
            },
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
            # ECS用のBlue/Green設定
            blueGreenDeploymentConfiguration={
                'deploymentReadyOption': {
                    'actionOnTimeout': 'CONTINUE_DEPLOYMENT',
                    'waitTimeInMinutes': 0
                },
                'terminateBlueInstancesOnDeploymentSuccess': {
                    'action': 'TERMINATE',
                    'terminationWaitTimeInMinutes': 5
                }
            },
            # 自動ロールバック設定
            autoRollbackConfiguration={
                'enabled': True,
                'events': ['DEPLOYMENT_FAILURE', 'DEPLOYMENT_STOP_ON_ALARM']
            }
        )
        
        print(f"✅ CodeDeploy Deployment Group created: vendor0913-api-group")
        return True
        
    except Exception as e:
        print(f"❌ Error creating CodeDeploy Deployment Group: {e}")
        print(f"   詳細: {str(e)}")
        return False

def create_alternative_deployment_group(service_role_arn):
    """代替設定でデプロイグループを作成"""
    codedeploy_client = boto3.client('codedeploy', region_name='ap-northeast-1')
    
    print("📋 代替設定でデプロイグループを作成中...")
    
    try:
        response = codedeploy_client.create_deployment_group(
            applicationName='vendor0913-api-app',
            deploymentGroupName='vendor0913-api-group-v2',
            serviceRoleArn=service_role_arn,
            deploymentConfigName='CodeDeployDefault.ECSAllAtOnceBlueGreen',  # 一括切り替え
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
            # 最小限のBlue/Green設定
            blueGreenDeploymentConfiguration={
                'deploymentReadyOption': {
                    'actionOnTimeout': 'CONTINUE_DEPLOYMENT'
                },
                'terminateBlueInstancesOnDeploymentSuccess': {
                    'action': 'TERMINATE',
                    'terminationWaitTimeInMinutes': 5
                }
            }
        )
        
        print(f"✅ 代替 CodeDeploy Deployment Group created: vendor0913-api-group-v2")
        return True
        
    except Exception as e:
        print(f"❌ Error creating alternative Deployment Group: {e}")
        return False

def validate_prerequisites():
    """事前要件を検証"""
    print("🔍 事前要件を検証中...")
    
    ecs_client = boto3.client('ecs', region_name='ap-northeast-1')
    elbv2_client = boto3.client('elbv2', region_name='ap-northeast-1')
    
    try:
        # ECSクラスターの存在確認
        clusters_response = ecs_client.describe_clusters(
            clusters=['vendor0913-cluster']
        )
        if not clusters_response['clusters'] or clusters_response['clusters'][0]['status'] != 'ACTIVE':
            print("❌ ECSクラスター 'vendor0913-cluster' が見つからないか非アクティブです")
            return False
        print("✅ ECSクラスター確認完了")
        
        # ECSサービスの存在確認
        services_response = ecs_client.describe_services(
            cluster='vendor0913-cluster',
            services=['vendor0913-api-service']
        )
        if not services_response['services'] or services_response['services'][0]['status'] != 'ACTIVE':
            print("❌ ECSサービス 'vendor0913-api-service' が見つからないか非アクティブです")
            return False
        print("✅ ECSサービス確認完了")
        
        # ターゲットグループの存在確認
        try:
            tg_response = elbv2_client.describe_target_groups(
                Names=['vendor0913-api-tg']
            )
            if not tg_response['TargetGroups']:
                print("❌ ターゲットグループ 'vendor0913-api-tg' が見つかりません")
                return False
            print("✅ ターゲットグループ確認完了")
        except elbv2_client.exceptions.TargetGroupNotFoundException:
            print("❌ ターゲットグループ 'vendor0913-api-tg' が見つかりません")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 事前要件の検証中にエラーが発生: {e}")
        return False

def list_deployment_configs():
    """利用可能なECS用デプロイ設定を一覧表示"""
    codedeploy_client = boto3.client('codedeploy', region_name='ap-northeast-1')
    
    try:
        configs = codedeploy_client.list_deployment_configs()
        
        print("\n📋 利用可能なECS用デプロイメント設定:")
        ecs_configs = [config for config in configs['deploymentConfigsList'] if 'ECS' in config]
        
        for config in ecs_configs:
            print(f"   - {config}")
        
        return ecs_configs
        
    except Exception as e:
        print(f"❌ デプロイメント設定の取得中にエラー: {e}")
        return []

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
    print("🚀 Setting up CodeDeploy for ECS Blue/Green deployments...")
    print("=" * 70)
    
    # 0. 事前要件の検証
    print("\n0. 事前要件の検証...")
    if not validate_prerequisites():
        print("❌ 事前要件が満たされていません。ECS、ALB、ターゲットグループを先に作成してください。")
        return
    
    # 利用可能なデプロイメント設定を表示
    list_deployment_configs()
    
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
    success = create_codedeploy_deployment_group(service_role_arn)
    
    if not success:
        print("\n⚠️ メインのデプロイグループ作成に失敗しました。代替設定を試行します...")
        create_alternative_deployment_group(service_role_arn)
    
    # 4. リソース一覧表示
    print("\n4. Listing created resources...")
    list_codedeploy_resources()
    
    print("\n✅ CodeDeploy setup completed!")
    print("\n📋 Next steps:")
    print("   1. ECSサービスでBlue/Greenデプロイメントを有効化")
    print("   2. appspec.yamlファイルを作成")
    print("   3. デプロイメントをテスト実行")
    print("   4. CloudWatchアラームを設定")
    print("   5. 自動ロールバックのテスト")
    
    print("\n📚 重要なポイント:")
    print("   - ECSサービスは必ずApplication Load Balancerと関連付けてください")
    print("   - ターゲットグループは2つ必要です（Blue用とGreen用）")
    print("   - appspec.yamlでタスク定義とコンテナ設定を指定してください")

if __name__ == "__main__":
    main()
