# ADR-010: 前端开发全流程记录——从分析到实现

## 状态

已完成（Completed）

## 1. 项目背景

本项目是一个**简历-岗位人才匹配系统**，上游数据生成 → 中游数据处理（Spark Streaming + 批处理）→ 下游 Web 展示。

前端属于"下游展示层"，需要将匹配结果以可视化、可交互的方式呈现给用户。项目已有一个参考实现——基于 Streamlit 的原型（运行在 `localhost:8500`），我们需要将其功能迁移到 React 前端，并增加实时监控、数据生成器控制等新功能。

## 2. 思维导图：前端功能全景

```
简历-岗位匹配系统 前端
├── 系统监控面板 (Dashboard)
│   ├── 实时数据统计（WebSocket 每2秒推送）
│   │   ├── 简历总数
│   │   ├── 岗位总数
│   │   ├── 匹配总数
│   │   ├── 最高匹配分
│   │   └── 平均匹配分
│   ├── 系统运行状态
│   │   ├── 数据生成器状态（运行中/已停止）
│   │   ├── Streaming 处理状态
│   │   ├── 批处理任务状态
│   │   └── 最后更新时间
│   ├── 分数分布柱状图（recharts）
│   └── 快捷入口（跳转到业务页面）
│
├── 岗位匹配查询 (JobMatchPage)
│   ├── 左侧：岗位列表（搜索 + 部门筛选）
│   └── 右侧：匹配候选人卡片列表
│       ├── 综合分 + 排名
│       ├── 各维度分数进度条
│       ├── 共同技能 / 缺失技能
│       └── 查看详情链接
│
├── 简历推荐查询 (ResumeRecommendPage)
│   ├── 左侧：简历列表（搜索）
│   └── 右侧：推荐岗位卡片列表
│       └── （结构同岗位匹配）
│
├── 匹配详情 (MatchDetailPage)
│   ├── 简历信息 vs 岗位信息（左右对比）
│   ├── 分数详情（语义分 + 规则分，树状展开）
│   ├── 技能匹配（共同技能 / 缺失技能）
│   └── 推荐理由文本
│
└── 数据生成器控制 (GeneratorControlPage)
    ├── 运行状态（简历数、岗位数、速率）
    ├── 启动 / 停止按钮
    └── 配置参数（生成间隔）
```

## 3. 设计思路

### 3.1 分析参考项目 → 确定功能范围

**第一步不是写代码，而是先看参考项目（Streamlit）有什么功能。**

我分析了 `localhost:8500` 上运行的 Streamlit 应用，归纳出 4 个核心页面：

| Streamlit 页面 | React 对应页面 | 补充说明 |
|---------------|-------------|---------|
| 项目概览 | Dashboard | 增加实时推送和图表 |
| 岗位匹配求职者 | JobMatchPage | 改为左右分栏布局 |
| 简历推荐岗位 | ResumeRecommendPage | 与岗位匹配对称 |
| 数据预览 | Dashboard 统计区 | 不单独做页面 |

同时从 PRD 文档中识别出 Streamlit 没有的新需求：
- **数据生成器控制**——Streamlit 版没有，PRD 模块 B 要求
- **匹配详情独立页面**——Streamlit 只有卡片内的简略信息，PRD 要求独立详情页
- **系统实时状态**——Streamlit 是静态数据，React 版通过 WebSocket 实时推送

**教训**：先分析参考实现，再对照 PRD 找差距，最后确定功能范围。不要一上来就写代码。

### 3.2 分层设计 → 从骨架到血肉

设计顺序是**自底向上**：

```
类型定义 (types)
    ↓
API 封装 (lib/api.ts)
    ↓
状态管理 (store)
    ↓
共享组件 (components)
    ↓
页面组件 (pages)
    ↓
路由 + 导航 (App.tsx)
```

每一层只依赖它下面的层，这样改某一层时不会影响到其他层。

**为什么是这个顺序？**

因为 TypeScript 是强类型的，类型定义决定了 API 的接口形状，API 接口决定了 store 的方法签名，store 方法决定了组件的 props，组件决定了页面的交互逻辑。如果先写页面再补类型，会大量返工。

### 3.3 左右分栏 vs 上下布局

Streamlit 版本用的是**下拉框选择 + 上下滚动**的布局，这是 Streamlit 的局限——它只能单栏渲染。

