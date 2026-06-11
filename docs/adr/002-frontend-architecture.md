# ADR-002: 前端架构设计

## 状态

已批准（Accepted）

## 背景

参考项目（Streamlit 版本，端口 8500）提供了以下功能页面：

1. **项目概览** — 展示简历数、岗位数、匹配数、最高分、平均分等统计指标，以及各维度分数的柱状图
2. **岗位匹配求职者** — 下拉选择岗位 → 展示 Top-N 匹配候选人卡片（综合分、语义分、技能分、经验分、学历分、城市分；共同技能、缺失技能；推荐理由）
3. **简历推荐岗位** — 下拉选择简历 → 展示 Top-N 推荐岗位卡片（同上评分维度）
4. **数据预览** — 简历、岗位、匹配结果三张原始数据表格

当前 React 前端仅实现了系统监控面板（WebSocket 实时推送），缺少业务功能页面。后端仅提供 WebSocket `/ws` 推送系统状态，尚未实现业务数据 API。

### 约束

- 前端技术栈已确定：React 19 + shadcn/ui + Tailwind CSS + Zustand + axios + Vite
- 后端技术栈已确定：FastAPI + WebSocket（端口 8002）
- 数据源为 HDFS CSV 文件，后端需通过 `hdfs dfs` 命令行或 PySpark 读取
- 前端开发服务器端口 5173，后端 CORS 已配置允许 5173 和 5174

## 决策

采用**单页应用（SPA）+ 多页面路由**架构，按功能模块拆分为独立页面组件。

### 2.1 页面路由设计

```
/                    → Dashboard（系统监控面板）
/jobs                → JobMatchPage（岗位匹配查询）
/resumes             → ResumeRecommendPage（简历推荐查询）
/match/:resumeId/:jobId → MatchDetailPage（匹配详情）
/generator           → GeneratorControlPage（数据生成器控制）
```

### 2.2 目录结构

```
frontend/src/
├── App.tsx                    # 路由配置 + 导航栏
├── main.tsx                   # 入口
├── index.css                  # 全局样式
├── types/
│   └── index.ts               # 类型定义（已有，需扩展）
├── store/
│   └── index.ts               # Zustand store（已有，需扩展）
├── lib/
│   └── utils.ts               # 工具函数
│   └── api.ts                 # axios 请求封装（新增）
├── hooks/
│   └── useWebSocket.ts        # WebSocket hook（新增，从 store 中抽取）
├── pages/
│   ├── Dashboard.tsx          # 系统监控面板（已有，需增强）
│   ├── JobMatchPage.tsx        # 岗位匹配查询（新增）
│   ├── ResumeRecommendPage.tsx # 简历推荐查询（新增）
│   ├── MatchDetailPage.tsx    # 匹配详情（新增）
│   └── GeneratorControlPage.tsx # 数据生成器控制（新增）
├── components/
│   ├── ui/                    # shadcn/ui 组件（已有）
│   ├── layout/
│   │   └── Navbar.tsx         # 顶部导航栏（新增）
│   ├── dashboard/
│   │   ├── SystemStatusCard.tsx  # 系统状态卡片
│   │   ├── MetricsChart.tsx      # 指标图表（新增）
│   │   └── DataStatsCards.tsx     # 数据统计卡片（新增）
│   ├── match/
│   │   ├── ScoreBar.tsx         # 分数进度条（新增）
│   │   ├── MatchCard.tsx         # 匹配结果卡片（新增）
│   │   ├── SkillTags.tsx         # 技能标签（新增）
│   │   └── ScoreBreakdown.tsx    # 分数详情面板（新增）
│   └── common/
│       ├── LoadingSpinner.tsx   # 加载指示器（新增）
│       ├── ErrorBoundary.tsx     # 错误边界（新增）
│       └── EmptyState.tsx        # 空状态提示（新增）
```

### 2.3 数据层设计

#### Zustand Store 扩展

```typescript
// store/index.ts 扩展后的结构
interface SystemStore {
  // 已有：系统状态
  status: SystemStatus | null
  connectWS: () => void
  disconnectWS: () => void

  // 新增：业务数据
  jobs: Job[]
  resumes: Resume[]
  matches: Match[]
  loading: boolean
  error: string | null

  // 新增：操作方法
  fetchJobs: () => Promise<void>
  fetchResumes: () => Promise<void>
  fetchJobMatches: (jobId: string, limit?: number) => Promise<Match[]>
  fetchResumeRecommendations: (resumeId: string, limit?: number) => Promise<Match[]>
  fetchMatchDetail: (resumeId: string, jobId: string) => Promise<MatchDetail>
}
```

#### API 封装

```typescript
// lib/api.ts
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8002',
  timeout: 30000,
})

export default api
```

### 2.4 导航栏设计

```
┌──────────────────────────────────────────────────────────┐
│ [Logo] 简历-岗位匹配系统                                     │
│                                                           │
│ [系统监控] [岗位匹配] [简历推荐] [生成器控制]                  │
└──────────────────────────────────────────────────────────┘
```

使用 React Router 的 `<NavLink>` 组件实现，高亮当前页面。

### 2.5 依赖新增

```json
{
  "dependencies": {
    "react-router-dom": "^7.x",
    "recharts": "^2.x"
  }
}
```

- `react-router-dom`：SPA 路由
- `recharts`：图表展示（分数分布柱状图、雷达图等）

## 影响

### 优点

1. **模块化清晰**：每个功能模块独立页面，易于维护和并行开发
2. **逐步增强**：可在现有 Dashboard 基础上逐步添加新页面
3. **类型安全**：TypeScript 类型定义已建立，扩展方便
4. **状态集中管理**：Zustand store 统一管理业务数据和系统状态

### 缺点

1. **需要后端配合**：后端需要新增 REST API 接口
2. **HDFS 读取延迟**：大数据量下 API 响应可能较慢，需要分页/缓存策略

### 风险缓解

- API 层添加请求缓存和 loading 状态
- 大数据表格采用虚拟滚动或分页
- WebSocket 断线自动重连（已实现）

## 实施计划

### 阶段 1：基础架构搭建

1. 安装 `react-router-dom` 和 `recharts`
2. 重构 `App.tsx` 添加路由和导航栏
3. 创建 `lib/api.ts` 封装 axios
4. 扩展 Zustand store 和类型定义

### 阶段 2：业务页面开发

5. 实现岗位匹配查询页面
6. 实现简历推荐查询页面
7. 实现匹配详情页面
8. 实现数据生成器控制页面

### 阶段 3：增强和优化

9. Dashboard 添加统计数据和图表
10. 添加 ErrorBoundary 和加载状态
11. 响应式布局优化

---

**日期**: 2026-06-11
**作者**: 项目组