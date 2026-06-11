# ADR-009: 实施优先级与开发顺序

## 状态

已批准（Accepted）

## 背景

基于 ADR-002 至 ADR-008 的架构决策，需要确定前端页面的实施优先级和开发顺序。

### 当前完成状态

| 模块 | 后端 API | 前端页面 | 状态 |
|------|---------|---------|------|
| 系统监控 | WebSocket `/ws`（已实现） | Dashboard 基础版（已实现） | 基础完成 |
| 数据统计 | 无 | 无 | 未开始 |
| 岗位匹配查询 | 无 | 无 | 未开始 |
| 简历推荐查询 | 无 | 无 | 未开始 |
| 匹配详情 | 无 | 无 | 未开始 |
| 数据生成器控制 | 无 | 无 | 未开始 |

### 依赖关系

```
后端 API 开发
  ├── GET /api/stats          → Dashboard 增强
  ├── GET /api/jobs           → 岗位匹配查询
  ├── GET /api/jobs/{id}/matches → 岗位匹配查询
  ├── GET /api/resumes        → 简历推荐查询
  ├── GET /api/resumes/{id}/recommendations → 简历推荐查询
  ├── GET /api/matches/{rid}/{jid} → 匹配详情
  └── POST /api/generator/*  → 数据生成器控制

前端开发依赖后端 API 完成
```

## 决策

### 9.1 开发顺序（按优先级排列）

#### 阶段 1：后端 API 基础建设（优先级：P0）

1. **创建 `web_backend/services/hdfs_reader.py`** — HDFS CSV 读取 + 缓存
2. **创建 `web_backend/services/cache.py`** — 统一缓存管理
3. **创建 `web_backend/api/` 目录结构** — 路由模块拆分
4. **实现 `GET /api/stats`** — 统计数据接口
5. **实现 `GET /api/jobs`** — 岗位列表接口
6. **实现 `GET /api/resumes`** — 简历列表接口
7. **实现 `GET /api/jobs/{job_id}/matches`** — 岗位匹配接口
8. **实现 `GET /api/resumes/{resume_id}/recommendations`** — 简历推荐接口
9. **实现 `GET /api/matches/{resume_id}/{job_id}`** — 匹配详情接口
10. **实现 `POST /api/generator/start` 和 `POST /api/generator/stop`** — 生成器代理
11. **实现 `GET /api/generator/status`** — 生成器状态查询

#### 阶段 2：前端基础架构（优先级：P0）

12. **安装依赖** — `react-router-dom`、`recharts`
13. **重构 `App.tsx`** — 添加路由和导航栏
14. **创建 `lib/api.ts`** — axios 封装
15. **扩展 `types/index.ts`** — 添加 Job、Resume、Match 等类型
16. **扩展 `store/index.ts`** — 添加业务数据状态和方法

#### 阶段 3：业务页面开发（优先级：P1）

17. **Dashboard 增强** — 添加统计指标、分数分布图、快捷入口
18. **岗位匹配查询页面** — 左右分栏布局
19. **简历推荐查询页面** — 左右分栏布局
20. **匹配详情页面** — 独立详情页

#### 阶段 4：辅助页面（优先级：P2）

21. **数据生成器控制页面** — 启停控制和配置
22. **数据预览页面** — 原始 CSV 数据表格预览（参考 Streamlit 的数据预览 Tab）

### 9.2 关键路径

```
[后端 API] → [前端路由] → [岗位匹配页面] → [匹配详情页面]
                                      ↓
                              [简历推荐页面]
```

最短可演示路径：后端 API → 前端路由 → 岗位匹配页面

### 9.3 开发工作量估算

| 任务 | 预估工时 | 依赖 |
|------|---------|------|
| 后端 API 基础建设 | 4 小时 | 无 |
| 前端路由和导航 | 1 小时 | 无 |
| Dashboard 增强 | 2 小时 | 后端 /api/stats |
| 岗位匹配页面 | 4 小时 | 后端 /api/jobs, /api/jobs/{id}/matches |
| 简历推荐页面 | 3 小时 | 后端 /api/resumes, /api/resumes/{id}/recommendations |
| 匹配详情页面 | 3 小时 | 后端 /api/matches/{rid}/{jid} |
| 数据生成器控制 | 2 小时 | 后端 /api/generator/* |
| 共享组件（ScoreBar、MatchCard 等） | 2 小时 | 无 |
| 样式优化和响应式 | 2 小时 | 所有页面 |
| **总计** | **约 23 小时** | |

### 9.4 验收标准

#### 后端 API 验收

- [ ] 所有 8 个 API 接口返回正确的 JSON 格式数据
- [ ] HDFS 数据读取有 60 秒缓存
- [ ] 分页功能正常（`/api/jobs?page=1&page_size=10`）
- [ ] 生成器代理转发正确

#### 前端页面验收

- [ ] 导航栏显示 4 个页面入口，点击可跳转
- [ ] Dashboard 显示 5 个统计指标 + 分数分布图 + 系统状态
- [ ] 岗位匹配页面：点击左侧岗位 → 右侧显示候选人列表
- [ ] 简历推荐页面：点击左侧简历 → 右侧显示推荐岗位列表
- [ ] 匹配详情页面：显示简历/岗位对比 + 分数详情 + 技能匹配 + 推荐理由
- [ ] 数据生成器页面：可启停生成器，显示运行状态
- [ ] 所有页面有加载状态、空状态、错误状态处理

### 9.5 与 Streamlit 参考的完整功能对照

| Streamlit 功能 | React 对应页面 | ADR 编号 |
|---------------|-------------|---------|
| 项目概览（统计指标 + 柱状图） | Dashboard | ADR-004 |
| 岗位匹配求职者 | JobMatchPage | ADR-005 |
| 简历推荐岗位 | ResumeRecommendPage | ADR-006 |
| 数据预览 | Dashboard 数据统计区 / 独立页面 | ADR-004 |
| 侧边栏筛选 | 各页面内筛选 | ADR-005, ADR-006 |
| 推荐理由 | MatchCard + MatchDetailPage | ADR-005, ADR-007 |
| 共同技能/缺失技能 | SkillTags 组件 | ADR-007 |
| 分数进度条 | ScoreBar 组件 | ADR-005 |
| 系统运行状态 | Dashboard（React 独有） | ADR-004 |
| 数据生成器控制 | GeneratorControlPage（React 独有） | ADR-008 |
| 匹配详情独立页面 | MatchDetailPage（React 独有） | ADR-007 |

---

**日期**: 2026-06-11
**作者**: 项目组