React 前端没有任何布局限制。根据 PRD 的要求，采用**左右分栏**：
- 左侧 30%：列表（可搜索、可筛选）
- 右侧 70%：匹配详情

这种布局在桌面端体验更好：左边选、右边看，不需要反复滚动。

### 3.4 组件复用策略

岗位匹配和简历推荐两个页面的结构**几乎完全一样**，只是数据源不同。设计时抽出了共享组件：

| 共享组件 | 用途 |
|---------|------|
| `ScoreBar` | 分数进度条（颜色：<60红，60-80黄，>80绿） |
| `MatchCard` | 匹配结果卡片，通过 `mode` prop 区分 job/resume |
| `SkillTags` | 技能标签（绿色=共同，红色=缺失） |
| `LoadingSpinner` | 加载指示器 |
| `EmptyState` | 空数据提示 |

这样 JobMatchPage 和 ResumeRecommendPage 可以复用同一套 MatchCard 和 ScoreBar，代码量减少约 40%。

## 4. 技术栈介绍

### 4.1 为什么选这些技术

| 技术 | 版本 | 作用 | 选择理由 |
|------|------|------|---------|
| React | 19 | UI 框架 | PRD 指定 |
| TypeScript | 6 | 类型系统 | 大型项目必须，IDE 提示好 |
| Vite | 8 | 构建工具 | 比 webpack 快 10 倍以上 |
| Tailwind CSS | 4 | 样式 | 原子化 CSS，开发效率高 |
| shadcn/ui | 4 | UI 组件库 | 基于 Radix UI，可定制性强 |
| Zustand | 5 | 状态管理 | 比 Redux 简单，适合中等项目 |
| axios | 1.7 | HTTP 客户端 | 拦截器、超时、错误处理完善 |
| react-router-dom | 7 | 路由 | SPA 单页路由标准方案 |
| recharts | 2 | 图表 | React 生态最流行的图表库 |

### 4.2 各技术在本项目中的具体用法

```
用户浏览器
    │
    ├── React Router ─── 页面路由切换（不刷新页面）
    │     ├── / → Dashboard
    │     ├── /jobs → JobMatchPage
    │     ├── /resumes → ResumeRecommendPage
    │     ├── /match/:rid/:jid → MatchDetailPage
    │     └── /generator → GeneratorControlPage
    │
    ├── Zustand Store ─── 全局状态管理
    │     ├── SystemStatus（从 WebSocket 实时更新）
    │     ├── jobs[] / resumes[]（从 REST API 加载）
    │     └── stats（分数统计分布）
    │
    ├── axios ─── HTTP 请求
    │     ├── GET /api/jobs
    │     ├── GET /api/resumes
    │     ├── GET /api/stats
    │     └── ...（8 个接口）
    │
    ├── WebSocket ─── 实时推送
    │     └── ws://localhost:8002/ws（每2秒推送系统状态）
    │
    └── recharts ─── 图表渲染
          └── BarChart（各维度平均分柱状图）
```

### 4.3 项目目录结构及每个文件的作用

```
frontend/src/
├── App.tsx                         # 路由配置 + 页面布局
├── main.tsx                        # 入口文件（挂载 React 到 DOM）
├── index.css                       # 全局样式（Tailwind 引入）
│
├── types/
│   └── index.ts                    # TypeScript 类型定义（所有接口）
│
├── lib/
│   ├── api.ts                      # axios 实例（baseURL、超时、错误拦截）
│   └── utils.ts                    # 工具函数（shadcn 生成）
│
├── store/
│   └── index.ts                    # Zustand 全局状态（WebSocket + API 方法）
│
├── components/
│   ├── ui/                         # shadcn/ui 基础组件
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   └── table.tsx
│   ├── layout/
│   │   └── Navbar.tsx              # 顶部导航栏
│   ├── match/
│   │   ├── MatchCard.tsx           # 匹配结果卡片（复用于两个页面）
│   │   ├── ScoreBar.tsx            # 分数进度条
│   │   └── SkillTags.tsx           # 技能标签（绿/红）
│   └── common/
│       ├── LoadingSpinner.tsx      # 加载中指示器
│       └── EmptyState.tsx          # 空数据提示
│
└── pages/
    ├── Dashboard.tsx               # 系统监控面板
    ├── JobMatchPage.tsx             # 岗位匹配查询
    ├── ResumeRecommendPage.tsx      # 简历推荐查询
    ├── MatchDetailPage.tsx          # 匹配详情
    └── GeneratorControlPage.tsx     # 数据生成器控制
```

