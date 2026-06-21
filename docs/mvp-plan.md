# Vid2Text MVP Skill 产物化与真实链路验证计划

> **For agentic workers:** 本计划以 `.skill` 打包产物为最终验收标准。`.skill` 内部包含 Python 源码（`vid2text/`）、`pyproject.toml` 和 `SKILL.md`。Agent 解压后执行 `pip install -e .` 即可使用。计划文档仅描述任务目标、文件、验收标准和命令，具体代码在任务执行时实现。

**Goal:** 用源码直接分发 `.skill` 技能包，再用真实 B站视频验证 `.skill` 产物能独立运行。

**Architecture:** Python 层负责 B站下载和 ffmpeg 转码，ASR 推理通过 subprocess 调用预编译的 SenseVoice.cpp 二进制完成。`.skill` 产物包含 Python 源码、C 二进制、GGUF 模型，解压后 pip install 即可使用。

**Tech Stack:** Python 3.10+、SenseVoice.cpp GGUF + C 二进制 subprocess 调用、click、ffmpeg、B站 Web API。

---

## 0. 范围与边界

**包含：**
- 更新 `SKILL.md`：匹配源码分发形态（pip install 安装）。
- 编写 `scripts/build_skill.py`：把源码 + `SKILL.md` 打成 `.skill` zip 包。
- 编写 `scripts/e2e_test.py`：解压 `.skill`，pip install，运行 vid2text 验证 help、错误 URL、真实 B站视频转写。
- 运行 e2e 测试，修复问题直到通过。

**不包含：**
- 缓存模块（按 MVP 边界保留源码）。
- CI 发布工作流。
- GUI、翻译、摘要、JSON 输出、SRT/VTT 字幕。
- PyInstaller 打包 exe。

**环境前提：**
- Python >= 3.10。
- 本机 PATH 中有 ffmpeg。
- 模型已内嵌于 .skill 产物中（174MB GGUF），无需额外下载
- 网络可访问 B站 API 与 ModelScope。

---

## 1. 文件结构

```
vid2text/                  # 已存在，MVP 实现
├── __init__.py
├── asr.py                 # SenseVoice.cpp 推理（subprocess 调用 C 二进制）
├── cli.py
├── downloader.py
├── errors.py
├── transcoder.py
bin/                       # 预编译 C 二进制（按平台分包）
├── darwin-arm64/sense-voice
└── linux-x64/sense-voice
models/                    # GGUF 模型
└── sense-voice-small-q4_k.gguf
scripts/                   # 新增
├── build_skill.py         # 把源码 + SKILL.md + pyproject.toml 打包成 .skill
└── e2e_test.py            # 真实端到端测试（解压 .skill → pip install → vid2text）
SKILL.md                   # 已创建
pyproject.toml             # 已存在
README.md                  # 已存在，可同步更新
```

**产物结构（zip 内部）：**
```
vid2text-0.1.0.skill
├── SKILL.md
├── pyproject.toml
├── vid2text/
│   ├── __init__.py
│   ├── asr.py
│   ├── cli.py
│   ├── downloader.py
│   ├── errors.py
│   └── transcoder.py
├── bin/
│   ├── darwin-arm64/sense-voice
│   └── linux-x64/sense-voice
└── models/
    └── sense-voice-small-q4_k.gguf
```

---

## 2. 执行约定

- 每个任务独立可交付，任务结束后提交。
- 不写代码注释（项目规则）。
- 真实链路测试可能耗时（模型下载），作为最终验证。
- 计划文档不放具体代码实现，只描述目标与验收标准。

---

## Task 1: 更新 SKILL.md 以匹配源码分发型态

**Files:**
- Modify: `SKILL.md`

**要求：**
- 顶部 YAML frontmatter 包含 `name: "vid2text"` 和 `description`。
- description 说明：B站视频转纯文本、基于 funasr_onnx、pip install 后使用。
- 正文包含：能力描述、触发场景、**安装步骤**（`pip install -e .`）、先决条件（Python >= 3.10、ffmpeg）、命令格式、输出契约、退出码表、典型用法、约束。
- 典型用法命令示例直接调用 `vid2text <url>`。

**验收：**
- 文件前 5 行包含 `name: "vid2text"` 与 `description:`。

**提交：**
```bash
git add SKILL.md
git commit -m "docs: update SKILL.md for source-based .skill distribution"
```

---

## Task 2: 创建 build_skill.py 打包 .skill

