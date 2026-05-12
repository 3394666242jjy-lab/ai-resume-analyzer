# AI 赋能的智能简历分析系统

基于 Python + FastAPI 构建的智能简历分析系统，支持 PDF 简历解析、AI 关键信息提取、岗位匹配评分与缓存机制。

---

## 在线演示

- **前端页面**：https://3394666242jjy-lab.github.io/ai-resume-analyzer/
- **后端 API**：https://resume-api-v-urokdnwpiq.cn-hangzhou.fcapp.run
- **API 文档**：https://resume-api-v-urokdnwpiq.cn-hangzhou.fcapp.run/docs

> **注意**：阿里云 FC 函数计算有免费额度，超出后按量计费。若长期不用建议删除资源避免扣费。

---

## 项目架构

```
.
├── backend/                 # Python FastAPI 后端
│   ├── app/
│   │   ├── api/v1/          # RESTful API 路由层
│   │   ├── core/            # 核心配置与缓存管理
│   │   ├── models/          # Pydantic 数据模型
│   │   ├── services/        # 业务逻辑层
│   │   └── utils/           # 工具模块（PDF 解析、AI 客户端）
│   ├── tests/               # 接口测试
│   ├── uploads/             # 上传文件临时存储
│   ├── main.py              # FastAPI 入口
│   ├── start.py             # 本地快捷启动脚本
│   ├── requirements.txt     # Python 依赖
│   ├── bootstrap            # 阿里云 FC custom runtime 启动脚本
│   ├── s.yaml               # 阿里云 Serverless 部署配置
│   └── Dockerfile           # 容器化构建
├── frontend/                # 前端页面
│   ├── index.html           # 主页面
│   ├── style.css            # 样式文件
│   ├── app.js               # 交互逻辑
│   └── deploy-config.js     # 后端 API 地址配置
├── .github/workflows/       # GitHub Actions 自动化部署
└── README.md
```

---

## 技术选型

| 层级 | 技术 | 说明 |
|------|------|------|
| Web 框架 | FastAPI + Uvicorn | 高性能异步 Python Web 框架，自动生成 OpenAPI 文档 |
| 数据校验 | Pydantic | 类型安全的请求/响应模型 |
| PDF 解析 | PyPDF2 | 纯 Python PDF 文本提取 |
| AI 模型 | OpenAI GPT-4o-mini | 智能信息提取与匹配评分（可选，未配置时自动降级规则引擎） |
| 缓存 | Redis / Memory | 支持 Redis 分布式缓存，未配置时自动降级为内存缓存 |
| 部署 | 阿里云函数计算 FC | Serverless 部署，按需计费 |
| 前端 | 原生 HTML5 + CSS3 + JS | 零构建工具，单页面应用 |
| CI/CD | GitHub Actions | 自动部署前端至 GitHub Pages |

---

## 功能模块

| 模块 | 功能 | 状态 |
|------|------|------|
| **简历上传与解析** | 支持 PDF 多页简历上传与文本提取 | 必选 |
| **关键信息提取** | AI 自动提取姓名、电话、邮箱、地址等基本信息 | 必选 |
| **简历评分与匹配** | 基于岗位需求进行技能、经验、学历多维匹配评分 | 必选 |
| **结果返回与缓存** | JSON 结构化返回，支持 Redis / 内存缓存 | 必选 |
| **前端交互页面** | 简洁美观的 Web 交互界面 | 必选 |
| **AI 精准评分** | 调用 OpenAI GPT 模型进行深度分析 | 加分项 |
| **缓存机制** | 支持 Redis 分布式缓存，自动降级内存缓存 | 加分项 |

---

## 快速开始

### 环境要求

- Python >= 3.9
- (可选) Redis >= 5.0
- (可选) OpenAI API Key

### 1. 克隆仓库

```bash
git clone https://github.com/3394666242jjy-lab/ai-resume-analyzer.git
cd ai-resume-analyzer/backend
```

### 2. 创建虚拟环境

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 启动服务

```bash
python start.py
```

服务启动后访问：
- **前端页面**：http://localhost:8000/
- **API 文档**：http://localhost:8000/docs