## 5. 实现过程

### 5.1 第一步：安装依赖

```bash
cd frontend
npm install react-router-dom recharts
```

- `react-router-dom`：页面路由，4 个页面需要互相跳转
- `recharts`：Dashboard 的分数分布柱状图

已有依赖（项目初始化时就装好的）：
- `axios`、`zustand`、`lucide-react`、各种 `@radix-ui/*`、`tailwindcss`

### 5.2 第二步：定义类型（types/index.ts）

这是**最关键的一步**。类型定义是整个前端的骨架：

```typescript
// 从后端 API 返回的数据结构 → 定义成 TypeScript 接口
export interface Job {
  job_id: string
  job_title: string
  department: string
  // ... 17个字段
}

export interface Match {
  resume_id: string
  job_id: string
  total_score: number
  semantic_score: number
  // ... 各维度分数
}

// API 响应也定义类型
export interface JobsResponse {
  total: number
  page: number
  page_size: number
  jobs: Job[]
}
```

**为什么先写类型？** 因为 TypeScript 编译器会在你写 store、组件、API 调用时检查类型，提前发现字段名拼错、数据结构不匹配等问题。如果后改成先写组件再补类型，会大量返工。

### 5.3 第三步：API 封装（lib/api.ts）

```typescript
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8002',  // 后端地址
  timeout: 30000,                      // 30秒超时
})

export default api
```

为什么单独一个文件？因为：
1. 所有 API 请求的 baseURL 集中管理，换环境只改一处
2. 可以统一加拦截器（错误处理、token 刷新等）
3. 组件不直接用 axios，而是通过 store 方法调用，解耦更彻底

### 5.4 第四步：状态管理（store/index.ts）

把原来只管 WebSocket 的 `useSystemStore` 扩展为 `useAppStore`，加入业务数据：

```typescript
interface AppStore {
  // 原有：WebSocket 系统状态
  status: SystemStatus | null
  connectWS: () => void
  disconnectWS: () => void

  // 新增：业务数据和方法
  jobs: Job[]
  resumes: Resume[]
  stats: Stats | null
  loading: boolean
  error: string | null
  fetchJobs: () => Promise<void>
  fetchJobMatches: (jobId: string, limit?: number) => Promise<JobMatchesResponse>
  // ... 更多方法
}
```

**设计原则**：
- 数据放 store，组件只做渲染和事件触发
- API 方法返回 Promise，组件可以 `.then()` 处理数据
- loading 和 error 状态集中管理，避免每个组件自己维护

### 5.5 第五步：路由 + 导航（App.tsx + Navbar.tsx）

```typescript
// App.tsx
<BrowserRouter>
  <Routes>
    <Route path="/" element={<Dashboard />} />
    <Route path="/jobs" element={<JobMatchPage />} />
    <Route path="/resumes" element={<ResumeRecommendPage />} />
    <Route path="/match/:resumeId/:jobId" element={<MatchDetailPage />} />
    <Route path="/generator" element={<GeneratorControlPage />} />
  </Routes>
</BrowserRouter>
```

导航栏用 `NavLink` 高亮当前页面，4 个入口对应 4 个路由。

### 5.6 第六步：逐个实现页面

**页面实现顺序**：Dashboard → JobMatchPage → ResumeRecommendPage → MatchDetailPage → GeneratorControlPage

每个页面的开发模式都一样：

```
1. 写 JSX 骨架（布局结构）
2. 引入 store 方法（用 useAppStore 拿数据和 API 方法）
3. useEffect 触发数据加载
4. 处理 loading / empty / error 三种状态
5. 样式微调（Tailwind 类名）
```

以 JobMatchPage 为例：

```typescript
export default function JobMatchPage() {
  // 1. 从 store 拿数据
  const { jobs, fetchJobs, fetchJobMatches } = useAppStore()
  const [matches, setMatches] = useState<Match[]>([])

  // 2. 页面加载时获取岗位列表
  useEffect(() => { fetchJobs() }, [fetchJobs])

  // 3. 选中岗位时获取匹配结果
  useEffect(() => {
    if (selectedJobId) {
      fetchJobMatches(selectedJobId, 50).then(res => setMatches(res.matches))
    }
  }, [selectedJobId])

  // 4. 渲染：左侧列表 + 右侧卡片
  return (
    <div className="flex gap-6">
      <div className="w-[320px]">岗位列表...</div>
      <div className="flex-1">匹配结果...</div>
    </div>
  )
}
```

