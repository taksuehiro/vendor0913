#!/usr/bin/env python3
"""
ドメイン設定スクリプト
Route53 + ACM + ALBの設定
"""

import boto3
import json
import time
import dns.resolver

def create_hosted_zone():
    """Route53ホストゾーンを作成"""
    route53_client = boto3.client('route53', region_name='us-east-1')  # Route53はus-east-1
    
    try:
        with open('route53-config.json', 'r') as f:
            config = json.load(f)
        
        hosted_zone_config = config['hostedZone']
        
        response = route53_client.create_hosted_zone(
            Name=hosted_zone_config['Name'],
            CallerReference=f"vendor0913-{int(time.time())}",
            HostedZoneConfig={
                'Comment': hosted_zone_config['Comment'],
                'PrivateZone': False
            }
        )
        
        hosted_zone_id = response['HostedZone']['Id'].split('/')[-1]
        name_servers = response['DelegationSet']['NameServers']
        
        print(f"✅ Hosted Zone created: {hosted_zone_config['Name']}")
        print(f"   Hosted Zone ID: {hosted_zone_id}")
        print(f"   Name Servers: {', '.join(name_servers)}")
        
        return hosted_zone_id, name_servers
        
    except route53_client.exceptions.HostedZoneAlreadyExists:
        print(f"ℹ️ Hosted Zone already exists: {hosted_zone_config['Name']}")
        # 既存のホストゾーンを取得
        response = route53_client.list_hosted_zones_by_name(DNSName=hosted_zone_config['Name'])
        if response['HostedZones']:
            hosted_zone_id = response['HostedZones'][0]['Id'].split('/')[-1]
            response = route53_client.get_hosted_zone(Id=hosted_zone_id)
            name_servers = response['DelegationSet']['NameServers']
            return hosted_zone_id, name_servers
        return None, None
    except Exception as e:
        print(f"❌ Error creating hosted zone: {e}")
        return None, None

def create_dns_records(hosted_zone_id):
    """DNSレコードを作成"""
    route53_client = boto3.client('route53', region_name='us-east-1')
    
    try:
        with open('route53-config.json', 'r') as f:
            config = json.load(f)
        
        records = config['records']
        created_records = 0
        
        for record in records:
            try:
                change_batch = {
                    'Changes': [
                        {
                            'Action': 'UPSERT',
                            'ResourceRecordSet': {
                                'Name': record['Name'],
                                'Type': record['Type'],
                                'TTL': record.get('TTL', 300)
                            }
                        }
                    ]
                }
                
                if 'AliasTarget' in record:
                    change_batch['Changes'][0]['ResourceRecordSet']['AliasTarget'] = record['AliasTarget']
                else:
                    change_batch['Changes'][0]['ResourceRecordSet']['ResourceRecords'] = [
                        {'Value': rr} for rr in record['ResourceRecords']
                    ]
                
                response = route53_client.change_resource_record_sets(
                    HostedZoneId=hosted_zone_id,
                    ChangeBatch=change_batch
                )
                
                print(f"✅ DNS record created: {record['Name']} ({record['Type']})")
                created_records += 1
                
            except Exception as e:
                print(f"❌ Error creating DNS record {record['Name']}: {e}")
                continue
        
        print(f"✅ Created {created_records} DNS records")
        return True
        
    except Exception as e:
        print(f"❌ Error creating DNS records: {e}")
        return False

def request_ssl_certificate():
    """SSL証明書をリクエスト"""
    acm_client = boto3.client('acm', region_name='us-east-1')  # ACMはus-east-1
    
    try:
        with open('acm-config.json', 'r') as f:
            config = json.load(f)
        
        certificate_config = config['certificates'][0]
        
        response = acm_client.request_certificate(
            DomainName=certificate_config['DomainName'],
            SubjectAlternativeNames=certificate_config['SubjectAlternativeNames'],
            ValidationMethod=certificate_config['ValidationMethod'],
            Tags=certificate_config['Tags']
        )
        
        certificate_arn = response['CertificateArn']
        print(f"✅ SSL certificate requested: {certificate_arn}")
        print(f"   Domain: {certificate_config['DomainName']}")
        print(f"   SANs: {', '.join(certificate_config['SubjectAlternativeNames'])}")
        
        return certificate_arn
        
    except Exception as e:
        print(f"❌ Error requesting SSL certificate: {e}")
        return None

def validate_certificate(certificate_arn):
    """証明書の検証"""
    acm_client = boto3.client('acm', region_name='us-east-1')
    
    try:
        response = acm_client.describe_certificate(CertificateArn=certificate_arn)
        certificate = response['Certificate']
        
        print(f"📋 Certificate Status: {certificate['Status']}")
        
        if certificate['Status'] == 'PENDING_VALIDATION':
            print("⏳ Certificate is pending validation...")
            print("   Please add the DNS validation records to your domain")
            
            for validation in certificate['DomainValidationOptions']:
                if 'ResourceRecord' in validation:
                    record = validation['ResourceRecord']
                    print(f"   Add CNAME record: {record['Name']} -> {record['Value']}")
        
        elif certificate['Status'] == 'ISSUED':
            print("✅ Certificate is issued and ready to use")
            return True
        else:
            print(f"⚠️ Certificate status: {certificate['Status']}")
            return False
        
        return False
        
    except Exception as e:
        print(f"❌ Error validating certificate: {e}")
        return False

