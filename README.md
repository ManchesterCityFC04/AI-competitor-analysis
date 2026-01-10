# AI 竞品分析工具

基于大语言模型（LLM）和搜索 API 的智能竞品分析工具，帮助快速发现和分析指定领域的竞争产品。

## 功能特性

### 核心功能
- **智能搜索查询生成** - LLM 自动生成优化的搜索查询
- **并行网页搜索** - 通过 Anspire API 高效搜索竞品信息
- **竞品智能提取** - 从搜索结果中自动识别和提取竞品
- **相关性评分系统** - 对竞品进行 1-10 分的相关性评分
  - 9-10 分：高度相关（直接竞品）
  - 7-8 分：中度相关（间接竞品）
  - 5-6 分：低度相关（领域相关）
  - 1-4 分：弱相关
- **功能深度挖掘** - 二次搜索获取竞品详细功能信息

### 导出功能
- **Excel 导出** - 导出包含竞品数据和分析摘要的 Excel 文件
- **PDF 导出** - 生成格式化的 PDF 分析报告

### 用户体验
- **实时进度显示** - SSE 流式推送分析进度
- **阶段指示器** - 可视化展示 8 个分析阶段
- **响应式界面** - 现代化 React 前端，支持各种设备

## 项目结构

```
prototype/
├── backend/                    # 后端代码
│   ├── api/                    # API 入口
│   │   └── main.py             # FastAPI 主应用（含 SSE 端点）
│   ├── agent/                  # Agent 模块
│   │   ├── competitor_agent.py # 竞品分析 Agent
│   │   └── feature_extractor.py# 功能深度提取器
│   ├── llm/                    # LLM 客户端模块
│   │   └── client.py
│   ├── tools/                  # 工具模块
│   │   ├── anspire_search.py   # 搜索工具
│   │   └── web_reader.py       # 网页读取工具
│   └── requirements.txt
├── frontend/                   # 前端代码
│   ├── src/
│   │   ├── App.tsx             # 主应用组件
│   │   └── styles/
│   └── package.json
├── env-example.txt             # 环境变量示例
└── README.md
```

## 技术栈

### 后端
- **Python 3.10+**
- **FastAPI** - 高性能异步 Web 框架
- **SSE (Server-Sent Events)** - 实时进度推送
- **OpenAI SDK** - LLM 调用
- **Requests** - HTTP 请求
- **Loguru** - 日志管理
- **ThreadPoolExecutor** - 并行处理

### 前端
- **React 18** - UI 框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **TailwindCSS** - 样式框架
- **Framer Motion** - 动画效果
- **xlsx** - Excel 导出
- **file-saver** - 文件下载

## 快速开始

### 后端启动

```bash
# 安装依赖
cd prototype
pip install -r backend/requirements.txt

# 创建环境变量文件
cp env-example.txt .env
# 编辑 .env 填入你的 API 密钥

# 启动后端服务
cd backend/api
python main.py
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

启动后访问：`http://localhost:5173`（或终端显示的端口）

## 环境变量配置

```env
# Anspire 搜索 API
ANSPIRE_API_KEY=your_anspire_api_key

# LLM 配置
LLM_API_KEY=your_llm_api_key
LLM_BASE_URL=your_llm_base_url
LLM_MODEL=gpt-4
```

## 使用说明

1. **输入分析领域**（可选）- 例如："AI 教育"、"在线协作"
2. **输入功能描述**（可选）- 例如："AI 批阅试卷、自动组卷"
3. **输入产品名称**（必填）- 例如："我的 AI 助手"
4. 点击 **"开始智能分析"** 按钮
5. 观察实时进度条和阶段指示器
6. 分析完成后查看竞品列表
7. 可点击 **"导出 Excel"** 或 **"导出 PDF"** 保存结果

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/analyze` | POST | 执行竞品分析（同步） |
| `/api/analyze/stream` | GET | 执行竞品分析（SSE 流式） |
| `/health` | GET | 健康检查 |

## 分析流程

```
1. 初始化分析
   ↓
2. 生成搜索查询（3 个优化查询）
   ↓
3. 并行搜索竞品信息
   ↓
4. 读取网页内容
   ↓
5. 提取竞品数据 + 相关性评分
   ↓
6. 合并去重
   ↓
7. 深度分析功能（二次搜索）
   ↓
8. 返回分析结果
```

## 注意事项

- 后端默认运行在 8001 端口
- 前端默认运行在 5173 端口（Vite 默认）
- 确保 `.env` 文件中的 API 密钥已正确配置
- 分析过程可能需要 1-3 分钟，取决于竞品数量

## 待办事项

### 已完成
- [x] Excel 导出功能
- [x] PDF 导出功能
- [x] 实时进度显示
- [x] 竞品相关性评分
- [x] 功能深度挖掘

### 计划中
- [ ] 用户认证系统
- [ ] 分析历史存储
- [ ] 支持多搜索引擎
- [ ] 竞品对比功能
- [ ] 数据可视化图表
- [ ] Docker 容器化
- [ ] 深色模式

## 许可证

MIT

## 贡献

欢迎提交 Issue 和 Pull Request！