### 5.7 第七步：共享组件抽取

在写第二个页面（ResumeRecommendPage）时，发现和 JobMatchPage 的匹配卡片几乎一样。于是抽取成：

- `MatchCard` — 通过 `mode="job"` 或 `mode="resume"` 控制显示简历名还是岗位名
- `ScoreBar` — 颜色逻辑统一（<60红，60-80黄，>80绿）
- `SkillTags` — 绿色标签 + 红色标签

### 5.8 第八步：构建验证

```bash
npx tsc -b    # TypeScript 类型检查
npm run build # Vite 生产构建
```

两个都通过才算完成。

## 6. 遇到的问题及解决方案

### 问题 1：ENOSPC — 文件监听器达到上限

**现象**：运行 `npm run dev` 时报错：
```
Error: ENOSPC: System limit for number of file watchers reached
```

**原因**：Vite 使用 Linux 的 inotify 机制监听文件变化。WSL2 中 VSCode Server 占用了大量 inotify 实例（默认限制只有 128 个），Vite 拿不到新的 watcher。

**解决方案**：在 `vite.config.ts` 中改用轮询模式(热更新)：

```typescript
server: {
  watch: {
    usePolling: true,  // 用轮询代替 inotify
    interval: 1000,    // 每秒检查一次
  },
}
```

同时提高系统限制（写到 `/etc/sysctl.conf` 永久生效）：
```bash
sudo sysctl fs.inotify.max_user_watches=524288
sudo sysctl fs.inotify.max_user_instances=512
```

**经验**：在 WSL2 环境开发，inotify 问题几乎是必遇的。`usePolling: true` 对中小项目性能影响可忽略，推荐直接加上。

### 问题 2：前后端端口不同导致跨域

**现象**：前端（5173）请求后端（8002）时浏览器报 CORS 错误。

**解决方案**：后端 FastAPI 已配置 CORS：
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
)
```

**经验**：开发环境必须配 CORS。生产部署时前后端同源就不需要了。

### 问题 3：WebSocket 断线重连

**现象**：WebSocket 连接不稳定，断线后页面数据停止更新。

**解决方案**：在 Zustand store 中实现自动重连：

```typescript
ws.onclose = () => {
  const reconnectTimer = window.setTimeout(() => get().connectWS(), 3000)
  set({ ws: null, reconnectTimer })
}
```

关闭后 3 秒自动重连。组件卸载时清理：

```typescript
useEffect(() => {
  connectWS()
  return () => disconnectWS()
}, [connectWS, disconnectWS])
```

### 问题 4：TypeScript 编译错误 — 未使用的变量

**现象**：`npx tsc -b` 报错：
```
error TS6133: 'loading' is declared but its value is never read
error TS6196: 'Match' is declared but never used
```

**原因**：TypeScript 默认会检查未使用的变量和导入。

**解决方案**：删掉未使用的解构和 import。这其实是好事——帮我清掉了无用代码。

### 问题 5：前后端数据格式对接

**现象**：后端返回 `matched_skills: "Python|SQL"`（管道符分隔的字符串），前端需要数组来显示标签。

**解决方案**：在前端组件中做转换：

```typescript
const matchedList = match.matched_skills
  ? match.matched_skills.split('|').filter(Boolean)
  : []
```

**经验**：后端的数据格式不一定适合前端展示，在组件层做轻量转换是合理的，不需要改后端。

### 问题 6：Vite 开发服务器在 WSL2 中不稳定

**现象**：`npm run dev` 有时能启动，有时直接崩溃（ENOSPC），有时端口被占用。

**解决方案**：
1. 先 `fuser -k 5173/tcp` 杀掉占用端口的旧进程
2. 确保 `usePolling: true` 配置生效
3. 如果还不行，用 `npm run build` + Python `http.server` 作为临时方案

```bash
npm run build
cd dist && python3 -m http.server 8080
```

注意 Python 的 `http.server` 不支持 SPA 路由，只能访问首页，子页面刷新会 404。

### 问题 7：URL 参数状态同步

**现象**：用户在岗位匹配页面选了一个岗位，刷新页面后选中状态丢失。

**解决方案**：用 `useSearchParams` 把选中状态保存在 URL 中：

```typescript
const [searchParams, setSearchParams] = useSearchParams()
const selectedJobId = searchParams.get('jobId') || ''

