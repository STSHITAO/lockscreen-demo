# LockScreen Demo

一个本地运行的 AI 锁屏生成 Demo。用户输入自然语言，后端先提取结构化素材需求，再从本地 SVG 和序列帧动画目录检索候选，最后让 LLM 在候选范围内生成 LockScreen DSL。Vue 使用同一份 DSL 渲染静态或动态锁屏，并支持导出 PNG、JPEG 和独立 SVG。

## 当前链路

```text
用户自然语言
  -> LLM 提取设计意图和素材槽位
  -> assets.json / animations.json 标签检索（不使用 embedding）
  -> 每个槽位返回 Top-K 静态或动画候选
  -> LLM 只能从候选 assetId 中选材并生成 draft DSL
  -> schema / asset / layout / semantic validators
  -> 素材确认缺失时由 Fallback Draw Agent 注入受控 shape DSL
  -> 最多两轮 deterministic-first repair agent
  -> 通过校验或返回 fallback DSL
  -> Vue/CSS/SVG 渲染
  -> PNG / JPEG / 独立 SVG 导出
```

当前素材策略限制为最多一个主视觉素材和两个辅助素材。LLM 不能自由编造 URL、文件路径或素材 ID。

前端默认调用流式接口。`qwen3.7-max` 使用 thinking 模式，后端将
`reasoning_content`、阶段状态、校验和修复事件通过 SSE 实时发送到浏览器。
生成结束以模型返回 `finish_reason` 和流结束标记为准，而不是固定等待 60 秒。
网络连接只有在连续 300 秒没有收到任何新数据时才会触发读取超时。

## 技术栈

- Vue 3 + Vite
- FastAPI + Uvicorn
- OpenAI-compatible Chat Completions API
- html-to-image
- 本地结构化 SVG 与序列帧动画素材目录

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
│  ├─ animations.json
│  ├─ frames/
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
├─ scripts/generate-animation-catalog.mjs
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

流式生成：

```text
POST http://localhost:8000/api/generate-lockscreen/stream
Content-Type: application/json
Accept: text/event-stream
```

流式事件包括 `phase`、`thinking`、`progress`、`validation`、`repair` 和
`final`。旧的非流式生成接口继续保留用于兼容。

调试素材检索：

```text
GET http://localhost:8000/api/materials/search?q=rocket&limit=8
```

健康检查：

```text
GET http://localhost:8000/api/health
```

模型请求失败、返回非法 JSON 或输出非法素材 ID 时，后端会返回安全的 fallback DSL。
返回 DSL 中的 `_debug` 字段会记录修复轮数、修复前后错误和是否使用 fallback，
方便观察 V2.1 agent-loop；渲染器会忽略该调试字段。

## V2.2 Fallback Draw Agent

系统始终优先使用本地可信 SVG 素材。只有素材候选明确为空，或本地目录无法找到
对应视觉目标时，orchestrator 才会调用确定性的 Fallback Draw Agent。该 Agent
只输出白名单 DSL shape，不生成自由 SVG、HTML 或 Vue 代码。

当前支持 `moon/crescent`、`star`、`heart`、`cloud`、`sparkle`、`planet`、
`circle/dot` 和 `blob`。生成的 layer 会带有 `fallback: true` 与
`fallbackReason: "asset_missing"`，并继续通过 layout、semantic validators
及现有 Repair Loop。Vue 预览和 SVG 导出使用同一份最终 DSL。

## V2.3 帧动画与动画 Fallback

动态效果按以下优先级生成：

1. 本地素材库命中合适的 `frameAnimation` 时，使用经过后端校验的 PNG 连续帧。
2. 没有帧动画素材、但效果可以安全地用基础图层表达时，Animation Fallback Agent 会为 shape 或静态素材添加受控 CSS 动画。
3. 对城堡变形、人物动作等复杂效果，不让模型自由生成未知图形。系统保留其余锁屏内容，并通过 `animation_unavailable` 事件和 `_debug.animationNotices` 返回“未匹配到动画素材，效果较复杂，暂时无法自主生成”的提示。

