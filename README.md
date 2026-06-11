# LockScreen Demo

一个本地运行的 AI 锁屏生成 Demo。用户输入自然语言，后端调用
OpenAI-compatible Chat Completions API 生成 LockScreen DSL JSON，前端根据同一份
JSON 渲染手机锁屏，并支持导出 PNG、JPEG 和 SVG。

## 功能链路

```text
自然语言
  -> LLM 理解
  -> LockScreen DSL JSON
  -> Vue/CSS 锁屏预览
  -> JSON 转 SVG/XML
  -> PNG / JPEG / SVG 导出
```

第一版只使用 Vue、CSS、HTML 和 SVG，不依赖素材库，不扫描
`public/materials`，不使用图片检索、多模态、视频或 Lottie。

## 技术栈

- Vue 3 + Vite
- FastAPI + Uvicorn
- OpenAI-compatible Chat Completions API
- html-to-image

## 项目结构

```text
lockscreen-demo/
├─ backend/
│  ├─ main.py
│  ├─ llm_client.py
│  ├─ requirements.txt
│  └─ tests/
├─ src/
│  ├─ components/
│  │  ├─ ExportPanel.vue
│  │  └─ LockScreenPreview.vue
│  ├─ core/
│  │  ├─ exportImage.js
│  │  ├─ exportSvg.js
│  │  └─ fallbackDSL.js
│  └─ App.vue
└─ test/
```

## 环境配置

后端只读取 `backend/.env`。该文件已被 Git 忽略，不会提交到仓库。

支持以下两组变量名，优先读取 `LLM_*`：

```dotenv
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://your-openai-compatible-endpoint/v1
LLM_MODEL=your_model
```

也兼容当前通义千问配置：

```dotenv
QWEN_API_KEY=your_api_key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen3.7-max
```

不要将真实 API Key 提交到 Git。

## 本地启动

### 1. 启动后端

```powershell
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

后端地址：`http://localhost:8000`

健康检查：

```text
GET http://localhost:8000/api/health
```

生成接口：

```text
POST http://localhost:8000/api/generate-lockscreen
Content-Type: application/json

{
  "prompt": "生成一个夜晚星空风格锁屏，有月亮和星星，整体深色高级一点，底部显示天气卡片。"
}
```

LLM 请求失败或返回无效 JSON 时，后端会自动返回 fallback DSL。

### 2. 启动前端

```powershell
cd lockscreen-demo
npm install
npm run dev
```

浏览器访问：`http://localhost:5173`

如果本地已经存在完整的 `node_modules`，可以直接运行 `npm run dev`。

## DSL 支持

- `text`：时间、日期、标题和短句
- `widget`：天气、日程和音乐卡片
- `shape`：`circle`、`roundedRect`、`blob`、`line`、`star`
- `glassCard`：玻璃拟态内容卡片
- 动画：`float`、`pulse`、`rotate`

## 导出

- `lockscreen.png`
- `lockscreen.jpeg`
- `lockscreen.svg`

PNG 和 JPEG 使用 `html-to-image` 导出。SVG 由 LockScreen DSL 手动转换生成。

## 测试与构建

前端：

```powershell
npm test
npm run build
```

后端：

```powershell
cd backend
python -m unittest discover -s tests -v
```
