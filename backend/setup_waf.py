#!/usr/bin/env python3
"""
WAF設定スクリプト
AWSコンソールで実行するためのスクリプト
"""

import boto3
import json
import time

def create_waf_ipset():
    """WAF IPセットを作成"""
    wafv2_client = boto3.client('wafv2', region_name='ap-northeast-1')
    
    try:
        with open('waf-ipset-config.json', 'r') as f:
            ipset_config = json.load(f)
        
        response = wafv2_client.create_ip_set(
            Name=ipset_config['Name'],
            Scope=ipset_config['Scope'],
            Description=ipset_config['Description'],
            IPAddressVersion=ipset_config['IPAddressVersion'],
            Addresses=ipset_config['Addresses'],
            Tags=ipset_config['Tags']
        )
        
        print(f"✅ WAF IP Set created: {ipset_config['Name']}")
        print(f"   ARN: {response['Summary']['ARN']}")
        return response['Summary']['ARN']
        
    except Exception as e:
        print(f"❌ Error creating WAF IP Set: {e}")
        return None

def create_waf_web_acl(ipset_arn):
    """WAF Web ACLを作成"""
    wafv2_client = boto3.client('wafv2', region_name='ap-northeast-1')
    
    try:
        with open('waf-config.json', 'r') as f:
            waf_config = json.load(f)
        
        # IPセットのARNを更新
        for rule in waf_config['Rules']:
            if rule['Name'] == 'IPWhitelistRule':
                rule['Statement']['IPSetReferenceStatement']['ARN'] = ipset_arn
                break
        
        response = wafv2_client.create_web_acl(
            Name=waf_config['Name'],
            Scope=waf_config['Scope'],
            DefaultAction=waf_config['DefaultAction'],
            Description=waf_config['Description'],
            Rules=waf_config['Rules'],
            VisibilityConfig=waf_config['VisibilityConfig'],
            Tags=waf_config['Tags']
        )
        
        print(f"✅ WAF Web ACL created: {waf_config['Name']}")
        print(f"   ARN: {response['Summary']['ARN']}")
        return response['Summary']['ARN']
        
    except Exception as e:
        print(f"❌ Error creating WAF Web ACL: {e}")
        return None

def main():
    """メイン実行関数"""
    print("��️ Setting up WAF for vendor0913 project...")
    print("=" * 60)
    
    # ALB ARN（実際の値に置き換え）
    alb_arn = "arn:aws:elasticloadbalancing:ap-northeast-1:067717894185:loadbalancer/app/vendor0913-alb/1829210726"
    
    # 1. WAF IPセットを作成
    print("\n1. Creating WAF IP Set...")
    ipset_arn = create_waf_ipset()
    
    if not ipset_arn:
        print("❌ Failed to create IP Set. Exiting.")
        return
    
    # 2. WAF Web ACLを作成
    print("\n2. Creating WAF Web ACL...")
    web_acl_arn = create_waf_web_acl(ipset_arn)
    
    if not web_acl_arn:
        print("❌ Failed to create Web ACL. Exiting.")
        return
    
    print("\n✅ WAF setup completed!")
    print("\n📝 Next steps:")
    print("   1. Verify WAF rules are working correctly")
    print("   2. Monitor WAF metrics in CloudWatch")
    print("   3. Test API endpoints with WAF protection")

if __name__ == "__main__":
    main()
