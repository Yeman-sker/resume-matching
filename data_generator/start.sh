#!/bin/bash
# 上游数据生成服务启动脚本

cd "$(dirname "$0")"

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "错误：未找到 .env 文件"
    echo "请复制 .env.example 并配置 OPENAI_API_KEY"
    echo "  cp .env.example .env"
    echo "  编辑 .env 文件填入你的 API Key"
    exit 1
fi

# 检查 HDFS
if ! hdfs dfs -test -d /resume_matching/raw/resumes 2>/dev/null; then
    echo "警告：HDFS 目录不存在，请先运行 scripts/init_hdfs.sh"
fi

# 安装依赖
if [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# 启动服务
echo "启动数据生成器（端口 8000）..."
python3 data_generator.py