受控 CSS 动画包括 `float`、`pulse`、`rotate`、`twinkle`、`drift-left`、
`drift-right`、`sway`、`bounce`、`fade` 和 `breathe`。例如云朵漂移可以使用
`drift-left` / `drift-right`，爱心跳动可以使用 `pulse`。这些 fallback 仍然输出
LockScreen DSL，不让 LLM 直接生成 CSS、SVG 或 HTML。

PNG/JPEG 会捕获导出时的当前动画画面；SVG 导出保持为可独立打开的静态表示。

## DSL 图层

- `text`：时间、日期、标题和短句
- `widget`：天气、日程和音乐卡片
- `shape`：`circle`、`roundedRect`、`blob`、`line`、`star`
- `glassCard`：玻璃拟态内容卡片
- `asset`：引用经过后端校验的本地 SVG 素材
- `frameAnimation`：引用经过后端校验的 PNG 连续帧动画素材
- 动画：`float`、`pulse`、`rotate`、`twinkle`、`drift-left`、`drift-right`、`sway`、`bounce`、`fade`、`breathe`

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

`frameAnimation` 示例：

```json
{
  "id": "twinkle-star",
  "type": "frameAnimation",
  "assetId": "frame-star-twinkle-001",
  "x": 280,
  "y": 300,
  "width": 88,
  "height": 88,
  "fit": "contain"
}
```

LLM 只选择 `assetId`。后端会从 `animations.json` 写入可信的 `frames`、
`poster`、`fps` 和 `loop`，并将 DSL `mode` 设置为 `dynamic`。

## V2.4 交互动作 DSL

V2.4 在视觉 `layers` 之外增加顶层 `interactions` 和 `cardGroups`。LLM
只组合受控 Trigger 与 Action，不生成 JavaScript、CSS 事件代码或自由 SVG。

支持的 Trigger：

- `tap`
- `multiTap`
- `longPressStart`
- `longPressEnd`
- `swipeLeft`
- `swipeRight`

支持的 Action：

- `animate`
- `stopAnimation`
- `setAnimationSpeed`
- `burst`
- `switchCard`
- `setVisibility`
- `reset`

模糊的“连续点击几次”按三次处理；明确次数按用户要求并限制到 `1–10`。
爆炸默认结束后恢复，只有用户明确要求消失时才使用 `afterEffect: "hide"`。
粒子优先使用 `heart/star/sparkle/circle` 基础图形，也可以引用经过后端素材
目录校验的本地 SVG `assetId`。

示例：

```json
{
  "interactions": [
    {
      "id": "heart-triple-tap",
      "targetId": "main-heart",
      "trigger": {
        "type": "multiTap",
        "count": 3,
        "withinMs": 1200
      },
      "actions": [
        {
          "type": "animate",
          "animation": "pulse",
          "duration": 600,
          "speed": 2,
          "intensity": 1.5
        },
        {
          "type": "burst",
          "particleSource": {"type": "shape", "shape": "heart"},
          "count": 12,
          "duration": 800,
          "afterEffect": "restore"
        }
      ]
    }
  ]
}
```

`cardGroups` 只切换锁屏内部天气、日程、短句等卡片，不切换整张锁屏。
PNG/JPEG 捕获导出时的当前交互画面；SVG 导出稳定静态状态，不携带脚本或
交互处理器。无法实现的复杂交互会写入 `_debug.interactionNotices`，不会让
整张锁屏进入 fallback。

## 导出

- `lockscreen.png`
- `lockscreen.jpeg`
- `lockscreen.svg`

PNG 和 JPEG 使用 `html-to-image` 导出并捕获导出时的当前动画帧。SVG 由 DSL
手动生成：静态素材会嵌入 SVG 源码，序列帧动画会嵌入目录定义的代表帧。

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
