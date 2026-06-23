# CLI 入口

`cli.py` 是唯一命令行入口，基于 click 框架。

## 命令结构

单一命令，无子命令组：

```
vid2text <url|bvid>
vid2text --version
```

- **`vid2text <url|bvid>`** — 接受完整 B站链接或纯 BV 号，执行完整流水线（下载 → 转码 → ASR → 输出）。使用 `tempfile.TemporaryDirectory()` 存放中间文件，进程退出时自动清理。
- **`vid2text --version`** — 输出版本号，不做任何处理。

## 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 成功 |
| 1 | 用户错误（无效链接、无 BV 号、缺少参数） |
| 2 | 系统错误（网络、转码、ASR 推理失败） |

错误信息输出到 STDERR，转写文本输出到 STDOUT。
