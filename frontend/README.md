# 简历匹配系统 - 前端

基于 React 18 + Vite + shadcn/ui + Zustand 构建的简历-岗位匹配系统前端。

## 技术栈

- **框架**: React 18 + TypeScript
- **构建工具**: Vite 5
- **UI 组件库**: shadcn/ui (Radix UI + Tailwind CSS)
- **状态管理**: Zustand
- **HTTP 客户端**: axios
- **样式**: Tailwind CSS

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
