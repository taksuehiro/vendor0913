#!/usr/bin/env python3
"""
Day19統合デプロイメントスクリプト
CI/CDパイプライン、Blue/Greenデプロイメント、ECS更新の統合
"""

import boto3
import json
import time
import subprocess
import sys
import os

def check_aws_credentials():
    """AWS認証情報をチェック"""
    try:
        sts_client = boto3.client('sts')
        response = sts_client.get_caller_identity()
        print(f"✅ AWS認証情報確認: {response['Arn']}")
        return True
    except Exception as e:
        print(f"❌ AWS認証情報エラー: {e}")
        return False

def check_github_secrets():
    """GitHub Secretsの確認"""
    required_secrets = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'NEXT_PUBLIC_API_BASE'
    ]
    
    print("🔍 GitHub Secrets確認...")
    missing_secrets = []
    
    for secret in required_secrets:
        if not os.getenv(secret):
            missing_secrets.append(secret)
    
    if missing_secrets:
        print(f"❌ 不足しているSecrets: {', '.join(missing_secrets)}")
        print("   GitHubリポジトリのSettings > Secrets and variables > Actionsで設定してください")
        return False
    else:
        print("✅ 必要なGitHub Secretsが設定されています")
        return True

def setup_codedeploy():
    """CodeDeploy設定を実行"""
    print("\n🛠️ CodeDeploy設定を実行中...")
    try:
        result = subprocess.run([sys.executable, 'setup_codedeploy.py'], 
                              capture_output=True, text=True, check=True)
        print("✅ CodeDeploy設定完了")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ CodeDeploy設定失敗: {e}")
        print(f"   エラー出力: {e.stderr}")
        return False

def create_github_workflows():
    """GitHub Actionsワークフローを作成"""
    print("\n📝 GitHub Actionsワークフローを作成中...")
    
    workflows = [
        '.github/workflows/deploy-frontend.yml',
        '.github/workflows/deploy-backend.yml',
        '.github/workflows/deploy-full-stack.yml'
    ]
    
    created_workflows = 0
    for workflow in workflows:
        if os.path.exists(workflow):
            print(f"   ✅ {workflow} が存在します")
            created_workflows += 1
        else:
            print(f"   ❌ {workflow} が見つかりません")
    
    if created_workflows == len(workflows):
        print("✅ すべてのGitHub Actionsワークフローが準備されています")
        return True
    else:
        print(f"⚠️ {created_workflows}/{len(workflows)} のワークフローが準備されています")
        return False

def test_ecs_service_update():
    """ECSサービス更新のテスト"""
    print("\n🧪 ECSサービス更新のテスト...")
    
    try:
        # 現在のECSサービス情報を取得
        ecs_client = boto3.client('ecs', region_name='ap-northeast-1')
        
        clusters = ecs_client.list_clusters()
        cluster_arn = None
        for cluster in clusters['clusterArns']:
            if 'vendor0913' in cluster:
                cluster_arn = cluster
                break
        
        if not cluster_arn:
            print("❌ ECSクラスターが見つかりません")
            return False
        
        services = ecs_client.list_services(cluster=cluster_arn)
        service_arn = None
        for service in services['serviceArns']:
            if 'vendor0913' in service:
                service_arn = service
                break
        
        if not service_arn:
            print("❌ ECSサービスが見つかりません")
            return False
        
        cluster_name = cluster_arn.split('/')[-1]
        service_name = service_arn.split('/')[-1]
        
        print(f"   ✅ クラスター: {cluster_name}")
        print(f"   ✅ サービス: {service_name}")
        
        # サービスの現在の状態を確認
        response = ecs_client.describe_services(
            cluster=cluster_name,
            services=[service_name]
        )
        
        if response['services']:
            service = response['services'][0]
            print(f"   ✅ 現在の状態: {service['status']}")
            print(f"   ✅ 実行中タスク: {service['runningCount']}/{service['desiredCount']}")
            print(f"   ✅ タスク定義: {service['taskDefinition']}")
        
        return True
        
    except Exception as e:
        print(f"❌ ECSサービス更新テストエラー: {e}")
        return False