**Files:**
- Create: `scripts/build_skill.py`

**要求：**
- 脚本从项目根目录读取 `vid2text/`、`SKILL.md`、`pyproject.toml`。
- 打包为 `dist/vid2text-{__version__}.skill`（zip 格式，DEFLATED）。
- zip 内包含：`SKILL.md`、`pyproject.toml`、`vid2text/` 目录下所有 `.py` 文件。
- 打包后校验 zip 内文件列表与预期一致。
- 打印构建成功的产物路径。

**验收：**
- Run: `python scripts/build_skill.py`
- Expected: 输出 `Built: dist/vid2text-0.1.0.skill`，无异常。
- Run: `python -c "import zipfile; z=zipfile.ZipFile('dist/vid2text-0.1.0.skill'); print('\n'.join(z.namelist()))"`
- Expected: 列出 `SKILL.md`、`pyproject.toml` 和 `vid2text/` 下所有 py 文件。

**提交：**
```bash
git add scripts/build_skill.py
git commit -m "build: package source and SKILL.md into .skill artifact"
```

---

## Task 3: 新增 e2e 测试脚本

**Files:**
- Create: `scripts/e2e_test.py`

**要求：**
- 若 `dist/vid2text-0.1.0.skill` 不存在，自动调用 `scripts/build_skill.py` 构建。
- 创建临时目录，解压 `.skill` 到该目录。
- 在解压目录中执行 `pip install -e .` 安装依赖和 CLI 入口。
- 执行以下测试：
  1. `vid2text --help`：期望退出码 0，输出包含"转写"。
  2. `vid2text https://youtube.com/watch?v=abc`：期望退出码非 0。
  3. `vid2text "https://www.bilibili.com/video/BV1MN4y177PB?vd_source=f4d5561279916bfa620a32d590265535"`：期望退出码 0，STDOUT 非空。
- 每个阶段打印命令与关键输出，失败时打印 STDOUT/STDERR 便于诊断。

**验收：**
- Run: `python -m py_compile scripts/e2e_test.py`
- Expected: 无输出（语法正确）。

**提交：**
```bash
git add scripts/e2e_test.py
git commit -m "test: add e2e test script against real .skill artifact"
```

---

## Task 4: 运行 e2e 测试并修复问题

**Files:**
- 无新文件，只执行与观察。

**要求：**
- Run: `python scripts/e2e_test.py`
- 观察解压 `.skill`、pip install、首次下载模型、真实转写二舅视频的完整流程。
- 记录退出码、STDOUT 前 2000 字符、STDERR 最后 2000 字符、转写文本长度。
- 若失败，分析失败阶段：
  - pip install 失败 → 检查 pyproject.toml 依赖是否完整。
  - ffmpeg 未找到 → 确认 ffmpeg 在 PATH 中。
  - B站 API/音频下载失败 → 检查 downloader 逻辑。
  - 模型下载/加载失败 → 检查 modelscope/funasr_onnx 相关导入。
  - ASR 推理失败 → 检查 asr.py 与模型兼容性。
- 循环修复直到 e2e 通过。

**验收：**
- 成功：退出码 0，STDOUT 非空，所有断言通过。
- 失败：明确失败阶段与错误信息，回到对应任务修复。

---

## Task 5: 同步 README.md

**Files:**
- Modify: `README.md`

**要求：**
- 精简为标题、用途、下载 `.skill` 后解压并 pip install 的示例、依赖（Python 3.10+、ffmpeg、首次模型下载）、License。
- 不展开架构细节。

**提交：**
```bash
git add README.md
git commit -m "docs: sync README with source-based .skill usage"
```

---

## 3. 自检

**规格覆盖：**
- SKILL.md 更新 → Task 1 ✅
- .skill 产物构建 → Task 2 ✅
- 真实产物端到端验证 → Task 3/4 ✅
- README 同步 → Task 5 ✅

**占位符扫描：** 无 TODO/TBD，计划文档仅描述目标、文件、验收标准与命令。

**一致性检查：**
- 产物路径 `dist/vid2text-{__version__}.skill` 在 build 和 e2e 中一致。
- e2e 解压后执行 `pip install -e .`，与 SKILL.md 中描述的安装步骤一致。

---

## 4. 执行方式

本计划采用**子代理逐任务执行**。每个任务完成后由主会话审查，通过后再进入下一任务。Task 2/4 涉及打包逻辑与真实链路运行，可能需迭代，单独作为关键验证任务。
