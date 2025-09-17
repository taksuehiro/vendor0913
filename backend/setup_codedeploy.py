#!/usr/bin/env python3
"""
CodeDeploy設定スクリプト
Blue/Greenデプロイメントの設定
"""

import boto3
import json
import time

def create_codedeploy_application():
    """CodeDeployアプリケーションを作成"""
    codedeploy_client = boto3.client('codedeploy', region_name='ap-northeast-1')
    
    try:
        response = codedeploy_client.create_application(
            applicationName='vendor0913-api-app',
            computePlatform='ECS',
            tags=[
                {
                    'Key': 'Project',
                    'Value': 'tak-vendor2-0912'
                },
                {
                    'Key': 'Owner',
                    'Value': 'takuya_suehiro'
                },
                {
                    'Key': 'Environment',
                    'Value': 'production'
                }
            ]
        )
        
        print(f"✅ CodeDeploy Application created: vendor0913-api-app")
        return True
        
    except codedeploy_client.exceptions.ApplicationAlreadyExistsException:
        print(f"ℹ️ CodeDeploy Application already exists: vendor0913-api-app")
        return True
    except Exception as e:
        print(f"❌ Error creating CodeDeploy Application: {e}")
        return False

def create_codedeploy_deployment_group():
    """CodeDeployデプロイメントグループを作成"""
    codedeploy_client = boto3.client('codedeploy', region_name='ap-northeast-1')
    
    try:
        # ECSクラスターとサービスを取得
        ecs_client = boto3.client('ecs', region_name='ap-northeast-1')
        
        # クラスター情報を取得
        clusters = ecs_client.list_clusters()
        cluster_arn = None
        for cluster in clusters['clusterArns']:
            if 'vendor0913' in cluster:
                cluster_arn = cluster
                break
        
        if not cluster_arn:
            print("❌ ECS cluster not found")
            return False
        
        # サービス情報を取得
        services = ecs_client.list_services(cluster=cluster_arn)
        service_arn = None
        for service in services['serviceArns']:
            if 'vendor0913' in service:
                service_arn = service
                break
        
        if not service_arn:
            print("❌ ECS service not found")
            return False
        
        # ターゲットグループを取得
        elbv2_client = boto3.client('elbv2', region_name='ap-northeast-1')
        target_groups = elbv2_client.describe_target_groups()
        target_group_arn = None
        for tg in target_groups['TargetGroups']:
            if 'vendor0913' in tg['TargetGroupName']:
                target_group_arn = tg['TargetGroupArn']
                break
        
        if not target_group_arn:
            print("❌ Target group not found")
            return False
        
        # デプロイメントグループを作成
        response = codedeploy_client.create_deployment_group(
            applicationName='vendor0913-api-app',
            deploymentGroupName='vendor0913-api-dg',
            serviceRoleArn='arn:aws:iam::067717894185:role/CodeDeployServiceRole',
            deploymentConfigName='CodeDeployDefault.ECSAllAtOnce',
            ecsServices=[
                {
                    'serviceName': service_arn.split('/')[-1],
                    'clusterName': cluster_arn.split('/')[-1]
                }
            ],
            loadBalancerInfo={
                'targetGroupInfoList': [
                    {
                        'name': 'vendor0913-api-tg-http'
                    }
                ]
            },
            blueGreenDeploymentConfiguration={
                'deploymentReadyOption': {
                    'actionOnTimeout': 'CONTINUE_DEPLOYMENT',
                    'waitTimeInMinutes': 0
                },
                'greenFleetProvisioningOption': {
                    'action': 'COPY_AUTO_SCALING_GROUP'
                },
                'terminateBlueInstancesOnDeploymentSuccess': {
                    'action': 'TERMINATE',
                    'terminationWaitTimeInMinutes': 5
                }
            },
            autoRollbackConfiguration={
                'enabled': True,
                'events': ['DEPLOYMENT_FAILURE', 'DEPLOYMENT_STOP_ON_ALARM', 'DEPLOYMENT_STOP_ON_REQUEST']
            },
            alarmConfiguration={
                'enabled': True,
                'alarms': [
                    {
                        'name': 'vendor0913-alb-high-5xx-error-rate'
                    },
                    {
                        'name': 'vendor0913-ecs-high-cpu-utilization'
                    }
                ]
            }
        )
        
        print(f"✅ CodeDeploy Deployment Group created: vendor0913-api-dg")
        return True
        
    except codedeploy_client.exceptions.DeploymentGroupAlreadyExistsException:
        print(f"ℹ️ CodeDeploy Deployment Group already exists: vendor0913-api-dg")
        return True
    except Exception as e:
        print(f"❌ Error creating CodeDeploy Deployment Group: {e}")
        return False

def create_codedeploy_service_role():
    """CodeDeployサービスロールを作成"""
    iam_client = boto3.client('iam', region_name='ap-northeast-1')
    
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
        
        # 権限ポリシー
        permissions_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "ecs:CreateTaskSet",
                        "ecs:DeleteTaskSet",
                        "ecs:DescribeServices",
                        "ecs:UpdateServicePrimaryTaskSet",
                        "ecs:DescribeTaskDefinition",
                        "ecs:DescribeTaskSets",
                        "ecs:UpdateService",
                        "elasticloadbalancing:DescribeTargetGroups",
                        "elasticloadbalancing:DescribeLoadBalancers",
                        "elasticloadbalancing:DescribeListeners",
                        "elasticloadbalancing:ModifyListener",
                        "elasticloadbalancing:DescribeRules",
                        "elasticloadbalancing:ModifyRule",
                        "cloudwatch:DescribeAlarms",
                        "sns:Publish",
                        "iam:PassRole"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        # ロールを作成
        response = iam_client.create_role(
            RoleName='CodeDeployServiceRole',
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='CodeDeploy service role for ECS Blue/Green deployments',
            Tags=[
                {
                    'Key': 'Project',
                    'Value': 'tak-vendor2-0912'
                },
                {
                    'Key': 'Owner',
                    'Value': 'takuya_suehiro'
                }
            ]
        )
        
        # 権限ポリシーをアタッチ
        iam_client.put_role_policy(
            RoleName='CodeDeployServiceRole',
            PolicyName='CodeDeployServicePolicy',
            PolicyDocument=json.dumps(permissions_policy)
        )
        
        print(f"✅ CodeDeploy Service Role created: CodeDeployServiceRole")
        return True
        
    except iam_client.exceptions.EntityAlreadyExistsException:
        print(f"ℹ️ CodeDeploy Service Role already exists: CodeDeployServiceRole")
        return True
    except Exception as e:
        print(f"❌ Error creating CodeDeploy Service Role: {e}")
        return False

