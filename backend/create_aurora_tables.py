import os
import boto3
from typing import Dict, Any, List

# Aurora Data API設定（直接設定）
AURORA_CLUSTER_ARN = "arn:aws:rds:ap-northeast-1:067717894185:cluster:vendor0913-serverless-cluster-2"
AURORA_SECRET_ARN = "arn:aws:secretsmanager:ap-northeast-1:067717894185:secret:rds!cluster-a1426c81-0e2b-4111-b91f-95079d238f81-S01tGG"
AURORA_DATABASE = "vendor_analysis"
AWS_REGION = "ap-northeast-1"

# RDS Data APIクライアント
rds_data = boto3.client('rds-data', region_name=AWS_REGION)

def execute_sql(sql: str, parameters: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Execute SQL and return results"""
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
        print(f'SQL execution error: {e}')
        raise e

def create_tables():
    """Create tables for Aurora Data API"""
    
    # usersテーブルの作成
    users_table_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        name VARCHAR(255) NOT NULL,
        hashed_password VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # vendorsテーブルの作成
    vendors_table_sql = """
    CREATE TABLE IF NOT EXISTS vendors (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        category VARCHAR(255) NOT NULL,
        description TEXT,
        website_url VARCHAR(500),
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # documentsテーブルの作成（RAG用）
    documents_table_sql = """
    CREATE TABLE IF NOT EXISTS documents (
        id SERIAL PRIMARY KEY,
        content TEXT NOT NULL,
        embedding vector(1536),
        metadata JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    try:
        print("Starting table creation...")
        
        # Create users table
        print("Creating users table...")
        execute_sql(users_table_sql)
        print("✅ users table created successfully")
        
        # Create vendors table
        print("Creating vendors table...")
        execute_sql(vendors_table_sql)
        print("✅ vendors table created successfully")
        
        # Create documents table
        print("Creating documents table...")
        execute_sql(documents_table_sql)
        print("✅ documents table created successfully")
        
        print("\n🎉 All tables created successfully!")
        
    except Exception as e:
        print(f"❌ Table creation error: {e}")
        raise e

def create_indexes():
    """Create indexes"""
    
    # Vector search index
    vector_index_sql = """
    CREATE INDEX IF NOT EXISTS documents_embedding_idx 
    ON documents USING ivfflat (embedding vector_cosine_ops);
    """
    
    try:
        print("Starting index creation...")
        execute_sql(vector_index_sql)
        print("✅ Vector search index created successfully")
        
    except Exception as e:
        print(f"❌ Index creation error: {e}")
        raise e

if __name__ == "__main__":
    create_tables()
    create_indexes()
