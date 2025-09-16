import boto3
import os
from dotenv import load_dotenv
from typing import Dict, Any, List

# 環境変数を読み込み
load_dotenv('.env.aurora')

# Aurora Data API設定
AURORA_CLUSTER_ARN = os.getenv('AURORA_CLUSTER_ARN')
AURORA_SECRET_ARN = os.getenv('AURORA_SECRET_ARN')
AURORA_DATABASE = os.getenv('AURORA_DATABASE')
AWS_REGION = os.getenv('AWS_REGION')

# RDS Data APIクライアント
rds_data = boto3.client('rds-data', region_name=AWS_REGION)

def execute_sql(sql: str, parameters: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """SQLを実行して結果を返す"""
    try:
        response = rds_data.execute_statement(
            resourceArn=AURORA_CLUSTER_ARN,
            secretArn=AURORA_SECRET_ARN,
            database=AURORA_DATABASE,
            sql=sql,
            parameters=parameters or []
        )
        return response
    except Exception as e:
        print(f'SQL実行エラー: {e}')
        raise e

def get_db():
    """データベース接続の依存関数（FastAPI用）"""
    # Data APIは接続プールが不要なので、単純にyield
    yield rds_data