def update_alb_listener(certificate_arn):
    """ALBリスナーを更新してHTTPSを有効化"""
    elbv2_client = boto3.client('elbv2', region_name='ap-northeast-1')
    
    try:
        # ALBを取得
        response = elbv2_client.describe_load_balancers(
            Names=['vendor0913-alb']
        )
        
        if not response['LoadBalancers']:
            print("❌ ALB not found")
            return False
        
        alb_arn = response['LoadBalancers'][0]['LoadBalancerArn']
        
        # 既存のHTTPSリスナーを確認
        listeners = elbv2_client.describe_listeners(LoadBalancerArn=alb_arn)
        https_listener = None
        
        for listener in listeners['Listeners']:
            if listener['Port'] == 443:
                https_listener = listener
                break
        
        if https_listener:
            # 既存のHTTPSリスナーを更新
            response = elbv2_client.modify_listener(
                ListenerArn=https_listener['ListenerArn'],
                Certificates=[{'CertificateArn': certificate_arn}]
            )
            print("✅ Updated existing HTTPS listener")
        else:
            # 新しいHTTPSリスナーを作成
            response = elbv2_client.create_listener(
                LoadBalancerArn=alb_arn,
                Protocol='HTTPS',
                Port=443,
                Certificates=[{'CertificateArn': certificate_arn}],
                DefaultActions=[
                    {
                        'Type': 'forward',
                        'TargetGroupArn': 'arn:aws:elasticloadbalancing:ap-northeast-1:067717894185:targetgroup/vendor0913-api-tg-http/1234567890123456'
                    }
                ]
            )
            print("✅ Created new HTTPS listener")
        
        # HTTPからHTTPSへのリダイレクトを設定
        http_listeners = [l for l in listeners['Listeners'] if l['Port'] == 80]
        if http_listeners:
            response = elbv2_client.modify_listener(
                ListenerArn=http_listeners[0]['ListenerArn'],
                DefaultActions=[
                    {
                        'Type': 'redirect',
                        'RedirectConfig': {
                            'Protocol': 'HTTPS',
                            'Port': '443',
                            'StatusCode': 'HTTP_301'
                        }
                    }
                ]
            )
            print("✅ Configured HTTP to HTTPS redirect")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating ALB listener: {e}")
        return False

def test_domain_resolution(domain_name):
    """ドメインの解決をテスト"""
    print(f"🔍 Testing domain resolution: {domain_name}")
    
    try:
        result = dns.resolver.resolve(domain_name, 'A')
        ip_addresses = [str(ip) for ip in result]
        print(f"✅ Domain resolves to: {', '.join(ip_addresses)}")
        return True
    except Exception as e:
        print(f"❌ Domain resolution failed: {e}")
        return False

def list_domain_resources():
    """ドメイン関連リソースを一覧表示"""
    route53_client = boto3.client('route53', region_name='us-east-1')
    acm_client = boto3.client('acm', region_name='us-east-1')
    
    try:
        # ホストゾーン
        hosted_zones = route53_client.list_hosted_zones()
        print("\n📋 Route53 Hosted Zones:")
        for zone in hosted_zones['HostedZones']:
            if 'vendor0913' in zone['Name']:
                print(f"   - {zone['Name']} (ID: {zone['Id']})")
        
        # 証明書
        certificates = acm_client.list_certificates()
        print("\n📋 ACM Certificates:")
        for cert in certificates['CertificateSummaryList']:
            if 'vendor0913' in cert['DomainName']:
                print(f"   - {cert['DomainName']} (Status: {cert['Status']})")
                print(f"     ARN: {cert['CertificateArn']}")
        
    except Exception as e:
        print(f"❌ Error listing domain resources: {e}")

def main():
    """メイン実行関数"""
    print("🌐 Setting up domain and SSL for vendor0913...")
    print("=" * 60)
    
    # 1. ホストゾーンを作成
    print("\n1. Creating Route53 Hosted Zone...")
    hosted_zone_id, name_servers = create_hosted_zone()
    
    if not hosted_zone_id:
        print("❌ Failed to create hosted zone. Exiting.")
        return
    
    print(f"\n📝 Important: Update your domain registrar with these name servers:")
    for ns in name_servers:
        print(f"   {ns}")
    
    # 2. DNSレコードを作成
    print("\n2. Creating DNS Records...")
    if not create_dns_records(hosted_zone_id):
        print("⚠️ Failed to create some DNS records, but continuing...")
    
    # 3. SSL証明書をリクエスト
    print("\n3. Requesting SSL Certificate...")
    certificate_arn = request_ssl_certificate()
    
    if not certificate_arn:
        print("❌ Failed to request SSL certificate. Exiting.")
        return
    
    # 4. 証明書の検証
    print("\n4. Validating Certificate...")
    if not validate_certificate(certificate_arn):
        print("⚠️ Certificate validation pending. Please add DNS records.")
    
    # 5. ALBリスナーを更新
    print("\n5. Updating ALB Listener...")
    if not update_alb_listener(certificate_arn):
        print("⚠️ Failed to update ALB listener, but continuing...")
    
    # 6. ドメイン解決をテスト
    print("\n6. Testing Domain Resolution...")
    test_domain_resolution("vendor0913.com")
    test_domain_resolution("api.vendor0913.com")
    
    # 7. リソースを一覧表示
    print("\n7. Listing Domain Resources...")
    list_domain_resources()
    
    print("\n✅ Domain setup completed!")
    print("\n📝 Next steps:")
    print("   1. Update domain registrar with name servers")
    print("   2. Wait for DNS propagation (up to 48 hours)")
    print("   3. Complete SSL certificate validation")
    print("   4. Test HTTPS access to your application")

if __name__ == "__main__":
    main()
