#!/usr/bin/env python3
"""
ECSサービス更新スクリプト
タスク定義の更新とサービスの再デプロイ
"""

import boto3
import json
import time
import sys

def get_current_task_definition(cluster_name, service_name):
    """現在のタスク定義を取得"""
    ecs_client = boto3.client('ecs', region_name='ap-northeast-1')
    
    try:
        response = ecs_client.describe_services(
            cluster=cluster_name,
            services=[service_name]
        )
        
        if not response['services']:
            print(f"❌ Service {service_name} not found")
            return None
        
        service = response['services'][0]
        task_definition_arn = service['taskDefinition']
        
        # タスク定義の詳細を取得
        task_def_response = ecs_client.describe_task_definition(
            taskDefinition=task_definition_arn
        )
        
        return task_def_response['taskDefinition']
        
    except Exception as e:
        print(f"❌ Error getting current task definition: {e}")
        return None

def update_task_definition_image(task_definition, new_image_uri):
    """タスク定義のイメージURIを更新"""
    try:
        # タスク定義をコピーして新しいバージョンを作成
        new_task_definition = task_definition.copy()
        
        # 不要なフィールドを削除
        fields_to_remove = [
            'taskDefinitionArn', 'revision', 'status', 'requiresAttributes',
            'placementConstraints', 'compatibilities', 'registeredAt',
            'registeredBy', 'tags'
        ]
        
        for field in fields_to_remove:
            new_task_definition.pop(field, None)
        
        # コンテナのイメージURIを更新
        for container in new_task_definition['containerDefinitions']:
            if container['name'] == 'vendor0913-api':
                container['image'] = new_image_uri
                print(f"✅ Updated image URI: {new_image_uri}")
                break
        
        return new_task_definition
        
    except Exception as e:
        print(f"❌ Error updating task definition: {e}")
        return None

def register_new_task_definition(task_definition):
    """新しいタスク定義を登録"""
    ecs_client = boto3.client('ecs', region_name='ap-northeast-1')
    
    try:
        response = ecs_client.register_task_definition(**task_definition)
        
        new_task_definition_arn = response['taskDefinition']['taskDefinitionArn']
        print(f"✅ New task definition registered: {new_task_definition_arn}")
        
        return new_task_definition_arn
        
    except Exception as e:
        print(f"❌ Error registering new task definition: {e}")
        return None

def update_ecs_service(cluster_name, service_name, new_task_definition_arn):
    """ECSサービスを更新"""
    ecs_client = boto3.client('ecs', region_name='ap-northeast-1')
    
    try:
        response = ecs_client.update_service(
            cluster=cluster_name,
            service=service_name,
            taskDefinition=new_task_definition_arn,
            forceNewDeployment=True
        )
        
        print(f"✅ ECS service updated: {service_name}")
        return response['service']
        
    except Exception as e:
        print(f"❌ Error updating ECS service: {e}")
        return None

def wait_for_service_stability(cluster_name, service_name, timeout_minutes=10):
    """サービスの安定化を待機"""
    ecs_client = boto3.client('ecs', region_name='ap-northeast-1')
    
    print(f"⏳ Waiting for service {service_name} to stabilize...")
    
    start_time = time.time()
    timeout_seconds = timeout_minutes * 60
    
    while time.time() - start_time < timeout_seconds:
        try:
            response = ecs_client.describe_services(
                cluster=cluster_name,
                services=[service_name]
            )
            
            if not response['services']:
                print("❌ Service not found")
                return False
            
            service = response['services'][0]
            deployments = service['deployments']
            
            # プライマリデプロイメントを確認
            primary_deployment = None
            for deployment in deployments:
                if deployment['status'] == 'PRIMARY':
                    primary_deployment = deployment
                    break
            
            if not primary_deployment:
                print("❌ Primary deployment not found")
                return False
            
            # デプロイメントが完了しているかチェック
            if (primary_deployment['status'] == 'PRIMARY' and 
                primary_deployment['runningCount'] == primary_deployment['desiredCount'] and
                primary_deployment['pendingCount'] == 0):
                
                print(f"✅ Service {service_name} is stable")
                return True
            
            print(f"   Running: {primary_deployment['runningCount']}/{primary_deployment['desiredCount']}, "
                  f"Pending: {primary_deployment['pendingCount']}")
            
            time.sleep(30)  # 30秒待機
            
        except Exception as e:
            print(f"❌ Error checking service stability: {e}")
            return False
    
    print(f"⚠️ Service stabilization timeout after {timeout_minutes} minutes")
    return False