def verify_codedeploy_setup():
    """CodeDeploy設定の確認"""
    print("\n🔍 CodeDeploy設定の確認...")
    
    try:
        codedeploy_client = boto3.client('codedeploy', region_name='ap-northeast-1')
        
        # アプリケーション確認
        apps = codedeploy_client.list_applications()
        vendor_apps = [app for app in apps['applications'] if 'vendor0913' in app]
        
        if vendor_apps:
            print(f"   ✅ CodeDeployアプリケーション: {len(vendor_apps)}個")
            for app in vendor_apps:
                print(f"      - {app}")
        else:
            print("   ❌ CodeDeployアプリケーションが見つかりません")
            return False
        
        # デプロイメントグループ確認
        for app in vendor_apps:
            dgs = codedeploy_client.list_deployment_groups(applicationName=app)
            if dgs['deploymentGroups']:
                print(f"   ✅ デプロイメントグループ: {len(dgs['deploymentGroups'])}個")
                for dg in dgs['deploymentGroups']:
                    print(f"      - {dg}")
            else:
                print(f"   ❌ アプリケーション {app} のデプロイメントグループが見つかりません")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ CodeDeploy設定確認エラー: {e}")
        return False

def create_deployment_summary():
    """デプロイメントサマリーを作成"""
    summary = {
        "deployment_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "day": "Day19",
        "components": [
            "GitHub Actions CI/CD Pipeline",
            "CodeDeploy Blue/Green Deployment",
            "ECS Service Update Automation",
            "Deployment Hooks and Monitoring"
        ],
        "files_created": [
            ".github/workflows/deploy-frontend.yml",
            ".github/workflows/deploy-backend.yml", 
            ".github/workflows/deploy-full-stack.yml",
            "backend/codedeploy-appspec.yml",
            "backend/setup_codedeploy.py",
            "backend/update_ecs_service.py",
            "backend/deploy_day19.py"
        ],
        "next_steps": [
            "Configure GitHub repository secrets",
            "Test CI/CD pipeline with code push",
            "Verify Blue/Green deployment",
            "Monitor deployment metrics",
            "Create deployment runbook"
        ]
    }
    
    with open('backend/day19-deployment-summary.json', 'w') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"✅ デプロイメントサマリー作成: day19-deployment-summary.json")

def main():
    """メイン実行関数"""
    print("🚀 Day19統合デプロイメント開始...")
    print("=" * 60)
    
    # 0. AWS認証情報確認
    if not check_aws_credentials():
        print("❌ AWS認証情報が正しく設定されていません")
        return
    
    # 1. GitHub Secrets確認
    if not check_github_secrets():
        print("⚠️ GitHub Secretsが不足していますが、続行します")
    
    # 2. CodeDeploy設定
    if not setup_codedeploy():
        print("⚠️ CodeDeploy設定に失敗しましたが、続行します")
    
    # 3. GitHub Actionsワークフロー確認
    if not create_github_workflows():
        print("⚠️ GitHub Actionsワークフローが不完全ですが、続行します")
    
    # 4. ECSサービス更新テスト
    if not test_ecs_service_update():
        print("⚠️ ECSサービス更新テストに失敗しましたが、続行します")
    
    # 5. CodeDeploy設定確認
    if not verify_codedeploy_setup():
        print("⚠️ CodeDeploy設定確認に失敗しましたが、続行します")
    
    # 6. デプロイメントサマリー作成
    create_deployment_summary()
    
    print("\n🎉 Day19デプロイメント完了!")
    print("\n📝 次のステップ:")
    print("   1. GitHubリポジトリのSecretsを設定")
    print("   2. コードをプッシュしてCI/CDパイプラインをテスト")
    print("   3. Blue/Greenデプロイメントをテスト")
    print("   4. デプロイメント監視を設定")
    print("   5. デプロイメント手順書を作成")
    
    print("\n🔗 重要なリンク:")
    print("   GitHub Actions: https://github.com/taksuehiro/vendor0913/actions")
    print("   CodeDeploy: https://ap-northeast-1.console.aws.amazon.com/codesuite/codedeploy/applications")
    print("   ECS: https://ap-northeast-1.console.aws.amazon.com/ecs/v2/clusters")

if __name__ == "__main__":
    main()
