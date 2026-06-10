# 上游数据生成服务

## 功能

- 持续调用 OpenAI 兼容 API 生成简历和岗位数据
- 故意注入 15% 脏数据（缺失值、格式不统一、HTML标签等）
- 内存缓冲 + 定时批量写入 HDFS
- FastAPI 提供启停控制接口

## 安装

```bash
cd data_generator
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 配置

1. 复制环境变量模板：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入你的 API Key：
```bash
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_API_KEY=sk-your-api-key-here
```

## 运行

```bash
# 方式1：直接运行
python3 data_generator.py

# 方式2：使用启动脚本
bash start.sh
```

## API 接口

### 1. 启动生成器
```bash
curl -X POST http://localhost:8000/control \
  -H "Content-Type: application/json" \
  -d '{"action": "start"}'
```

### 2. 停止生成器
```bash
curl -X POST http://localhost:8000/control \
  -H "Content-Type: application/json" \
  -d '{"action": "stop"}'
```

### 3. 查看状态
```bash
curl http://localhost:8000/status
```

响应示例：
```json
{
  "is_generating": true,
  "stats": {
    "resumes": 120,
    "jobs": 120,
    "last_flush": "2026-06-10T10:30:00"
  },
  "buffer_size": {
    "resumes": 15,
    "jobs": 15
  }
}
```

## 数据输出

- **简历数据**：`hdfs://localhost:9000/resume_matching/raw/resumes/YYYY-MM-DD_HH-MM.csv`
- **岗位数据**：`hdfs://localhost:9000/resume_matching/raw/jobs/YYYY-MM-DD_HH-MM.csv`

## 脏数据类型

| 字段 | 脏数据类型 | 概率 |
|------|-----------|------|
| resume_id/job_id | 空值或重复ID | 5% |
| gender | 格式错误（m/f/Male） | 10% |
| age | 中文数字（二十五） | 5% |
| education | 英文（Bachelor/Master） | 10% |
| skills | 包含HTML标签 | 15% |
| experience_years | 文本描述（三年经验） | 5% |
| city | 英文或缩写（Beijing/BJ） | 10% |
| salary_range | 格式混乱（15k~20k） | 10% |

## 生成策略

- **批量大小**：每轮并发生成 20 条数据（10简历 + 10岗位）
- **刷新间隔**：每 60 秒将缓冲区写入 HDFS
- **速率控制**：取决于 OpenAI API 响应速度，约 1-2 条/秒
