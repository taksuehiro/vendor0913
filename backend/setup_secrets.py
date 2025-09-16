import boto3
import json
import os

# AWSリージョン設定
AWS_REGION = os.getenv('AWS_REGION', 'ap-northeast-1')
secrets_client = boto3.client('secretsmanager', region_name=AWS_REGION)

def create_or_update_secret(secret_name: str, secret_string: dict, description: str):
    """
    Secrets Managerにシークレットを作成または更新する
    """
    try:
        secrets_client.create_secret(
            Name=secret_name,
            Description=description,
            SecretString=json.dumps(secret_string)
        )
        print(f"✅ Secret '{secret_name}' created.")
    except secrets_client.exceptions.ResourceExistsException:
        secrets_client.update_secret(
            SecretId=secret_name,
            SecretString=json.dumps(secret_string)
        )
        print(f"🔄 Secret '{secret_name}' updated.")
    except Exception as e:
        print(f"❌ Error creating/updating secret '{secret_name}': {e}")
        raise

def setup_aurora_secrets():
    """Aurora Data APIの設定をSecrets Managerに保存"""
    aurora_secret_name = "vendor0913/aurora/config"
    aurora_secret_string = {
        "AURORA_CLUSTER_ARN": "arn:aws:rds:ap-northeast-1:067717894185:cluster:vendor0913-serverless-cluster-2",
        "AURORA_SECRET_ARN": "arn:aws:secretsmanager:ap-northeast-1:067717894185:secret:rds!cluster-a1426c81-0e2b-4111-b91f-95079d238f81-S01tGG",
        "AURORA_DATABASE": "vendor_analysis",
        "AWS_REGION": AWS_REGION
    }
    create_or_update_secret(aurora_secret_name, aurora_secret_string, "Aurora PostgreSQL Serverless v2 configuration")

def setup_openai_secrets(openai_api_key: str):
    """OpenAI APIの設定をSecrets Managerに保存"""
    openai_secret_name = "vendor0913/openai/config"
    openai_secret_string = {
        "OPENAI_API_KEY": openai_api_key,
        "OPENAI_MODEL": "text-embedding-3-small"
    }
    create_or_update_secret(openai_secret_name, openai_secret_string, "OpenAI API configuration")

def list_secrets():
    """Secrets Managerに保存されているシークレットを一覧表示"""
    print("\n--- Current Secrets in Secrets Manager ---")
    try:
        response = secrets_client.list_secrets(
            Filters=[
                {
                    'Key': 'name',
                    'Values': ['vendor0913/']
                },
            ]
        )
        for secret in response['SecretList']:
            print(f"- Name: {secret['Name']}, ARN: {secret['ARN']}")
    except Exception as e:
        print(f"❌ Error listing secrets: {e}")

if __name__ == "__main__":
    print("Starting Secrets Manager setup...")
    
    # OpenAI APIキーはユーザーが手動で入力するか、環境変数から取得
    openai_key = os.getenv('OPENAI_API_KEY', 'your_actual_openai_api_key_here') 
    
    setup_aurora_secrets()
    setup_openai_secrets(openai_key)
    list_secrets()
    print("\n�� Secrets Manager setup complete!")
