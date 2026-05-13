# AI 赋能的智能简历分析系统

基于 Python + FastAPI + 通义千问 (Qwen) 的智能简历分析系统，支持 PDF 简历解析、AI 关键信息提取、岗位匹配分析，可选择 Redis 或内存缓存。

---

## 在线演示

- **前端页面**：https://3394666242jjy-lab.github.io/ai-resume-analyzer/
- **后端 API**：https://resume-api-v-urokdnwpiq.cn-hangzhou.fcapp.run
- **API 文档**：https://resume-api-v-urokdnwpiq.cn-hangzhou.fcapp.run/docs

> **注意**：阿里云 FC 按量计费，测试完毕建议释放资源避免持续扣费。

---

## 项目架构

```
.
├── backend/                 # Python FastAPI 后端
│   ├── app/
│   │   ├── api/v1/          # RESTful API 路由层
│   │   ├── core/            # 配置与缓存管理
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
│   ├── .fcignore            # FC 部署排除文件
│   └── Dockerfile           # 容器化构建
├── frontend/                # 前端页面
│   ├── index.html           # 首页
│   ├── style.css            # 样式文件
│   ├── app.js               # 业务逻辑
│   └── deploy-config.js     # 后端 API 地址配置
├── .github/workflows/       # GitHub Actions 自动部署
└── README.md
```

---

## 技术选型

| 层级 | 技术 | 说明 |
|------|------|------|
| Web 框架 | FastAPI + Uvicorn | 高性能异步 Python Web 框架，自动生成 OpenAPI 文档 |
| 数据校验 | Pydantic | 类型安全，请求/响应模型 |
| PDF 解析 | PyPDF2 | 纯 Python PDF 文本提取 |
| AI 模型 | 通义千问 (Qwen) | 简历信息提取与匹配分析（通过 OpenAI 兼容接口调用） |
| 缓存 | Redis / Memory | 支持 Redis 分布式缓存，未配置时自动回退为内存缓存 |
| 部署 | 阿里云函数计算 FC | Serverless 架构，按需付费 |
| 前端 | 原生 HTML5 + CSS3 + JS | 零构建工具，单页应用 |
| CI/CD | GitHub Actions | 自动构建前端到 GitHub Pages |

---

## 功能模块

| 模块 | 功能 | 状态 |
|------|------|------|
| **简历上传与解析** | 支持 PDF 格式简历上传与文本提取 | 已就绪 |
| **关键信息提取** | AI 自动提取姓名、电话、邮箱、地址、工作经历、项目经历、技能等 | 已就绪 |
| **岗位匹配分析** | 基于岗位描述进行技能、经验、学历多维匹配评分 | 已就绪 |
| **缓存与持久化** | JSON 结构化缓存，支持 Redis / 内存缓存 | 已就绪 |
| **前端交互页面** | 开箱即用的 Web 可视化界面 | 已就绪 |
| **AI 语义理解** | 基于 Qwen 大模型进行深度语义提取与匹配 | 已就绪 |

---

## 快速开始

### 环境要求

