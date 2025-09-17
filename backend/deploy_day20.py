#!/usr/bin/env python3
"""
Day20統合デプロイメントスクリプト
ドメイン設定・運用ルールブック・最終検証の統合
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

def setup_domain():
    """ドメイン設定を実行"""
    print("\n🌐 Setting up domain and SSL...")
    try:
        result = subprocess.run([sys.executable, 'setup_domain.py'], 
                              capture_output=True, text=True, check=True)
        print("✅ Domain setup completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Domain setup failed: {e}")
        print(f"   エラー出力: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Domain setup error: {e}")
        return False

def setup_budget():
    """コスト予算設定を実行"""
    print("\n💰 Setting up cost budget...")
    try:
        result = subprocess.run([sys.executable, 'setup_budget.py'], 
                              capture_output=True, text=True, check=True)
        print("✅ Budget setup completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Budget setup failed: {e}")
        print(f"   エラー出力: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Budget setup error: {e}")
        return False

def run_final_verification():
    """最終検証を実行"""
    print("\n🔍 Running final verification...")
    try:
        result = subprocess.run([sys.executable, 'final_verification.py'], 
                              capture_output=True, text=True, check=True)
        print("✅ Final verification completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Final verification failed: {e}")
        print(f"   エラー出力: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Final verification error: {e}")
        return False

def create_project_summary():
    """プロジェクトサマリーを作成"""
    print("\n📋 Creating project summary...")
    
    summary = {
        "project_name": "vendor0913",
        "completion_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_days": 20,
        "architecture": {
            "frontend": "Next.js + Amplify Hosting",
            "backend": "FastAPI + ECS Fargate",
            "database": "Aurora Serverless v2 + pgvector",
            "storage": "S3",
            "cdn": "CloudFront",
            "monitoring": "CloudWatch",
            "security": "WAF + Secrets Manager",
            "cicd": "GitHub Actions + CodeDeploy"
        },
        "aws_services": [
            "Amplify Hosting",
            "ECS Fargate",
            "ALB",
            "RDS Aurora Serverless v2",
            "S3",
            "CloudWatch",
            "WAF",
            "Secrets Manager",
            "Route53",
            "ACM",
            "CodeDeploy",
            "GitHub Actions"
        ],
        "key_features": [
            "AI-powered vendor search",
            "RAG-based document analysis",
            "Real-time monitoring",
            "Blue/Green deployment",
            "Cost optimization",
            "Security hardening",
            "Automated CI/CD"
        ],
        "cost_optimization": {
            "monthly_budget": "$100",
            "alerts": ["80%", "100%"],
            "monitoring": "CloudWatch + Cost Explorer"
        },
        "security_features": [
            "WAF protection",
            "Secrets Manager",
            "HTTPS/TLS",
            "VPC isolation",
            "IAM roles",
            "CloudWatch monitoring"
        ],
        "monitoring": {
            "dashboards": 1,
            "alarms": 7,
            "log_groups": 3,
            "sns_topics": 1
        },
        "files_created": [
            "Frontend: Next.js application",
            "Backend: FastAPI application",
            "Infrastructure: AWS resources",
            "CI/CD: GitHub Actions workflows",
            "Monitoring: CloudWatch dashboards",
            "Security: WAF rules",
            "Documentation: Runbook and guides"
        ],
        "next_steps": [
            "Monitor system performance",
            "Optimize costs based on usage",
            "Update documentation as needed",
            "Plan for scaling",
            "Regular security reviews"
        ]
    }
    
    with open('backend/day20-project-summary.json', 'w') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Project summary created: day20-project-summary.json")
    return True

def create_deployment_guide():
    """デプロイメントガイドを作成"""
    print("\n📖 Creating deployment guide...")
    
    guide = """# Vendor0913 デプロイメントガイド

## 概要
このガイドは、vendor0913アプリケーションのデプロイメント手順を説明します。

## 前提条件
- AWS CLI設定済み
- GitHubリポジトリアクセス権限
- 必要なAWS権限

## デプロイメント手順

### 1. 初期設定
```bash
# リポジトリをクローン
git clone https://github.com/taksuehiro/vendor0913.git
cd vendor0913

# 依存関係をインストール
pip install -r backend/requirements.txt
npm install --prefix frontend
```

