# Vid2Text MVP Skill 产物化与真实链路验证计划

> **For agentic workers:** 本计划以 `.skill` 打包产物为最终验收标准。`.skill` 内部只包含 `vid2text.exe`（单文件、内嵌 ffmpeg）和 `SKILL.md`。计划文档仅描述任务目标、文件、验收标准和命令，具体代码在任务执行时实现。

**Goal:** 用 PyInstaller 把 MVP 源码打包为单文件 exe（内嵌 ffmpeg），再把 exe + SKILL.md 打包成 `.skill` 技能包，最后用真实 B站视频验证 `.skill` 产物能独立运行。

**Architecture:** 源码经 PyInstaller 构建为 `dist/vid2text.exe`（单文件，`--onefile`，内嵌 ffmpeg.exe，收集 funasr_onnx/modelscope/onnxruntime 隐藏导入）。然后 `scripts/build_skill.py` 把 `vid2text.exe` 和 `SKILL.md` 压缩为 `dist/vid2text-{version}.skill`。`scripts/e2e_test.py` 解压 `.skill` 到临时目录，直接运行 `vid2text.exe` 完成真实链路验证。

**Tech Stack:** Python 3.10+、PyInstaller、funasr_onnx、modelscope、onnxruntime、ffmpeg、B站 Web API。

---

## 0. 范围与边界

**包含：**
- 更新 `SKILL.md`：匹配 MVP 设计（B站单平台、funasr_onnx、纯文本 STDOUT、exe 入口）。
- 安装/确认 PyInstaller 环境。
- 编写 PyInstaller 配置（`.spec` 或命令行参数）：单文件、内嵌 ffmpeg、收集隐藏导入。
- 构建 `vid2text.exe`。
- 编写 `scripts/build_skill.py`：把 `vid2text.exe` + `SKILL.md` 打成 `.skill` zip 包。
- 编写 `scripts/e2e_test.py`：解压 `.skill`，直接运行 exe 验证 help、错误 URL、真实二舅视频转写。
- 运行 e2e 测试，修复打包/运行问题直到通过。

**不包含：**
- 缓存模块（按 MVP 边界保留源码）。
- CI 发布工作流。
- GUI、翻译、摘要、JSON 输出、SRT/VTT 字幕。
- 把模型文件打包进 `.skill`（首次运行仍从 ModelScope 下载）。

**环境前提：**
- Python >= 3.10。
- 本机 PATH 中有 ffmpeg（仅用于打包时把 ffmpeg.exe 复制进 exe）。
- 首次真实运行会从 ModelScope 下载约 1.2GB 模型到 `~/.cache/modelscope/`。
- 网络可访问 B站 API 与 ModelScope。

---

## 1. 文件结构

```
vid2text/                  # 已存在，MVP 实现
scripts/                   # 新增
├── build_skill.py         # 把 exe + SKILL.md 打包成 .skill
└── e2e_test.py            # 真实端到端测试（直接运行 exe）
vid2text.spec              # 新增：PyInstaller 配置
SKILL.md                   # 新增/更新
pyproject.toml             # 已存在（打包时仍用它安装依赖）
README.md                  # 已存在，可同步更新
```

**产物结构（zip 内部）：**
```
vid2text-0.1.0.skill
├── SKILL.md
└── vid2text.exe
```

---

## 2. 执行约定

- 每个任务独立可交付，任务结束后提交。
- 不写代码注释（项目规则）。
- 真实链路测试可能耗时（模型下载），作为最终验证。
- 计划文档不放具体代码实现，只描述目标与验收标准。

---

## Task 1: 更新 SKILL.md 以匹配 exe 形态 MVP

**Files:**
- Create: `SKILL.md`

**要求：**
- 顶部 YAML frontmatter 包含 `name: "vid2text"` 和 `description`。
- description 说明：B站视频转纯文本、无需 Python、基于 funasr_onnx。
- 正文包含：能力描述、触发场景、先决条件（Windows、ffmpeg 已内嵌、网络）、命令格式、输出契约、退出码表、典型用法（二舅视频 URL）、约束。
- 典型用法命令示例直接调用 `vid2text.exe <url>`。
- 退出码表：0 成功 / 1 用户输入错误 / 2 系统错误。

**验收：**
- Run: `Get-Content SKILL.md | Select-Object -First 5`
- Expected: 包含 `name: "vid2text"` 与 `description:`。

**提交：**
```bash
git add SKILL.md
git commit -m "docs: update SKILL.md for packaged exe artifact"
```

---

## Task 2: 安装并验证 PyInstaller 环境

**Files:**
- 无新文件，仅安装依赖。

**要求：**
- 安装 PyInstaller：`pip install pyinstaller`。
- 确认 `pyinstaller --version` 可执行。
- 确认本机 `ffmpeg.exe` 存在（打包时需要复制进 exe），记录其路径。

**验收：**
- Run: `pyinstaller --version`
- Expected: 输出版本号，无报错。
- Run: `Get-Command ffmpeg`
- Expected: 显示 ffmpeg.exe 路径。

**提交：**
- 本任务不产生项目文件变更，不提交；或如有 `pyproject.toml` 追加 build 依赖则单独提交。

---

## Task 3: 编写 PyInstaller 配置

**Files:**
- Create: `vid2text.spec`

**要求：**
- 以 `vid2text/cli.py` 为入口脚本。
- 输出单文件 exe（`--onefile`）。
- 通过 `binaries` 把本机 `ffmpeg.exe` 打包进 exe 根目录。
- 在 `hiddenimports` 中显式声明 `funasr_onnx.paraformer_bin`、`funasr_onnx.vad_bin`、`funasr_onnx.punc_bin`、`onnxruntime`、`onnxruntime.capi`。
- 使用 `--collect-all funasr_onnx` 和 `--collect-all modelscope`（或 spec 中等价配置），确保运行时能找到模块数据文件。
- 控制台程序（`console=True`），因为工具依赖 STDOUT/STDERR。

