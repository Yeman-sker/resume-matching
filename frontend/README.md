# 简历匹配系统 - 前端

基于 React 19 + Vite + shadcn/ui + Zustand 构建的简历-岗位匹配系统前端。

## 技术栈

- **框架**: React 19 + TypeScript
- **构建工具**: Vite 8
- **UI 组件库**: shadcn/ui (Radix UI + Tailwind CSS 4)
- **状态管理**: Zustand 5
- **HTTP 客户端**: axios
- **样式**: Tailwind CSS 4

## 开发

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览构建结果
npm run preview
```

## 项目结构

```
src/
├── components/
│   └── ui/           # shadcn/ui 组件
├── pages/            # 页面组件
│   └── Dashboard.tsx # 系统监控面板
├── store/            # Zustand 状态管理
├── types/            # TypeScript 类型定义
└── lib/              # 工具函数
```

## 环境要求

- Node.js 18+
- npm 9+

## 端口

- 开发服务器: http://localhost:5173
- 后端 API: http://localhost:8002
- WebSocket: ws://localhost:8002/ws

## 功能模块

- **系统监控面板**：实时显示数据生成、Streaming 处理、批处理任务状态
- **数据生成器控制**：启动/停止数据生成器（待实现）
- **岗位匹配查询**：HR 视角，查看岗位匹配的简历（待实现）
- **简历推荐查询**：求职者视角，查看简历推荐的岗位（待实现）
- **匹配详情页**：查看详细匹配分数和推荐理由（待实现）
