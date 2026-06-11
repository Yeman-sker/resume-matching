# 上游数据生成服务

## 功能

- 持续调用 OpenAI 兼容 API 生成简历和岗位数据
- 故意注入脏数据（缺失值、重复 ID、格式不统一、HTML 标签等）
- 内存缓冲 + 定时批量写入 HDFS
- FastAPI 提供启停控制接口

## 安装

```bash
bash scripts/setup_python_env.sh
```

## 配置

创建 `.env` 文件（项目根目录或 data_generator 目录）：
```bash
OPENAI_API_BASE=https://api.deepseek.com/v1
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=deepseek-chat
BATCH_SIZE=20
GENERATION_INTERVAL=10
FLUSH_INTERVAL=60
```

## 运行

```bash
# 方式1：直接运行
.venv/bin/python data_generator/data_generator.py

# 方式2：使用启动脚本
bash data_generator/start.sh
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

- **简历数据**：`hdfs://localhost:9000/resume_matching/raw/resumes/*.csv`
- **岗位数据**：`hdfs://localhost:9000/resume_matching/raw/jobs/*.csv`
- **文件命名**：`YYYY-MM-DD_HH-MM-SS_<random>.csv`

## 脏数据类型

| 字段 | 脏数据类型 | 概率 |
|------|-----------|------|
| resume_id/job_id | 空值或重复ID | 3-10% |
| age | 异常值（-3/88） | 少量 |
| education | 写法不统一（本科/本科学历/本科及以上） | 少量 |
| skills | 别名不统一（py/python/PYTHON/Apache Spark） | 少量 |
| years_experience | 文本描述（一年/3年以上） | 少量 |
| location | 写法不统一（南昌/南昌市/江西南昌） | 少量 |
| expected_salary | 异常值（0/999） | 少量 |
| work_history/job_description | HTML 标签、多余空格、特殊符号 | 少量 |

## 生成策略

- **批量大小**：每轮并发生成 20 条数据（10 简历 + 10 岗位）
- **生成间隔**：默认 10 秒
- **刷新间隔**：每 60 秒将缓冲区写入 HDFS
- **最大并发**：4 个请求
- **失败重试**：超时、429、5xx 最多重试 2 次
- **温度参数**：0.9（保证数据多样性）