def rollback_service(cluster_name, service_name, previous_task_definition_arn):
    """サービスをロールバック"""
    ecs_client = boto3.client('ecs', region_name='ap-northeast-1')
    
    try:
        response = ecs_client.update_service(
            cluster=cluster_name,
            service=service_name,
            taskDefinition=previous_task_definition_arn,
            forceNewDeployment=True
        )
        
        print(f"🔄 Service rolled back to: {previous_task_definition_arn}")
        return True
        
    except Exception as e:
        print(f"❌ Error rolling back service: {e}")
        return False

def get_service_health(cluster_name, service_name):
    """サービスのヘルスを確認"""
    ecs_client = boto3.client('ecs', region_name='ap-northeast-1')
    
    try:
        response = ecs_client.describe_services(
            cluster=cluster_name,
            services=[service_name]
        )
        
        if not response['services']:
            return None
        
        service = response['services'][0]
        
        health_info = {
            'service_name': service['serviceName'],
            'status': service['status'],
            'running_count': service['runningCount'],
            'desired_count': service['desiredCount'],
            'pending_count': service['pendingCount'],
            'task_definition': service['taskDefinition'],
            'deployments': len(service['deployments'])
        }
        
        return health_info
        
    except Exception as e:
        print(f"❌ Error getting service health: {e}")
        return None

def main():
    """メイン実行関数"""
    if len(sys.argv) != 3:
        print("Usage: python update_ecs_service.py <cluster_name> <service_name>")
        print("Example: python update_ecs_service.py vendor0913-cluster vendor0913-api-service")
        sys.exit(1)
    
    cluster_name = sys.argv[1]
    service_name = sys.argv[2]
    
    print(f"🚀 Updating ECS service: {service_name} in cluster: {cluster_name}")
    print("=" * 60)
    
    # 1. 現在のタスク定義を取得
    print("\n1. Getting current task definition...")
    current_task_definition = get_current_task_definition(cluster_name, service_name)
    
    if not current_task_definition:
        print("❌ Failed to get current task definition. Exiting.")
        sys.exit(1)
    
    current_task_definition_arn = current_task_definition['taskDefinitionArn']
    print(f"   Current task definition: {current_task_definition_arn}")
    
    # 2. 新しいイメージURIを取得（環境変数または引数から）
    new_image_uri = input("Enter new image URI (or press Enter to use current): ").strip()
    
    if not new_image_uri:
        print("❌ New image URI is required. Exiting.")
        sys.exit(1)
    
    # 3. タスク定義を更新
    print("\n2. Updating task definition...")
    updated_task_definition = update_task_definition_image(current_task_definition, new_image_uri)
    
    if not updated_task_definition:
        print("❌ Failed to update task definition. Exiting.")
        sys.exit(1)
    
    # 4. 新しいタスク定義を登録
    print("\n3. Registering new task definition...")
    new_task_definition_arn = register_new_task_definition(updated_task_definition)
    
    if not new_task_definition_arn:
        print("❌ Failed to register new task definition. Exiting.")
        sys.exit(1)
    
    # 5. ECSサービスを更新
    print("\n4. Updating ECS service...")
    updated_service = update_ecs_service(cluster_name, service_name, new_task_definition_arn)
    
    if not updated_service:
        print("❌ Failed to update ECS service. Exiting.")
        sys.exit(1)
    
    # 6. サービスの安定化を待機
    print("\n5. Waiting for service stability...")
    if not wait_for_service_stability(cluster_name, service_name):
        print("⚠️ Service did not stabilize. Consider rolling back.")
        
        rollback_choice = input("Do you want to rollback? (y/N): ").strip().lower()
        if rollback_choice == 'y':
            rollback_service(cluster_name, service_name, current_task_definition_arn)
        else:
            print("⚠️ Service update completed but may not be stable.")
    
    # 7. 最終的なヘルスチェック
    print("\n6. Final health check...")
    health_info = get_service_health(cluster_name, service_name)
    
    if health_info:
        print(f"✅ Service Health:")
        print(f"   Status: {health_info['status']}")
        print(f"   Running: {health_info['running_count']}/{health_info['desired_count']}")
        print(f"   Pending: {health_info['pending_count']}")
        print(f"   Task Definition: {health_info['task_definition']}")
    else:
        print("❌ Failed to get service health information")
    
    print("\n🎉 ECS service update completed!")

if __name__ == "__main__":
    main()