def create_deployment_hooks():
    """デプロイメントフック用のLambda関数を作成"""
    lambda_client = boto3.client('lambda', region_name='ap-northeast-1')
    
    # フック関数のコード
    hook_code = '''
import json
import boto3

def lambda_handler(event, context):
    print(f"Deployment hook triggered: {event}")
    
    # デプロイメントの前処理
    if 'BeforeInstall' in event.get('LifecycleEventHookExecutionId', ''):
        print("BeforeInstall hook: Preparing for deployment")
        
    elif 'AfterInstall' in event.get('LifecycleEventHookExecutionId', ''):
        print("AfterInstall hook: Post-installation tasks")
        
    elif 'BeforeAllowTraffic' in event.get('LifecycleEventHookExecutionId', ''):
        print("BeforeAllowTraffic hook: Pre-traffic validation")
        
    elif 'AfterAllowTraffic' in event.get('LifecycleEventHookExecutionId', ''):
        print("AfterAllowTraffic hook: Post-traffic validation")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hook executed successfully')
    }
'''
    
    hooks = [
        'vendor0913-pre-deploy-hook',
        'vendor0913-post-deploy-hook',
        'vendor0913-pre-traffic-hook',
        'vendor0913-post-traffic-hook'
    ]
    
    created_hooks = 0
    for hook_name in hooks:
        try:
            response = lambda_client.create_function(
                FunctionName=hook_name,
                Runtime='python3.9',
                Role='arn:aws:iam::067717894185:role/lambda-execution-role',
                Handler='index.lambda_handler',
                Code={'ZipFile': hook_code.encode()},
                Description=f'CodeDeploy hook for {hook_name}',
                Timeout=30,
                Tags={
                    'Project': 'tak-vendor2-0912',
                    'Owner': 'takuya_suehiro'
                }
            )
            
            print(f"✅ Lambda hook created: {hook_name}")
            created_hooks += 1
            
        except lambda_client.exceptions.ResourceConflictException:
            print(f"ℹ️ Lambda hook already exists: {hook_name}")
            created_hooks += 1
        except Exception as e:
            print(f"❌ Error creating Lambda hook {hook_name}: {e}")
    
    return created_hooks == len(hooks)

def list_codedeploy_resources():
    """CodeDeployリソースを一覧表示"""
    codedeploy_client = boto3.client('codedeploy', region_name='ap-northeast-1')
    
    try:
        # アプリケーション
        apps = codedeploy_client.list_applications()
        print("\n📋 CodeDeploy Applications:")
        for app in apps['applications']:
            if 'vendor0913' in app:
                print(f"   - {app}")
        
        # デプロイメントグループ
        for app in apps['applications']:
            if 'vendor0913' in app:
                dgs = codedeploy_client.list_deployment_groups(applicationName=app)
                print(f"\n📋 Deployment Groups for {app}:")
                for dg in dgs['deploymentGroups']:
                    print(f"   - {dg}")
        
        # デプロイメント履歴
        for app in apps['applications']:
            if 'vendor0913' in app:
                deployments = codedeploy_client.list_deployments(
                    applicationName=app,
                    maxResults=5
                )
                if deployments['deployments']:
                    print(f"\n📋 Recent Deployments for {app}:")
                    for deployment in deployments['deployments']:
                        print(f"   - {deployment}")
                
    except Exception as e:
        print(f"❌ Error listing CodeDeploy resources: {e}")

def main():
    """メイン実行関数"""
    print("🚀 Setting up CodeDeploy for Blue/Green deployments...")
    print("=" * 60)
    
    # 1. CodeDeployサービスロールを作成
    print("\n1. Creating CodeDeploy Service Role...")
    if not create_codedeploy_service_role():
        print("⚠️ Failed to create service role, but continuing...")
    
    # 2. CodeDeployアプリケーションを作成
    print("\n2. Creating CodeDeploy Application...")
    if not create_codedeploy_application():
        print("❌ Failed to create application. Exiting.")
        return
    
    # 3. CodeDeployデプロイメントグループを作成
    print("\n3. Creating CodeDeploy Deployment Group...")
    if not create_codedeploy_deployment_group():
        print("⚠️ Failed to create deployment group, but continuing...")
    
    # 4. デプロイメントフックを作成
    print("\n4. Creating Deployment Hooks...")
    if not create_deployment_hooks():
        print("⚠️ Failed to create some deployment hooks, but continuing...")
    
    # 5. 作成されたリソースを一覧表示
    print("\n5. Listing created resources...")
    list_codedeploy_resources()
    
    print("\n✅ CodeDeploy setup completed!")
    print("\n📝 Next steps:")
    print("   1. Test Blue/Green deployment")
    print("   2. Configure deployment hooks")
    print("   3. Set up monitoring and alerts")
    print("   4. Create deployment runbook")

if __name__ == "__main__":
    main()
