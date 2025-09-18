#!/bin/bash
set -e

# 変数定義
TASK_DEF_NAME="vendor0918-task"
CLUSTER_NAME="vendor0918-cluster"
SERVICE_NAME="vendor0918-service"
REGION="ap-northeast-1"

echo "📥 現在のタスク定義を取得中..."
aws ecs describe-task-definition \
  --task-definition ${TASK_DEF_NAME} \
  --region ${REGION} \
  --query taskDefinition \
  > td-current.json

echo "🛠 jqでhealthCheckを追加..."
jq '.containerDefinitions[0].healthCheck = {
  command: ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
  interval: 30,
  timeout: 5,
  retries: 3,
  startPeriod: 60
}' td-current.json > td-updated.json

echo "📤 新しいタスク定義を登録..."
NEW_TASK_DEF=$(aws ecs register-task-definition \
  --cli-input-json file://td-updated.json \
  --region ${REGION} \
  --query "taskDefinition.taskDefinitionArn" \
  --output text)

echo "✅ 新しいタスク定義: $NEW_TASK_DEF"

echo "🔄 サービスを更新..."
aws ecs update-service \
  --cluster ${CLUSTER_NAME} \
  --service ${SERVICE_NAME} \
  --task-definition ${NEW_TASK_DEF} \
  --region ${REGION} \
  --force-new-deployment

echo "🎉 完了！新しいタスク定義にhealthCheckを追加してデプロイしました。"

