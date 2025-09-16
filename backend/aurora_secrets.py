import boto3
import os
import json
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class AuroraSecretsManager:
    def __init__(self):
        self.secrets_client = boto3.client('secretsmanager', region_name=os.getenv('AWS_REGION', 'ap-northeast-1'))
        self._load_secrets()
        self.rds_data = boto3.client('rds-data', region_name=self.aws_region)

    def _load_secrets(self):
        # Aurora Configuration
        try:
            aurora_secret_name = os.getenv('AURORA_SECRET_NAME', 'vendor0913/aurora/config')
            aurora_secret = self.secrets_client.get_secret_value(SecretId=aurora_secret_name)['SecretString']
            aurora_config = json.loads(aurora_secret)
            self.aurora_cluster_arn = aurora_config.get('AURORA_CLUSTER_ARN')
            self.aurora_secret_arn = aurora_config.get('AURORA_SECRET_ARN')
            self.aurora_database = aurora_config.get('AURORA_DATABASE')
            self.aws_region = aurora_config.get('AWS_REGION')
            logger.info("Aurora configuration loaded from Secrets Manager.")
        except Exception as e:
            logger.warning(f"Could not load Aurora config from Secrets Manager: {e}. Falling back to environment variables.")
            self.aurora_cluster_arn = os.getenv('AURORA_CLUSTER_ARN')
            self.aurora_secret_arn = os.getenv('AURORA_SECRET_ARN')
            self.aurora_database = os.getenv('AURORA_DATABASE')
            self.aws_region = os.getenv('AWS_REGION', 'ap-northeast-1')

        # OpenAI Configuration
        try:
            openai_secret_name = os.getenv('OPENAI_SECRET_NAME', 'vendor0913/openai/config')
            openai_secret = self.secrets_client.get_secret_value(SecretId=openai_secret_name)['SecretString']
            openai_config = json.loads(openai_secret)
            self.openai_api_key = openai_config.get('OPENAI_API_KEY')
            self.openai_model = openai_config.get('OPENAI_MODEL', 'text-embedding-3-small')
            logger.info("OpenAI configuration loaded from Secrets Manager.")
        except Exception as e:
            logger.warning(f"Could not load OpenAI config from Secrets Manager: {e}. Falling back to environment variables.")
            self.openai_api_key = os.getenv('OPENAI_API_KEY')
            self.openai_model = os.getenv('OPENAI_MODEL', 'text-embedding-3-small')

        if not all([self.aurora_cluster_arn, self.aurora_secret_arn, self.aurora_database, self.aws_region]):
            logger.error("Missing one or more Aurora configuration values.")
        if not self.openai_api_key:
            logger.error("Missing OpenAI API Key.")

    def execute_sql(self, sql: str, parameters: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute SQL and return results"""
        try:
            response = self.rds_data.execute_statement(
                resourceArn=self.aurora_cluster_arn,
                secretArn=self.aurora_secret_arn,
                database=self.aurora_database,
                sql=sql,
                parameters=parameters or []
            )
            return response
        except Exception as e:
            logger.error(f'SQL execution error: {e}')
            raise e

    def get_db(self):
        """Database connection dependency for FastAPI"""
        yield self.rds_data

    def get_openai_api_key(self) -> str:
        return self.openai_api_key

    def get_openai_model(self) -> str:
        return self.openai_model

aurora_secrets_manager = AuroraSecretsManager()