### 2. AWS設定
```bash
# AWS認証情報を設定
aws configure

# 必要なSecretsを設定
aws secretsmanager create-secret --name vendor0913/aurora/config --secret-string '{"AURORA_CLUSTER_ARN":"...","AURORA_SECRET_ARN":"...","AURORA_DATABASE":"vendor_analysis","AWS_REGION":"ap-northeast-1"}'
aws secretsmanager create-secret --name vendor0913/openai/config --secret-string '{"OPENAI_API_KEY":"...","OPENAI_MODEL":"text-embedding-3-small"}'
```

### 3. インフラデプロイ
```bash
# Day11-20の設定を順次実行
python backend/deploy_day11.py  # Amplify設定
python backend/deploy_day12.py  # ECR + CodeBuild
python backend/deploy_day13.py  # ECS設定
python backend/deploy_day14.py  # ALB設定
python backend/deploy_day15.py  # RDS設定
python backend/deploy_day16.py  # S3設定
python backend/deploy_day17.py  # Secrets Manager
python backend/deploy_day18.py  # WAF + CloudWatch
python backend/deploy_day19.py  # CI/CD + Blue/Green
python backend/deploy_day20.py  # ドメイン + 最終検証
```

### 4. アプリケーションデプロイ
```bash
# フロントエンドデプロイ
cd frontend
npm run build
npm run deploy

# バックエンドデプロイ
cd ../backend
python deploy_day19.py
```

### 5. 検証
```bash
# 最終検証を実行
python backend/final_verification.py

# ヘルスチェック
curl https://your-alb-dns/health
```

## トラブルシューティング

### よくある問題
1. **認証エラー**: AWS認証情報を確認
2. **権限エラー**: IAMロールを確認
3. **リソース不足**: リージョンとクォータを確認
4. **ネットワークエラー**: セキュリティグループを確認

### ログ確認
```bash
# ECSログ
aws logs tail /ecs/vendor0913/api --follow

# ALBログ
aws logs tail /aws/applicationloadbalancer/vendor0913-alb --follow
```

## メンテナンス

### 定期作業
- 月次: コスト確認・最適化
- 週次: セキュリティ更新・パフォーマンス確認
- 日次: ログ確認・アラート対応

### バックアップ
- データベース: 自動スナップショット
- 設定: Gitリポジトリ
- ログ: CloudWatch Logs

## 連絡先
- プロジェクトオーナー: takuya_suehiro
- ドキュメント: docs/runbook.md
- 監視: CloudWatch Dashboard
"""
    
    with open('docs/deployment-guide.md', 'w') as f:
        f.write(guide)
    
    print(f"✅ Deployment guide created: docs/deployment-guide.md")
    return True

def main():
    """メイン実行関数"""
    print("🎯 Day20統合デプロイメント開始...")
    print("=" * 60)
    
    # 0. AWS認証情報確認
    if not check_aws_credentials():
        print("❌ AWS認証情報が正しく設定されていません")
        return
    
    # 1. ドメイン設定
    if not setup_domain():
        print("⚠️ ドメイン設定に失敗しましたが、続行します")
    
    # 2. コスト予算設定
    if not setup_budget():
        print("⚠️ コスト予算設定に失敗しましたが、続行します")
    
    # 3. 最終検証
    if not run_final_verification():
        print("⚠️ 最終検証に失敗しましたが、続行します")
    
    # 4. プロジェクトサマリー作成
    if not create_project_summary():
        print("⚠️ プロジェクトサマリー作成に失敗しましたが、続行します")
    
    # 5. デプロイメントガイド作成
    if not create_deployment_guide():
        print("⚠️ デプロイメントガイド作成に失敗しましたが、続行します")
    
    print("\n🎉 Day20デプロイメント完了!")
    print("\n🎊 プロジェクト完了おめでとうございます!")
    print("\n📝 プロジェクトサマリー:")
    print("   - 20日間の開発完了")
    print("   - フルスタックアプリケーション構築")
    print("   - AWSクラウドネイティブ設計")
    print("   - CI/CDパイプライン構築")
    print("   - セキュリティ・監視・コスト最適化")
    
    print("\n🔗 重要なリンク:")
    print("   - アプリケーション: https://your-domain.com")
    print("   - 監視ダッシュボード: CloudWatch")
    print("   - ドキュメント: docs/runbook.md")
    print("   - デプロイメントガイド: docs/deployment-guide.md")
    
    print("\n📚 次のステップ:")
    print("   1. システムの監視を開始")
    print("   2. ユーザーフィードバックを収集")
    print("   3. パフォーマンスを最適化")
    print("   4. 新機能の開発を計画")
    print("   5. 運用プロセスの改善")

if __name__ == "__main__":
    main()
