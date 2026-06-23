# 错误类型

所有错误继承基类 `Vid2TextError`，通过 `exit_code` 属性控制进程退出码。

CLI 层捕获后取 `exit_code` 作为退出码，`str(e)` 输出到 STDERR。

| 错误类型 | 基类 | exit_code | 触发条件 |
|----------|------|-----------|----------|
| `UserError` | `Vid2TextError` | 1 | 无效链接、不含可识别的 BV 号 |
| `NetworkError` | `Vid2TextError` | 2 | B站 API 请求失败、音频下载失败 |
| `TranscodeError` | `Vid2TextError` | 2 | 转码失败 |
| `ModelError` | `Vid2TextError` | 2 | 模型文件损坏、推理异常、不支持的操作系统 |