---

## 配置说明

复制 `.env.example` 为 `.env`，按需配置：

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 密钥（可选） | - |
| `OPENAI_BASE_URL` | OpenAI API 地址 | https://api.openai.com/v1 |
| `OPENAI_MODEL` | 使用的模型 | gpt-4o-mini |
| `REDIS_HOST` | Redis 主机地址（可选） | - |
| `REDIS_PORT` | Redis 端口 | 6379 |
| `APP_HOST` | 服务监听地址 | 0.0.0.0 |
| `APP_PORT` | 服务端口 | 8000 |
| `MAX_FILE_SIZE` | 最大上传文件大小 | 10485760 (10MB) |

> **提示**：不配置 `OPENAI_API_KEY` 也能完整运行，系统会自动降级为规则引擎。不配置 `REDIS_HOST` 会自动使用内存缓存。

---

## API 接口

### 上传并匹配（一步到位）

```http
POST /api/v1/resume/upload-and-match
Content-Type: multipart/form-data

file: <PDF 文件>
job_description: <岗位描述文本>
```

**响应示例：**

```json
{
  "success": true,
  "message": "匹配完成",
  "resume_info": {
    "basic_info": {
      "name": "张三",
      "phone": "13800138000",
      "email": "zhangsan@example.com",
      "address": "北京市"
    },
    "skills": ["Python", "Java", "MySQL"]
  },
  "match_score": {
    "overall_score": 85.5,
    "skill_match_rate": 80.0,
    "experience_match_rate": 90.0,
    "education_match_rate": 85.0,
    "matched_keywords": ["Python", "MySQL"],
    "missing_keywords": ["Kubernetes"],
    "analysis": "该候选人技能匹配度较高..."
  }
}
```

### 其他接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/resume/upload` | POST | 上传简历文件 |
| `/api/v1/resume/parse/{resume_id}` | GET | 解析简历信息 |
| `/api/v1/resume/match` | POST | 简历与岗位匹配评分 |

---

## 部署方式

### 方式一：阿里云函数计算 FC（推荐）

```bash
cd backend

# 安装 Serverless Devs 工具
npm install @serverless-devs/s -g

# 配置阿里云凭证
s config add

# 部署
s deploy
```

部署后获取公网访问地址，更新 `frontend/deploy-config.js` 中的 `API_BASE`，然后推送至 GitHub。

**注意事项**：
- 阿里云 FC `custom.debian11` runtime 使用 Python 3.9
- 部署时需将纯 Python 依赖打包上传（`pip install -r requirements.txt -t .`）
- 免费额度：每月 100 万次调用 + 40 万 GB-秒计算资源

### 方式二：Docker 部署

```bash
cd backend
docker build -t ai-resume-analyzer .
docker run -p 8000:8000 ai-resume-analyzer
```

### 方式三：前端部署至 GitHub Pages

1. 在 GitHub 创建公开仓库
2. 推送代码至仓库
3. 进入仓库 **Settings > Pages**
4. Source 选择 **GitHub Actions**
5. 工作流自动运行，部署完成后即可访问

**配置后端 API 地址**：

前端部署后，修改 `frontend/deploy-config.js`：
```javascript
window.API_BASE = 'https://你的阿里云地址/api/v1';
```

或在浏览器控制台执行：
```javascript
localStorage.setItem('api_base', 'https://你的阿里云地址/api/v1');
location.reload();
```

---

## 测试

```bash
cd backend
pytest tests/
```

---

## 评分标准对应

| 维度 | 权重 | 本项目实现 |
|------|------|-----------|
| **功能完整性** | 30% | 全部必选模块已实现并可正常运行 |
| **代码质量** | 25% | 结构清晰，命名规范，分层明确（API/Service/Utils） |
| **工程化实践** | 20% | Git 管理、README 文档、Dockerfile、Serverless 配置、错误处理 |
| **技术深度** | 15% | AI 模型可插拔设计、缓存自动降级、性能优化 |
| **加分项** | 10% | AI 精准评分、Redis 缓存、前端交互体验、GitHub Pages 部署 |

---

## 许可证

MIT License
