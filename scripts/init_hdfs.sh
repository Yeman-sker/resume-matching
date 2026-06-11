#!/bin/bash
# HDFS 目录初始化脚本

echo "初始化 HDFS 目录结构..."

# 创建原始数据目录
hdfs dfs -mkdir -p /resume_matching/raw/resumes
hdfs dfs -mkdir -p /resume_matching/raw/jobs

# 创建清洗后数据目录
hdfs dfs -mkdir -p /resume_matching/processed/resumes
hdfs dfs -mkdir -p /resume_matching/processed/jobs

# 创建模型目录
hdfs dfs -mkdir -p /resume_matching/models/count_vectorizer
hdfs dfs -mkdir -p /resume_matching/models/tfidf
hdfs dfs -mkdir -p /resume_matching/models/word2vec

# 创建输出目录
hdfs dfs -mkdir -p /resume_matching/output/matches

# 创建 checkpoint 目录
hdfs dfs -mkdir -p /resume_matching/checkpoints/streaming_resumes
hdfs dfs -mkdir -p /resume_matching/checkpoints/streaming_jobs

# 创建资源目录
hdfs dfs -mkdir -p /resume_matching/resources

echo "HDFS 目录结构创建完成！"
echo ""
echo "目录列表："
hdfs dfs -ls -R /resume_matching
