# LockScreen Demo

一个本地运行的 AI 锁屏生成 Demo。用户输入自然语言，后端先提取结构化素材需求，再从本地 SVG 目录检索候选，最后让 LLM 在候选范围内生成 LockScreen DSL。Vue 使用同一份 DSL 渲染锁屏，并支持导出 PNG、JPEG 和独立 SVG。

## 当前链路

```text
用户自然语言
  -> LLM 提取设计意图和素材槽位
  -> assets.json 标签检索（不使用 embedding）
  -> 每个槽位返回 Top-K SVG 候选
  -> LLM 只能从候选 assetId 中选材并生成 DSL
  -> 后端校验 assetId 并解析本地 src
  -> Vue/CSS/SVG 渲染
  -> PNG / JPEG / 独立 SVG 导出
```

当前素材策略限制为最多一个主视觉素材和两个辅助素材。LLM 不能自由编造 URL、文件路径或素材 ID。

## 技术栈

- Vue 3 + Vite
- FastAPI + Uvicorn
- OpenAI-compatible Chat Completions API
- html-to-image
- 本地结构化 SVG 素材目录

## 项目结构

```text
lockscreen-demo/
├─ backend/
│  ├─ main.py
│  ├─ llm_client.py
│  ├─ material_catalog.py
│  ├─ requirements.txt
│  └─ tests/
├─ public/materials/
│  ├─ assets.json
│  ├─ README.md
│  └─ svg/
├─ src/
│  ├─ components/
│  │  ├─ ExportPanel.vue
│  │  └─ LockScreenPreview.vue
│  ├─ core/
│  │  ├─ exportImage.js
│  │  ├─ exportSvg.js
│  │  ├─ fallbackDSL.js
│  │  └─ materialSearch.js
│  └─ App.vue
├─ scripts/generate-material-catalog.mjs
└─ test/
```

## 环境配置

后端只读取 `backend/.env`：

```dotenv
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://your-openai-compatible-endpoint/v1
LLM_MODEL=your_model
```

仓库提供了 `backend/.env.example`，当前通义千问配置可以复制后填写真实 Key：

```powershell
Copy-Item backend/.env.example backend/.env
```

后端同时兼容示例文件中的 `QWEN_API_KEY`、`QWEN_BASE_URL` 和 `QWEN_MODEL`。

不要把真实 API Key 提交到 Git。

## 本地启动

后端：

```powershell
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

前端：

```powershell
npm install
npm run dev
```

访问 `http://localhost:5173`。

如果依赖已经完整安装，可以直接执行 `npm run dev`。Python 环境中已安装 `backend/requirements.txt` 的全部依赖时，也不需要重复安装。

## API

生成锁屏：

```text
POST http://localhost:8000/api/generate-lockscreen
Content-Type: application/json

{
  "prompt": "生成一个可爱的太空锁屏，有火箭和飞碟，整体深蓝色。"
}
```

调试素材检索：

```text
GET http://localhost:8000/api/materials/search?q=rocket&limit=8
```

健康检查：

```text
GET http://localhost:8000/api/health
```

模型请求失败、返回非法 JSON 或输出非法素材 ID 时，后端会返回安全的 fallback DSL。

## DSL 图层

- `text`：时间、日期、标题和短句
- `widget`：天气、日程和音乐卡片
- `shape`：`circle`、`roundedRect`、`blob`、`line`、`star`
- `glassCard`：玻璃拟态内容卡片
- `asset`：引用经过后端校验的本地 SVG 素材
- 动画：`float`、`pulse`、`rotate`

`asset` 示例：

```json
{
  "id": "hero-rocket",
  "type": "asset",
  "assetId": "doodle-034",
  "src": "/materials/svg/doodle-34.svg",
  "x": 70,
  "y": 330,
  "width": 250,
  "height": 250,
  "fit": "contain",
  "rotation": -8,
  "opacity": 1,
  "animation": "float"
}
```

其中 `src` 由后端根据 `assetId` 写入，不接受模型提供的任意路径。

## 导出

- `lockscreen.png`
- `lockscreen.jpeg`
- `lockscreen.svg`

PNG 和 JPEG 使用 `html-to-image` 导出。SVG 由 DSL 手动生成，本地素材的 SVG 源码会被嵌入最终文件，不依赖 `/materials` 外链。

## 测试

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