**验收：**
- Run: `python -m py_compile vid2text.spec`
- Expected: 无输出（语法正确）。
- Run: `pyinstaller vid2text.spec`
- Expected: 成功生成 `dist/vid2text.exe`。

**提交：**
```bash
git add vid2text.spec
git commit -m "build: add pyinstaller spec for single-file exe with embedded ffmpeg"
```

---

## Task 4: 验证 exe 可独立运行

**Files:**
- 无新文件，仅执行验证。

**要求：**
- 运行 `dist/vid2text.exe --help`，确认 exe 能启动、显示帮助。
- 运行 `dist/vid2text.exe https://youtube.com/watch?v=abc`，确认返回非 0 退出码。
- 若出现隐藏导入错误、模块数据缺失等问题，回到 Task 3 调整 spec，重新打包，直到 help 正常。

**验收：**
- Run: `dist/vid2text.exe --help`
- Expected: 输出 usage 与描述，退出码 0。

---

## Task 5: 创建 build_skill.py 打包 .skill

**Files:**
- Create: `scripts/build_skill.py`

**要求：**
- 脚本从项目根目录读取 `dist/vid2text.exe` 和 `SKILL.md`。
- 打包为 `dist/vid2text-{__version__}.skill`（zip 格式，DEFLATED）。
- zip 内只包含两个文件：`SKILL.md`、`vid2text.exe`。
- 打包后校验 zip 内文件列表与预期一致。
- 打印构建成功的产物路径。

**验收：**
- Run: `python scripts/build_skill.py`
- Expected: 输出 `Built: dist/vid2text-0.1.0.skill`，无断言错误。
- Run: `python -c "import zipfile; z=zipfile.ZipFile('dist/vid2text-0.1.0.skill'); print('\n'.join(z.namelist()))"`
- Expected: 仅列出 `SKILL.md` 和 `vid2text.exe`。

**提交：**
```bash
git add scripts/build_skill.py
git commit -m "build: package exe and SKILL.md into .skill artifact"
```

---

## Task 6: 新增 e2e 测试脚本（真实产物 + 真实链路）

**Files:**
- Create: `scripts/e2e_test.py`

**要求：**
- 若 `dist/vid2text-0.1.0.skill` 不存在，自动调用 `scripts/build_skill.py` 构建。
- 创建临时目录，解压 `.skill` 到该目录。
- 在解压目录中执行以下测试：
  1. `vid2text.exe --help`：期望退出码 0，输出包含"转写"。
  2. `vid2text.exe https://youtube.com/watch?v=abc`：期望退出码非 0。
  3. `vid2text.exe "https://www.bilibili.com/video/BV1MN4y177PB?vd_source=f4d5561279916bfa620a32d590265535"`：期望退出码 0，STDOUT 非空。
- 每个阶段打印命令与关键输出，失败时打印 STDOUT/STDERR 便于诊断。

**验收：**
- Run: `python -m py_compile scripts/e2e_test.py`
- Expected: 无输出（语法正确）。

**提交：**
```bash
git add scripts/e2e_test.py
git commit -m "test: add e2e test script against real .skill exe artifact"
```

---

## Task 7: 运行 e2e 测试并修复问题

**Files:**
- 无新文件，只执行与观察。

**要求：**
- Run: `python scripts/e2e_test.py`
- 观察解压 `.skill`、运行 exe、首次下载模型、真实转写二舅视频的完整流程。
- 记录退出码、STDOUT 前 2000 字符、STDERR 最后 2000 字符、转写文本长度。
- 若失败，分析失败阶段：
  - exe 启动失败/隐藏导入错误 → 回到 Task 3 调整 PyInstaller 配置。
  - ffmpeg 未找到 → 确认 ffmpeg 已内嵌，检查 `transcoder.py` 的 `sys._MEIPASS` 路径解析。
  - B站 API/音频下载失败 → 检查 downloader 逻辑。
  - 模型下载/加载失败 → 检查 modelscope/funasr_onnx 相关隐藏导入。
  - ASR 推理失败 → 检查 asr.py 与模型兼容性。
- 循环修复直到 e2e 通过。

**验收：**
- 成功：退出码 0，STDOUT 非空，所有断言通过。
- 失败：明确失败阶段与错误信息，回到对应任务修复。

---

## Task 8: 同步 README.md

**Files:**
- Modify: `README.md`

**要求：**
- 精简为标题、用途、下载 `.skill` 后解压运行 exe 的示例、依赖（Windows、首次模型下载）、License。
- 不展开架构细节。

**提交：**
```bash
git add README.md
git commit -m "docs: sync README with packaged exe usage"
```

---

## 3. 自检

**规格覆盖：**
- SKILL 元数据更新 → Task 1 ✅
- PyInstaller 单文件 exe + 内嵌 ffmpeg → Task 2/3/4 ✅
- .skill 产物构建 → Task 5 ✅
- 真实产物端到端验证 → Task 6/7 ✅
- README 同步 → Task 8 ✅

**占位符扫描：** 无 TODO/TBD，计划文档仅描述目标、文件、验收标准与命令。

**一致性检查：**
- 产物路径 `dist/vid2text-{__version__}.skill` 在 build 和 e2e 中一致。
- e2e 直接运行解压后的 `vid2text.exe`，与 SKILL.md 中描述的用法一致。

---

## 4. 执行方式

本计划采用**子代理逐任务执行**。每个任务完成后由主会话审查，通过后再进入下一任务。Task 3/4/7 涉及 PyInstaller 打包与真实链路运行，可能需多次迭代，单独作为关键验证任务。
