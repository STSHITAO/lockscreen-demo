# 素材标签说明

> 当前接入状态：该目录已用于后端的结构化素材检索。生成流程会先按素材槽位返回 Top-K 静态或动画候选，再由 LLM 从候选 `assetId` 中选择；后端会二次校验并解析真实文件路径。当前阶段不使用 embedding。

本目录保存锁屏 Demo 的本地静态 SVG、PNG 序列帧及其结构化目录。当前共有
151 张有效 SVG，以及 1 组包含 5 张 PNG 的序列帧动画。

## 目的

素材标签用于把自然语言需求转换成可解释、可约束的素材选择过程：

```text
用户自然语言
  -> LLM 提取主题、主体、情绪和用途
  -> assets.json / animations.json 标签过滤与关键词检索
  -> 返回真实 assetId
  -> LockScreen DSL 引用素材
  -> Vue / SVG 渲染
```

第一阶段采用结构化标签检索，不使用向量数据库。这样可以先验证标签体系、
素材角色和构图约束是否合理，也便于检查为什么某张素材被选中。素材数量增长到
数千张后，可以在现有标签过滤之前增加 VL embedding 语义召回。

## 文件

```text
public/materials/
├─ README.md
├─ assets.json
├─ animations.json
├─ frames/
│  └─ star_twinkle/
│     ├─ 01.png
│     └─ ...
└─ svg/
   ├─ doodle-01.svg
   └─ ...
```

- `svg/`：原始素材，不修改图形内容。
- `assets.json`：每张 SVG 对应一条结构化元数据。
- `frames/`：按动画名称分目录保存顺序编号的 PNG 帧。
- `animations.json`：每组连续帧对应一条动画元数据。
- `scripts/generate-material-catalog.mjs`：从人工校正的主题信息和 SVG
  结构重新生成 `assets.json`。
- `scripts/generate-animation-catalog.mjs`：验证帧目录并重新生成
  `animations.json`。
- `src/core/materialSearch.js`：标签过滤与关键词排序函数。

## 标签方法

采用“自动提取客观属性 + 人工校正语义标签”的方式。

### 自动提取

生成脚本直接从 SVG 获取：

- 文件名和访问路径
- 画布尺寸与 `viewBox`
- 实际颜色
- path 数量
- 视觉复杂度
- 是否透明、是否可改色

这批素材均为 `600 × 600`、透明背景、纯 path、纯色填充 SVG，没有嵌入
位图、滤镜或渐变。

### 人工校正

逐张确认以下语义信息：

- 中文名和英文名
- 一级分类 `category`
- 主体 `subjects`
- 中英文检索词 `keywords`
- 适用主题 `themes`
- 情绪 `moods`
- 素材用途 `roles`

描述允许使用自然语言，但分类、主题、情绪和用途使用受控词表，避免出现
“太空、宇宙风、星际风”被当成三个完全不同标签的问题。

## 字段说明

| 字段 | 作用 |
| --- | --- |
| `assetId` | DSL 和后端引用的稳定 ID |
| `file` / `src` | 真实文件名和前端访问路径 |
| `name` | 中英文名称 |
| `description` | 适合 embedding 或展示的自然语言描述 |
| `category` | 唯一一级分类 |
| `subjects` | 画面中的核心对象 |
| `keywords` | 中文、英文和常用同义检索词 |
| `themes` | 适合的锁屏主题 |
| `moods` | 情绪和视觉氛围 |
| `roles` | 在锁屏中的用途 |
| `colors` | 从 SVG 色值归一化得到的颜色标签 |
| `recommendedPositions` | 建议放置区域 |
| `visualWeight` | `light`、`medium` 或 `heavy` |
| `style` | 统一视觉风格 |
| `containsText` | 图形内部是否已有固定文字 |
| `pathCount` | SVG path 数量，可用于复杂度判断 |

动画记录额外包含：

| 字段 | 作用 |
| --- | --- |
| `assetType` | 当前固定为 `frameSequence` |
| `directory` | `frames/` 下的序列帧目录 |
| `frames` | 按播放顺序排列的可信 PNG 路径 |
| `frameCount` | 帧数量 |
| `fps` | 默认播放帧率 |
| `loop` | 是否循环播放 |
| `poster` | SVG 导出和静态环境使用的代表帧 |

`star_twinkle` 标签为：主体 `star`、`sparkle`；主题 `night`、`space`、
`cute`、`dreamy`；用途 `decoration`、`animated-accent`；主要检索词包括
“星星、闪烁、发光、星光、闪光、twinkle、glowing star”。

## 素材用途

当前素材以透明底卡通贴纸为主，不适合作为全屏背景：

- `hero`：锁屏中的主要视觉主体
- `sticker`：普通贴纸或辅助主体
- `decoration`：角落和空白区域装饰
- `icon`：小尺寸功能图标
- `callout`：可叠加短文本的对话框
- `facePart`：嘴巴、舌头等组合部件

DSL 素材图层只允许保存可信 `assetId`。静态素材由后端解析 `src`；动画素材
由后端解析 `frames`、`poster`、`fps` 和 `loop`。不要允许 LLM 自由编造
文件路径、帧顺序或播放参数。

## 检索示例

用户输入：

```text
生成一个可爱的太空锁屏，有火箭和外星人。
```

可以先提取：

```json
{
  "themes": ["space"],
  "moods": ["cute"],
  "subjects": ["rocket", "ufo"]
}
```

再从目录中召回 `doodle-034`、`doodle-044`、`doodle-057`、
`doodle-093` 等真实候选，最后交给布局阶段选择。

## 维护规则

1. 新增 SVG 后必须补充生成脚本中的人工语义标签。
2. 新增序列帧时，每组动画使用独立目录，并使用连续、可排序的文件名。
3. 运行 `npm run materials:generate` 更新静态和动画目录。
4. 运行 `npm test`，确认每张 SVG 和每组动画都恰好有一条元数据。
5. 不直接手改自动提取字段，避免目录与原始文件不一致。
6. 标签词表新增同义概念前，优先复用现有标准词。