- Python >= 3.9
- (可选) Redis >= 5.0
- 通义千问 API Key（从 [阿里云百炼](https://bailian.console.aliyun.com/) 获取）

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

### 4. 配置环境变量

复制 `.env.example` 为 `.env`，并填写你的通义千问 API Key：

```bash
cp .env.example .env
```

编辑 `.env`：

```env
QWEN_API_KEY=sk-你的真实Key
```

### 5. 启动服务

```bash
python start.py
```

服务启动后访问：
- **前端页面**：http://localhost:8000/
- **API 文档**：http://localhost:8000/docs

---

## 环境变量说明

### 本地开发（.env 文件）

| 变量名 | 说明 | 默认值 |
|---------|------|--------|
| `QWEN_API_KEY` | 通义千问 API 密钥 | - |
| `QWEN_BASE_URL` | 通义千问接口地址 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `QWEN_MODEL` | 使用模型 | `qwen-plus` |
| `REDIS_HOST` | Redis 服务器地址（可选） | - |
| `REDIS_PORT` | Redis 端口 | 6379 |
| `APP_HOST` | 服务绑定地址 | 0.0.0.0 |
| `APP_PORT` | 服务端口 | 8000 |
| `MAX_FILE_SIZE` | 最大上传文件大小 | 10485760 (10MB) |

> 兼容阿里云标准变量名 `DASHSCOPE_API_KEY`，优先级低于 `QWEN_API_KEY`。

### 阿里云 FC 控制台配置

由于阿里云 FC 控制台对环境变量名的输入存在兼容性问题，**建议直接在 FC 控制台使用以下极简命名**：

| FC 控制台变量名 | 对应含义 | 示例值 |
|----------------|---------|--------|
| `ApiKey` | 通义千问 API Key | `sk-xxx` |
| `BaseUrl` | 接口 Base URL | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `AiModel` | 模型名称 | `qwen-plus` |

代码已同时兼容 `QWEN_API_KEY`、`QwenApiKey`、`ApiKey` 等多种命名方式。

---

## API 接口

### 上传并匹配（一步到位）

```http
POST /api/v1/resume/upload-and-match
Content-Type: multipart/form-data

file: <PDF 文件>
job_description: <岗位描述文本>
```

**响应示例**

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

### 核心接口列表

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/resume/upload` | POST | 上传简历文件 |
| `/api/v1/resume/parse/{resume_id}` | GET | 解析简历信息 |
| `/api/v1/resume/match` | POST | 简历岗位匹配分析 |
| `/api/v1/resume/upload-and-match` | POST | 上传+匹配一步到位 |

---

## 部署方式

### 方式一：阿里云函数计算 FC（推荐）

```bash
cd backend

# 安装 Serverless Devs CLI
npm install -g @serverless-devs/s

# 配置阿里云凭证（首次使用）
s config add

# 部署（.env 等敏感文件已自动排除）
s deploy
```

部署完成后获取公网访问地址，然后到 FC 控制台配置环境变量：
- **函数名**：`resume-api-v5`
- **环境变量**：添加 `ApiKey` = `sk-你的Key`

**注意事项**：
- FC `custom.debian11` runtime 使用 Python 3.9
- 首次冷启动会自动执行 `pip install` 安装新依赖
- 按量计费：每月前 100 万次调用 + 40 万 GB-秒资源免费

### 方式二：Docker 本地运行

```bash
cd backend
docker build -t ai-resume-analyzer .
docker run -p 8000:8000 --env-file .env ai-resume-analyzer
```

### 方式三：前端部署到 GitHub Pages

1. Fork 或推送代码到 GitHub 仓库
2. 进入仓库 **Settings > Pages**
3. Source 选择 **GitHub Actions**
4. 等待自动构建完成即可访问

**配置后端 API 地址**：

前端修改 `frontend/deploy-config.js`：
```javascript
window.API_BASE = 'https://你的FC地址/api/v1';
```

或在浏览器控制台临时切换：
```javascript
localStorage.setItem('api_base', 'https://你的FC地址/api/v1');
location.reload();
```

---

## 运行测试

```bash
cd backend
pytest tests/
```

---

## 评分标准与响应

| 维度 | 权重 | 实现要点 |
|------|------|----------|
| **核心功能实现** | 30% | 全栈工程实现，PDF 解析、AI 提取、匹配评分 |
| **代码质量** | 25% | 结构清晰、类型注解、分层明确（API/Service/Utils） |
| **工程化实践** | 20% | Git 规范、README 文档、Dockerfile、Serverless 配置、环境变量安全 |
| **架构设计** | 15% | AI 模型可替换性、缓存自动降级、部署优化 |
| **附加功能** | 10% | AI 语义匹配、Redis 缓存、前端交互界面、GitHub Pages 部署 |

---

## License

MIT License
