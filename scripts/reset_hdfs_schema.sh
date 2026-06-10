#!/bin/bash
set -euo pipefail

ROOT="/resume_matching"
TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
BACKUP="$ROOT/backups/schema_v1_$TIMESTAMP"

echo "备份旧 HDFS 数据到 $BACKUP"
hdfs dfs -mkdir -p "$BACKUP"

for path in raw processed output checkpoints; do
    if hdfs dfs -test -e "$ROOT/$path"; then
        hdfs dfs -cp "$ROOT/$path" "$BACKUP/$path"
    fi
done

echo "清理旧 Schema 数据与 checkpoint"
for path in raw processed output checkpoints; do
    if hdfs dfs -test -e "$ROOT/$path"; then
        hdfs dfs -rm -r -skipTrash "$ROOT/$path"
    fi
done

echo "重建目录"
hdfs dfs -mkdir -p "$ROOT/raw/resumes"
hdfs dfs -mkdir -p "$ROOT/raw/jobs"
hdfs dfs -mkdir -p "$ROOT/processed/resumes"
hdfs dfs -mkdir -p "$ROOT/processed/jobs"
hdfs dfs -mkdir -p "$ROOT/output/matches"
hdfs dfs -mkdir -p "$ROOT/checkpoints/streaming_resumes"
hdfs dfs -mkdir -p "$ROOT/checkpoints/streaming_jobs"
hdfs dfs -mkdir -p "$ROOT/resources"
hdfs dfs -mkdir -p "$ROOT/models/tfidf"
hdfs dfs -mkdir -p "$ROOT/models/word2vec"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
hdfs dfs -put -f "$PROJECT_DIR/streaming/stopwords.json" "$ROOT/resources/stopwords.json"
hdfs dfs -put -f "$PROJECT_DIR/streaming/skill_alias.json" "$ROOT/resources/skill_alias.json"

echo "完成。备份位置：$BACKUP"
hdfs dfs -ls -R "$ROOT"
