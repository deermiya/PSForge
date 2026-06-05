#=============================================================    
# module name : image_analyzer.py                                    
# author      : Chmy                                       
# create time : 2026-06-05
# description : PS Image Analyzer prompt for PSForge MCP Server
#=============================================================    
"""PS Image Analyzer Prompt."""

from typing import Callable
from mcp.server.fastmcp import FastMCP
from psforge.registry import register_prompt

PROMPT_CONTENT = """# PS Image Analyzer

将任意图片拆解为 PSForge MCP server 可直接执行的结构化重建规格书。

## 核心流程

1. 用户提供图片（上传或URL）
2. Claude 用视觉能力分析图片
3. 输出 JSON 格式的重建规格书（PS Reconstruction Spec）
4. 规格书中的每个操作直接对应 PSForge 的工具 and 参数

## 分析维度

按以下顺序逐项分析，**不要跳过任何一项**：

### 1. 画布信息
- 推断尺寸（像素），如无法精确判断则根据图片比例和常见用途给出合理值
- 分辨率（默认72dpi，印刷品用300dpi）
- 色彩模式（默认RGB）

### 2. 图层拆解（从最底层到最顶层）
将图片拆解为可重建的图层结构。每个图层标注：

- **type**: 图层类型，取值：
  - `fill` — 纯色填充层（对应 `create_layer` + `fill_layer`）
  - `text` — 文字层（对应 `create_text_layer`）
  - `image` — 图片/照片层（对应 `place_image`，需外部素材）
  - `shape` — 几何形状（⚠️ PSForge 暂不支持，标记到 unsupported）
  - `gradient` — 渐变填充（⚠️ PSForge 暂不支持，标记到 unsupported）
  - `effect` — 图层样式/特效（⚠️ PSForge 暂不支持，标记到 unsupported）

- **name**: 语义化图层名，如 "背景色块"、"标题文字"、"产品图"
- **position**: `{ "x": number, "y": number }` 左上角坐标（像素）
- **size**: `{ "width": number, "height": number }` 尺寸（像素）
- **opacity**: 0-100
- **blend_mode**: 混合模式（NORMAL, MULTIPLY, SCREEN, OVERLAY 等，PSForge 支持27种）
- **visible**: true/false

**文字层额外字段：**
- **text**: 文字内容
- **font_size**: 字号（pt）
- **font_name**: 字体名（尽量推断，无法确定则给出风格描述如 "无衬线粗体"）
- **color**: `{ "r": 0-255, "g": 0-255, "b": 0-255 }`
- **alignment**: LEFT / CENTER / RIGHT

**填充层额外字段：**
- **color**: `{ "r": 0-255, "g": 0-255, "b": 0-255 }`

**图片层额外字段：**
- **description**: 对该图片内容的详细描述（便于后续 AI 生图或人工寻找素材）
- **source_hint**: 素材类型提示，如 "需要一张产品照片"、"可用AI生成"

### 3. 滤镜和调整
识别图片上应用的后期效果：
- 模糊（高斯模糊、动感模糊）→ 对应 `apply_gaussian_blur` / `apply_motion_blur`
- 锐化 → 对应 `apply_sharpen`
- 噪点 → 对应 `apply_noise`
- 亮度/对比度 → 对应 `adjust_brightness_contrast`
- 色相/饱和度 → 对应 `adjust_hue_saturation`
- 去色 → 对应 `desaturate`
- 反色 → 对应 `invert`

### 4. 不支持元素标记
PSForge 当前 **不支持** 以下操作，遇到时必须标记到 `unsupported` 数组：
- 矢量形状（矩形、圆形、多边形、自定义路径）
- 渐变填充/渐变叠加
- 图层样式（投影、描边、内发光、外发光、斜面浮雕等）
- 钢笔路径/贝塞尔曲线
- 智能对象
- 剪贴蒙版
- 调整图层（色阶、曲线、色彩平衡等独立调整图层）
- 图案填充/图案叠加
- 自定义笔刷绘制

对于每个不支持的元素，给出：
- **element**: 元素描述
- **workaround**: 如果有替代方案（如用选区+填充模拟矩形），说明替代步骤；否则标注 "需要补充工具"

## 输出格式

严格输出以下 JSON 结构，不要包裹在 markdown 代码块中：

```json
{
  "document": {
    "width": 1200,
    "height": 628,
    "resolution": 72,
    "color_mode": "RGB",
    "name": "推断的文档名"
  },
  "layers": [
    {
      "order": 1,
      "type": "fill",
      "name": "背景",
      "position": { "x": 0, "y": 0 },
      "size": { "width": 1200, "height": 628 },
      "opacity": 100,
      "blend_mode": "NORMAL",
      "visible": true,
      "color": { "r": 34, "g": 34, "b": 34 }
    },
    {
      "order": 2,
      "type": "text",
      "name": "标题",
      "position": { "x": 600, "y": 200 },
      "size": { "width": 800, "height": 80 },
      "opacity": 100,
      "blend_mode": "NORMAL",
      "visible": true,
      "text": "Hello World",
      "font_size": 72,
      "font_name": "Arial-Bold",
      "color": { "r": 255, "g": 255, "b": 255 },
      "alignment": "CENTER"
    },
    {
      "order": 3,
      "type": "image",
      "name": "产品图",
      "position": { "x": 100, "y": 150 },
      "size": { "width": 400, "height": 400 },
      "opacity": 100,
      "blend_mode": "NORMAL",
      "visible": true,
      "description": "白色背景上的耳机产品照，45度角俯拍，柔光",
      "source_hint": "需要产品实拍图"
    }
  ],
  "adjustments": [
    {
      "target_layer": "产品图",
      "type": "brightness_contrast",
      "params": { "brightness": 10, "contrast": 15 }
    }
  ],
  "unsupported": [
    {
      "element": "标题文字下方的投影效果",
      "workaround": "可复制文字层，下移2px，填充黑色，降低透明度模拟"
    },
    {
      "element": "背景从左到右的蓝-紫渐变",
      "workaround": "需要补充工具；临时可用 execute_script 执行 ExtendScript 实现"
    }
  ]
}
```

## 关键原则

1. **精确优于模糊**：颜色用吸色值而非"蓝色"；位置用像素而非"左上方"
2. **可执行优于好看**：每个字段都要能直接传给 PSForge 工具，不能有歧义
3. **诚实标记能力边界**：PSForge 做不到的不要硬凑，明确标到 unsupported
4. **图层顺序从底到顶**：order=1 是最底层（背景），依次递增
5. **文字内容原样保留**：图中能看清的文字照抄，看不清的用 `[illegible]` 标记
6. **中文图中文标注**：图层名、描述等跟随图片语言

## 与 PSForge 工具的映射

PSForge v0.3.0+ 采用极简的 5 核心工具架构（无各个细分工具）。分析完成后，如果用户要求执行，AI 客户端应将重建规格书（JSON）翻译为对应的 Photoshop ExtendScript，并通过 `execute_script` 或 `execute_batch` 执行：

1. **创建文档**：根据 `document` 节点参数，编写 ExtendScript 调用 `app.documents.add(width, height, resolution, name, colorMode)` 新建文档。
2. **构建图层**（按 `order` 从底到顶顺序遍历 `layers`）：
   - `fill`：创建新图层，建立全选区并使用 `SolidColor` 进行填充。
   - `text`：创建新图层并将 `kind` 设为 `LayerKind.TEXT`，接着设置文字内容（`contents`）、字体（`font`）、字号（`size`）、颜色（`color`）及对齐方式。
   - `image`：通过文件路径置入外部图像素材。
3. **设置图层属性**：对各图层设置不透明度（`opacity`）与混合模式（`blendMode`）。
4. **应用滤镜和调整**：按照 `adjustments` 应用对应的后期效果（如高斯模糊、亮度/对比度调整等）。
5. **保存输出**：调用 `activeDocument.saveAs()` 保存为最终文件。
"""

def register(mcp: FastMCP) -> list[str]:
    """Register the image analyzer prompt with FastMCP."""
    
    def analyze_ps_image() -> str:
        """分析图片并输出可直接执行的 Photoshop 重建规格书（JSON）。"""
        return PROMPT_CONTENT

    # Register the prompt
    prompt_name = register_prompt(
        mcp,
        analyze_ps_image,
        name="ps-image-analyzer",
        description="分析图片并输出 PSForge MCP 可执行的 Photoshop 重建规格书（JSON）"
    )
    return [prompt_name]
