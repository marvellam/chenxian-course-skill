---
name: chenxian-course-outline
description: 更新陈衔中国美术史课程大纲，从已授权飞书内容生成可编辑母版和第06张大纲图，检查排版后按项目配置交付；全套详情页仅在明确要求时导出。
---

# 中国美术史课程大纲更新 Skill

本 Skill 适用于任何支持本地工具调用的 AI Agent（Claude Code、Cursor、Windsurf 等）。
在开始操作前，请先完整读取本文件。

---

## 这个工具做什么

从飞书多维表格读取最新课程大纲 → 与现有内容对比 → 生成可视化预览 → 确认后导出大纲图片 → 复制到 NAS。

**范围：只负责课程大纲部分（详情页第06张）的日常更新。** 完整详情页的重新导出由 `scripts/export_detail_v1.py` 单独完成，不属于日常流程。

全程不需要同事手动编辑任何 HTML、JSON 或代码。

---

## 目录结构

```
course-skill/
├── SKILL.md                  ← 本文件，Agent 操作手册
├── README.md                 ← 人类阅读的安装说明
├── package-version.txt       ← 当前包版本号
├── requirements.txt          ← Python 依赖
├── install.bat               ← 一键安装脚本（Windows 双击运行）
├── fonts/                    ← 随包字体（SIL 协议）
├── scripts/                  ← 排版与导出脚本
│   ├── build_outline_editable.py
│   ├── prepare_outline_elements.py
│   ├── export_detail_v1.py
│   ├── typography.py         ← 两条导出路径共享的字体与标题定位
│   └── verify_layout.py      ← 检查真实导出像素与文案
├── assets/                   ← 配图素材（原画裁切源等）
└── output/
    ├── outline-editable-v1/  ← 大纲模板目录
    │   ├── content.json      ← 当前确认文案（文字唯一来源）
    │   └── assets/           ← 预生成篇章头图
    └── detail-entry-v1/      ← 完整详情页母版
        └── 课程入口_可编辑母版.html
```

---

## 飞书表格信息

- 表格地址：https://i0as0i80h06.feishu.cn/base/NdhRbJtUNak6KEsTmDRcpQF4nmc
- 大纲结构：序章（2项）+ 山水篇（10讲）+ 花鸟篇（10讲）+ 人物篇（4讲）
- 读取时使用当前登录用户自己的飞书身份，不使用任何共享 token

---

## 日常操作流程

### 第一步：读取飞书最新大纲，检查变动

1. 通过飞书 MCP 或已授权的飞书连接，读取上方表格地址的最新内容
2. 读取 `output/outline-editable-v1/content.json`，作为"当前已确认内容"
3. 对比两者，列出所有变动项：
   - 格式：`[篇章] 第N讲 / 序章` — 旧内容 → 新内容（或"新增"/"已删除"）
   - 空白或明显未完成的条目（title 为空、含"待定""TBD""？"等）**不列为变动**，保留原稿
4. 明确告知哪些条目因为未完成而跳过
5. **等待用户确认**，用户说"可以更新"后再进行第二步

### 第二步：更新 content.json

按用户确认的变动，更新 `output/outline-editable-v1/content.json`：

**数据保护规则（不得违反）：**
- 只更新已填写完整的条目
- 空白或未完成的条目保留原文，不覆盖、不清空
- `"3大系列24章节"` 表述固定，不根据表格行数自动修改
- 篇章数量（山水10讲、花鸟10讲、人物4讲）固定，不根据表格记录数改变
- `outline_source.revision` 更新为本次飞书表格的修订版本号
- `outline_source.checked_date` 更新为今日日期

### 第三步：生成预览

在 `course-skill/` 目录下运行：

```
python scripts/build_outline_editable.py
```

脚本会输出：
- `output/outline-editable-v1/课程大纲_1_山水篇.png`（含序章）
- `output/outline-editable-v1/课程大纲_2_花鸟篇.png`
- `output/outline-editable-v1/课程大纲_3_人物篇.png`
- `output/outline-editable-v1/课程大纲_三篇合并_YYYYMMDD.png`（三篇合并，1080px宽）
- `output/outline-editable-v1/课程大纲与须知_可编辑母版_微信小店版.html`
- `output/outline-editable-v1/课程大纲与须知_可编辑母版_小红书版.html`
- 各篇 `_390宽预览.png`（手机宽度参考）

**请用浏览器打开 HTML 文件预览**，拖动窗口边缘至约 390px 宽可模拟手机效果。PNG 文件是排版校验图，与 HTML 共用同一份文案和字号参数，但浏览器字体渲染与 Pillow 合成在 1-2px 级别有差异，导出以 PNG 为准。

先运行 `python scripts/verify_layout.py`，检查简体字体、标题框内留白与大纲文字回读，再目视检查生成的 PNG（含390px预览）。检查失败时先定位原因，不将该图作为合格预览或交付图。

