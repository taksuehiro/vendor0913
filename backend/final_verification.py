#!/usr/bin/env python3
"""
最終検証スクリプト
全システムの動作確認とパフォーマンステスト
"""

import boto3
import json
import time
import requests
import subprocess
import sys
from datetime import datetime

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

def check_ecs_services():
    """ECSサービスの状態をチェック"""
    print("\n🔍 ECS Services Check...")
    
    try:
        ecs_client = boto3.client('ecs', region_name='ap-northeast-1')
        
        # クラスター一覧
        clusters = ecs_client.list_clusters()
        vendor_clusters = [c for c in clusters['clusterArns'] if 'vendor0913' in c]
        
        if not vendor_clusters:
            print("❌ No ECS clusters found")
            return False
        
        print(f"   ✅ ECS Clusters: {len(vendor_clusters)}")
        
        # サービス状態確認
        for cluster_arn in vendor_clusters:
            cluster_name = cluster_arn.split('/')[-1]
            services = ecs_client.list_services(cluster=cluster_arn)
            
            if services['serviceArns']:
                service_details = ecs_client.describe_services(
                    cluster=cluster_arn,
                    services=services['serviceArns']
                )
                
                for service in service_details['services']:
                    service_name = service['serviceName']
                    status = service['status']
                    running = service['runningCount']
                    desired = service['desiredCount']
                    pending = service['pendingCount']
                    
                    print(f"   ✅ Service: {service_name}")
                    print(f"      Status: {status}")
                    print(f"      Running: {running}/{desired}")
                    print(f"      Pending: {pending}")
                    
                    if status != 'ACTIVE' or running != desired or pending > 0:
                        print(f"      ⚠️ Service may not be healthy")
                        return False
        
        return True
        
    except Exception as e:
        print(f"❌ ECS services check error: {e}")
        return False

def check_alb_health():
    """ALBのヘルスをチェック"""
    print("\n🔍 ALB Health Check...")
    
    try:
        elbv2_client = boto3.client('elbv2', region_name='ap-northeast-1')
        
        # ALB一覧
        albs = elbv2_client.describe_load_balancers()
        vendor_albs = [alb for alb in albs['LoadBalancers'] if 'vendor0913' in alb['LoadBalancerName']]
        
        if not vendor_albs:
            print("❌ No ALBs found")
            return False
        
        print(f"   ✅ ALBs: {len(vendor_albs)}")
        
        for alb in vendor_albs:
            alb_name = alb['LoadBalancerName']
            alb_dns = alb['DNSName']
            state = alb['State']['Code']
            
            print(f"   ✅ ALB: {alb_name}")
            print(f"      DNS: {alb_dns}")
            print(f"      State: {state}")
            
            if state != 'active':
                print(f"      ⚠️ ALB is not active")
                return False
            
            # ターゲットグループのヘルスチェック
            target_groups = elbv2_client.describe_target_groups(
                LoadBalancerArn=alb['LoadBalancerArn']
            )
            
            for tg in target_groups['TargetGroups']:
                tg_name = tg['TargetGroupName']
                health = elbv2_client.describe_target_health(
                    TargetGroupArn=tg['TargetGroupArn']
                )
                
                healthy_targets = len([t for t in health['TargetHealthDescriptions'] 
                                     if t['TargetHealth']['State'] == 'healthy'])
                total_targets = len(health['TargetHealthDescriptions'])
                
                print(f"      Target Group: {tg_name}")
                print(f"      Healthy Targets: {healthy_targets}/{total_targets}")
                
                if healthy_targets == 0:
                    print(f"      ⚠️ No healthy targets")
                    return False
        
        return True
        
    except Exception as e:
        print(f"❌ ALB health check error: {e}")
        return False

