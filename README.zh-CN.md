# token-tracker

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Release](https://img.shields.io/github/v/release/YOUR_GITHUB_USERNAME/token-tracker?display_name=tag)](https://github.com/YOUR_GITHUB_USERNAME/token-tracker/releases)
[![License](https://img.shields.io/badge/License-Unspecified-lightgrey)](./LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)](https://www.microsoft.com/windows)

语言: [English](./README.md) | 简体中文

`token-tracker` 是一个本地离线 Token 统计工具，用于分析 AI 编码助手日志，并按天展示 token 趋势。

当前版本重点支持 Codex 日志；后续会扩展到 Claude Code、Cursor 等工具。

## 功能特性

- 多路径扫描：支持添加多个目录/文件
- 按天聚合：总量、上传（Input）、下载（Output）
- 本地持久化：SQLite 保存路径和统计结果
- 多折线图：支持总量/上传/下载同时展示
- 悬浮提示：鼠标移动到点上显示明细
- 一键打包：Windows 单文件 `exe`

## 快速开始

### 1. 环境要求

- Windows 10/11
- Python 3.10+

```bat
python --version
```

### 2. 安装依赖

```bat
cd /d C:\path\to\token-tracker
python -m pip install -r requirements.txt
```

### 3. 本地运行

```bat
python token_tracker.py
```

或：

```bat
run.bat
```

### 4. 打包 EXE

```bat
build_exe.bat
```

产物：

```text
dist\token-tracker.exe
```

## 使用方法

1. 添加日志路径（添加目录/添加文件）。
2. 点击刷新统计，解析并聚合日志。
3. 勾选图表线条（总量/上传/下载）。
4. 鼠标移到折线点，查看该日详细数据。

## 当前解析字段

主要支持：

- `event_msg`
- `payload.type == token_count`
- `payload.info.total_token_usage`
- `payload.info.last_token_usage`

回退字段：

- `usage`
- `last_response.usage`

## 本地数据目录

默认路径：

```text
%APPDATA%\token-tracker\
```

文件：

- `config.json`：路径配置
- `tracker.db`：本地统计数据库

## 兼容迁移

如果旧版本使用过 `%APPDATA%\CodexTokenTracker\`，首次启动会自动迁移：

- `config.json`
- `tracker.db`

## 开发结构

- `token_tracker.py`：解析、存储、后端 API、应用启动
- `web/index.html`：页面结构
- `web/styles.css`：样式
- `web/app.js`：前端交互与图表绘制

## 规划（Roadmap）

- 更多日志来源适配
- Claude Code 适配
- Cursor 适配
- 多工具统一统计视图（对比/筛选）
- 更细粒度维度（会话/项目/模型）

## 开源发布提示

- 发布到 GitHub 后，将徽章中的 `YOUR_GITHUB_USERNAME/token-tracker` 改为你的真实仓库。
- 建议补充 `LICENSE` 文件，让许可证徽章生效。

## 贡献

欢迎提 Issue / PR。