告知用户：预览文件已生成，请检查内容和排版，确认后告知是否导出。

### 第四步：确认导出大纲图

用户确认预览无误后，将三篇合并大纲图复制到本机交付目录：

`build_outline_editable.py` 已在上一步生成：
- `output/outline-editable-v1/课程大纲_三篇合并_YYYYMMDD.png`（1080px 宽，三篇含序章合并）
- 各篇单独 PNG 和 390px 预览图

这张合并图即为详情页第 06 张的更新来源，不需要重新导出完整详情页的其余 7 张。

### 第五步：复制到 NAS

大纲图生成后，读取 `config.json` 中的 `nas_base` 字段，拼上本次版本目录名（例如 `第一版修订N_YYYYMMDD`），构成完整目标路径。

默认 NAS 路径（一艺之间企业网盘，`\\172.16.5.11`，盘符 `Z:`）：
```
Z:\图片\1.课程\2026_陈衔中国美术史\1 详情页\第一版修订N_YYYYMMDD
```

将以下文件复制到上述目录：
- `output/outline-editable-v1/课程大纲_三篇合并_YYYYMMDD.png`（大纲合并图，替换第06张）
- `output/outline-editable-v1/课程大纲_1_山水篇.png`
- `output/outline-editable-v1/课程大纲_2_花鸟篇.png`
- `output/outline-editable-v1/课程大纲_3_人物篇.png`
- `output/outline-editable-v1/content.json`（文案备份）

注意事项：
- 如果目标路径已存在，先告知用户再确认
- 如果 `Z:` 不可达，提示用户检查 NAS 连接，或告知实际盘符，不要静默失败
- 如果用户的盘符与 `config.json` 不同，按用户提供的路径操作，并提示更新 `config.json`
- 旧版本目录保留，不覆盖

---

## 固定设计规则（不得修改）

以下参数是已确认的设计，不根据内容重新判断，也不提交用户选择：

- 画布宽度：1080px，高度随内容自动增加，不压缩字号
- 序章：位于"课程大纲"标题之后、山水篇之前，标签44px Bold，题目48px Bold，行高68px
- 讲题：44px；含分节的讲题加粗，分节42px 行高62px
- 序章和分节题目前加小圆点（独立于文字，换行对齐文字左沿）
- 篇章配图：原画素材 SVG 裁切，不生成仿古画，不加装饰印章
- 字体：思源黑（正文）+ 思源宋（篇章标题）
- 思源黑TTC须明确选择简体中文SC字面；随包字体中为index=2，HTML优先使用Source Han Sans SC。
- 四字框内小标题统一使用思源宋Bold、52px，456×80框体；文字按共享行框基线定位，不能沿用正文的字形顶部定位。山水篇等无框篇章标题仍使用原Heavy字重。
- 领取课程与课程须知的切图边界取框体位置，不根据文字top反推；详见共享排版代码与核验脚本。
- 底色：`#f1ebdf`，主文字：`#46534d`，标题：`#304e46`
- 当前图库权益：60张经典名作
- 两平台各8张，06大纲图为三篇含序章合并

---

## 错误处理

| 情况 | 处理方式 |
|------|----------|
| 飞书读取失败 | 告知用户，请求重新授权后重试；不使用本地旧快照替代 |
| 字体找不到 | 提示检查 `fonts/` 目录或重新安装；不跳过字体错误 |
| 飞书条目为空或含"待定" | 跳过该条目，保留原稿，在变动报告中注明 |
| 标题变长导致排版溢出 | `build_outline_editable.py` 自动增加画布高度，属正常行为 |
| NAS 路径不可写 | 告知用户检查 NAS 连接和权限，不重试写入 |
| 导出时脚本报错 | 完整显示错误信息，不猜测原因，等待用户指示 |

---

## 版本管理

`package-version.txt` 记录当前包版本。每次从 GitHub 拉取新版后，版本号会更新。
如果有人告知包有更新，请从 GitHub 重新克隆或 `git pull`。

GitHub仓库是本工具脚本与操作规则的统一维护来源；Claude、Codex等均在同一版本上继续维护。迁入其他制作目录已验证的修复时，保留本包的相对路径、随包字体与NAS配置，不能直接用本机专用脚本覆盖。

### 维护排版或明确要求全套导出时

先运行构建器，再运行 `python scripts/export_detail_v1.py --output detail-export-版本日期 --version 版本名称`，最后运行 `python scripts/verify_layout.py --export output/detail-export-版本日期`。旧构建结果缺少框体位置时须重建，不能通过猜测偏移继续切图。

除自动核验外，目视检查03/04/06/07/08各标题及两平台最终成图。仅改标题时，使用相同文案和字体配置比较无损PNG：变化应限于标题区，正文、尺寸和无关模块不变；字体修复则单独核对字形及换行。修改脚本不能顺带覆盖当前确认文案。核验通过后才提交版本；仅更新大纲的日常流程仍只交付第06张。