def check_database_connection():
    """データベース接続をチェック"""
    print("\n🔍 Database Connection Check...")
    
    try:
        # Aurora Data API接続テスト
        result = subprocess.run([
            sys.executable, 'backend/test_aurora_data_api.py'
        ], capture_output=True, text=True, check=True)
        
        print("   ✅ Aurora Data API connection successful")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Aurora Data API connection failed: {e}")
        print(f"      Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"   ❌ Database connection check error: {e}")
        return False

def check_api_endpoints():
    """APIエンドポイントをチェック"""
    print("\n🔍 API Endpoints Check...")
    
    try:
        # ALBのDNS名を取得
        elbv2_client = boto3.client('elbv2', region_name='ap-northeast-1')
        albs = elbv2_client.describe_load_balancers()
        vendor_albs = [alb for alb in albs['LoadBalancers'] if 'vendor0913' in alb['LoadBalancerName']]
        
        if not vendor_albs:
            print("❌ No ALBs found for API testing")
            return False
        
        alb_dns = vendor_albs[0]['DNSName']
        base_url = f"https://{alb_dns}"
        
        # ヘルスチェックエンドポイント
        try:
            response = requests.get(f"{base_url}/health", timeout=10)
            if response.status_code == 200:
                print("   ✅ Health endpoint: OK")
            else:
                print(f"   ❌ Health endpoint: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Health endpoint error: {e}")
            return False
        
        # ベンダー一覧エンドポイント
        try:
            response = requests.get(f"{base_url}/vendors", timeout=10)
            if response.status_code in [200, 404]:  # 404はデータがない場合
                print("   ✅ Vendors endpoint: OK")
            else:
                print(f"   ❌ Vendors endpoint: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Vendors endpoint error: {e}")
            return False
        
        # 検索エンドポイント
        try:
            response = requests.post(f"{base_url}/search/documents?query=test&limit=1", timeout=10)
            if response.status_code in [200, 404]:  # 404はデータがない場合
                print("   ✅ Search endpoint: OK")
            else:
                print(f"   ❌ Search endpoint: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Search endpoint error: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoints check error: {e}")
        return False

def check_security_settings():
    """セキュリティ設定をチェック"""
    print("\n🔍 Security Settings Check...")
    
    try:
        # WAF設定確認
        wafv2_client = boto3.client('wafv2', region_name='ap-northeast-1')
        web_acls = wafv2_client.list_web_acls(Scope='REGIONAL')
        vendor_wafs = [waf for waf in web_acls['WebACLs'] if 'vendor0913' in waf['Name']]
        
        if vendor_wafs:
            print(f"   ✅ WAF Web ACLs: {len(vendor_wafs)}")
        else:
            print("   ⚠️ No WAF Web ACLs found")
        
        # Secrets Manager確認
        secrets_client = boto3.client('secretsmanager', region_name='ap-northeast-1')
        secrets = secrets_client.list_secrets()
        vendor_secrets = [s for s in secrets['SecretList'] if 'vendor0913' in s['Name']]
        
        if vendor_secrets:
            print(f"   ✅ Secrets: {len(vendor_secrets)}")
        else:
            print("   ⚠️ No secrets found")
        
        # CloudWatchアラーム確認
        cloudwatch_client = boto3.client('cloudwatch', region_name='ap-northeast-1')
        alarms = cloudwatch_client.describe_alarms()
        vendor_alarms = [a for a in alarms['MetricAlarms'] if 'vendor0913' in a['AlarmName']]
        
        if vendor_alarms:
            print(f"   ✅ CloudWatch Alarms: {len(vendor_alarms)}")
        else:
            print("   ⚠️ No CloudWatch alarms found")
        
        return True
        
    except Exception as e:
        print(f"❌ Security settings check error: {e}")
        return False

def check_monitoring():
    """監視設定をチェック"""
    print("\n🔍 Monitoring Check...")
    
    try:
        # CloudWatchダッシュボード確認
        cloudwatch_client = boto3.client('cloudwatch', region_name='ap-northeast-1')
        dashboards = cloudwatch_client.list_dashboards()
        vendor_dashboards = [d for d in dashboards['DashboardEntries'] if 'vendor0913' in d['DashboardName']]
        
        if vendor_dashboards:
            print(f"   ✅ CloudWatch Dashboards: {len(vendor_dashboards)}")
        else:
            print("   ⚠️ No CloudWatch dashboards found")
        
        # ロググループ確認
        logs_client = boto3.client('logs', region_name='ap-northeast-1')
        log_groups = logs_client.describe_log_groups()
        vendor_logs = [lg for lg in log_groups['logGroups'] if 'vendor0913' in lg['logGroupName']]
        
        if vendor_logs:
            print(f"   ✅ CloudWatch Log Groups: {len(vendor_logs)}")
        else:
            print("   ⚠️ No CloudWatch log groups found")
        
        # SNSトピック確認
        sns_client = boto3.client('sns', region_name='ap-northeast-1')
        topics = sns_client.list_topics()
        vendor_topics = [t for t in topics['Topics'] if 'vendor0913' in t['TopicArn']]
        
        if vendor_topics:
            print(f"   ✅ SNS Topics: {len(vendor_topics)}")
        else:
            print("   ⚠️ No SNS topics found")
        
        return True
        
    except Exception as e:
        print(f"❌ Monitoring check error: {e}")
        return False

def check_cicd_pipeline():
    """CI/CDパイプラインをチェック"""
    print("\n🔍 CI/CD Pipeline Check...")
    
    try:
        # GitHub Actionsワークフローファイル確認
        workflow_files = [
            '.github/workflows/deploy-frontend.yml',
            '.github/workflows/deploy-backend.yml',
            '.github/workflows/deploy-full-stack.yml'
        ]
        
        existing_workflows = 0
        for workflow in workflow_files:
            try:
                with open(workflow, 'r') as f:
                    content = f.read()
                    if 'vendor0913' in content:
                        existing_workflows += 1
                        print(f"   ✅ {workflow}")
            except FileNotFoundError:
                print(f"   ❌ {workflow} not found")
        
        if existing_workflows == len(workflow_files):
            print(f"   ✅ All GitHub Actions workflows found")
        else:
            print(f"   ⚠️ {existing_workflows}/{len(workflow_files)} workflows found")
        
        # CodeDeploy設定確認
        codedeploy_client = boto3.client('codedeploy', region_name='ap-northeast-1')
        apps = codedeploy_client.list_applications()
        vendor_apps = [app for app in apps['applications'] if 'vendor0913' in app]
        
        if vendor_apps:
            print(f"   ✅ CodeDeploy Applications: {len(vendor_apps)}")
        else:
            print("   ⚠️ No CodeDeploy applications found")
        
        return True
        
    except Exception as e:
        print(f"❌ CI/CD pipeline check error: {e}")
        return False

def performance_test():
    """パフォーマンステストを実行"""
    print("\n🔍 Performance Test...")
    
    try:
        # ALBのDNS名を取得
        elbv2_client = boto3.client('elbv2', region_name='ap-northeast-1')
        albs = elbv2_client.describe_load_balancers()
        vendor_albs = [alb for alb in albs['LoadBalancers'] if 'vendor0913' in alb['LoadBalancerName']]
        
        if not vendor_albs:
            print("❌ No ALBs found for performance testing")
            return False
        
        alb_dns = vendor_albs[0]['DNSName']
        base_url = f"https://{alb_dns}"
        
        # レスポンス時間テスト
        start_time = time.time()
        response = requests.get(f"{base_url}/health", timeout=10)
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # ミリ秒
        
        print(f"   ✅ Health endpoint response time: {response_time:.2f}ms")
        
        if response_time > 2000:  # 2秒以上
            print(f"   ⚠️ Response time is slow: {response_time:.2f}ms")
            return False
        
        # 複数リクエストテスト
        success_count = 0
        total_requests = 10
        
        for i in range(total_requests):
            try:
                response = requests.get(f"{base_url}/health", timeout=5)
                if response.status_code == 200:
                    success_count += 1
            except Exception as e:
                print(f"   ⚠️ Request {i+1} failed: {e}")
        
        success_rate = (success_count / total_requests) * 100
        print(f"   ✅ Success rate: {success_rate:.1f}% ({success_count}/{total_requests})")
        
        if success_rate < 90:  # 90%未満
            print(f"   ⚠️ Success rate is low: {success_rate:.1f}%")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test error: {e}")
        return False

def generate_verification_report():
    """検証レポートを生成"""
    print("\n📊 Generating verification report...")
    
    report = {
        "verification_date": datetime.now().isoformat(),
        "day": "Day20",
        "checks": {
            "aws_credentials": check_aws_credentials(),
            "ecs_services": check_ecs_services(),
            "alb_health": check_alb_health(),
            "database_connection": check_database_connection(),
            "api_endpoints": check_api_endpoints(),
            "security_settings": check_security_settings(),
            "monitoring": check_monitoring(),
            "cicd_pipeline": check_cicd_pipeline(),
            "performance_test": performance_test()
        }
    }
    
    # 成功したチェック数
    successful_checks = sum(1 for check in report["checks"].values() if check)
    total_checks = len(report["checks"])
    
    report["summary"] = {
        "total_checks": total_checks,
        "successful_checks": successful_checks,
        "success_rate": f"{(successful_checks/total_checks)*100:.1f}%"
    }
    
    # レポートをファイルに保存
    with open('backend/day20-verification-report.json', 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ Verification report saved: day20-verification-report.json")
    print(f"   📈 Success rate: {report['summary']['success_rate']} ({successful_checks}/{total_checks})")
    
    return report

def main():
    """メイン実行関数"""
    print("🔍 Final verification for vendor0913 project...")
    print("=" * 60)
    
    # 各コンポーネントの確認
    check_aws_credentials()
    check_ecs_services()
    check_alb_health()
    check_database_connection()
    check_api_endpoints()
    check_security_settings()
    check_monitoring()
    check_cicd_pipeline()
    performance_test()
    
    # 検証レポート生成
    report = generate_verification_report()
    
    print("\n🎯 Final verification completed!")
    
    if report["summary"]["successful_checks"] == report["summary"]["total_checks"]:
        print("✅ All systems are working correctly!")
        print("🎉 Project deployment is successful!")
    else:
        print("⚠️ Some systems have issues. Please check the verification report.")
    
    print("\n📝 Next steps:")
    print("   1. Review the verification report")
    print("   2. Fix any identified issues")
    print("   3. Monitor system performance")
    print("   4. Update documentation as needed")

if __name__ == "__main__":
    main()