// 选择岗位时
const handleSelectJob = (jobId: string) => {
  setSearchParams({ jobId })
}
```

这样刷新页面不会丢失状态，还能分享链接给他人。

## 7. 与参考 Streamlit 版本的功能对照

| 功能 | Streamlit 版本 | React 版本 | 差异说明 |
|------|-------------|-----------|---------|
| 统计指标（简历数/岗位数/匹配数） | ✅ 3个 | ✅ 5个（增加最高分/平均分） | 数据来源从 CSV → REST API |
| 分数分布柱状图 | ✅ | ✅ | Streamlit 用 `st.bar_chart`，React 用 `recharts` |
| 系统运行状态 | ❌ 无 | ✅ WebSocket 实时推送 | React 独有功能 |
| 岗位匹配查询 | ✅ 下拉框选择 | ✅ 左右分栏列表选择 | 交互方式不同 |
| 简历推荐查询 | ✅ 下拉框选择 | ✅ 左右分栏列表选择 | 交互方式不同 |
| 匹配详情独立页 | ❌ 卡片内简略 | ✅ 独立页面，分数树状展开 | React 版本更详细 |
| 数据生成器控制 | ❌ 无 | ✅ 启停+配置 | React 独有功能 |
| 部门筛选 | ✅ 侧边栏全局筛选 | ✅ 列表内筛选 | 位置不同 |
| Top-N 控制 | ✅ 滑块 3-20 | ✅ 下拉框 10/20/50 | 交互方式不同 |
| 推荐理由 | ✅ 卡片内 | ✅ 卡片内 + 详情页 | React 多了详情页 |
| 数据预览表格 | ✅ `st.dataframe` | ❌ 未实现 | 可后续添加 |

## 8. 新手入门建议

### 8.1 推荐学习路径

```
第1步：理解数据流
    前端 → axios → 后端 API → HDFS CSV → 数据
    前端 ← Zustand ← WebSocket ← 后端推送

第2步：从 types/index.ts 开始读代码
    所有数据结构都在这里定义，是理解整个项目的钥匙

第3步：读 store/index.ts
    看数据怎么获取、怎么存储、怎么更新

第4步：读一个简单页面（Dashboard.tsx）
    理解页面 → store → API 的调用链

第5步：读一个复杂页面（JobMatchPage.tsx）
    理解搜索、筛选、分页、条件加载等交互逻辑

第6步：读共享组件（MatchCard.tsx, ScoreBar.tsx）
    理解组件复用和 props 设计

第7步：试着加一个小功能
    比如：在 Dashboard 添加一个"最近10条匹配记录"卡片
```

### 8.2 常用开发命令

```bash
cd frontend

# 安装依赖
npm install

# 开发模式启动（热更新）
npm run dev

# TypeScript 类型检查
npx tsc -b

# 生产构建
npm run build

# 代码检查
npm run lint
```

### 8.3 修改代码后的验证步骤

1. **保存文件** → Vite 会自动热更新浏览器（如果 `npm run dev` 在运行）
2. **改了类型定义** → 运行 `npx tsc -b` 确认编译通过
3. **改了新页面或路由** → 运行 `npm run build` 确认完整构建通过
4. **改了 API 调用** → 打开浏览器开发者工具 Network 面板，确认请求正确

## 9. 后续工作

前端代码已完成，但要真正看到数据，还需要：

| 待完成项 | 说明 | 优先级 |
|---------|------|-------|
| 后端改用本地 CSV 数据 | 当前后端读 HDFS（未启动），需改为读本地 CSV | P0 |
| 后端启动并验证所有 API | `python main.py` 并用 curl 测试每个接口 | P0 |
| 前后端联调 | 浏览器打开前端，确认各页面数据正常显示 | P0 |
| 数据预览表格页面 | Streamlit 有的 `st.dataframe` 功能 | P2 |
| 响应式布局优化 | 移动端适配 | P2 |
| 代码分割优化 | 当前构建产物 684KB，可用 `React.lazy` 拆分 | P3 |

---

**日期**: 2026-06-12
**作者**: 项目组