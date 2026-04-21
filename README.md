# 剪切板管理器

一款跨平台剪切板管理工具，支持 Windows 和 macOS（M系列芯片），提供历史记录、分类管理、快捷键操作和开机自启动。注：瞎写的纯练手，就当给github中在添加依托就好

## 功能特性

- **剪切板历史记录** - 自动保存所有复制内容，支持最多100条历史
- **智能分类** - 自动识别文本、链接、文件路径、图片、代码等类型
- **图片支持** - 支持截图/图片的复制粘贴，自动预览
- **文件支持** - 支持文件/文件夹的复制粘贴
- **实时搜索** - 快速搜索历史记录
- **快捷键操作** - Windows: `Ctrl+Shift+V` / macOS: `Cmd+Shift+V`
- **系统托盘** - 最小化到托盘，后台静默运行
- **开机自启** - Windows 注册表 / macOS LaunchAgent
- **固定功能** - 重要内容可固定置顶，不会被清空
- **深色模式** - 支持浅色/深色主题切换
- **字体缩放** - 设置中可调节字体大小
- **本地存储** - 数据保存在本地，保护隐私

## 安装

### 环境要求

- Python 3.8+
- Windows 10/11 或 macOS (Apple Silicon / Intel)

### 第一步：安装依赖库

本项目依赖以下第三方库，需要额外安装（Python 自带的标准库无需安装）：

| 库 | 平台 | 用途 |
|----|------|------|
| pyperclip | 全平台 | 剪切板文本操作 |
| keyboard | Windows | 全局快捷键 |
| pynput | macOS/Linux | 全局快捷键 |
| pystray | 全平台 | 系统托盘 |
| Pillow | 全平台 | 图标生成、图片处理 |

**一键安装全部依赖：**

```bash
pip install -r requirements.txt
```

> `requirements.txt` 已按平台条件配置，Windows 只会安装 `keyboard`，macOS/Linux 只会安装 `pynput`，无需手动筛选。

**如果需要逐个安装，执行以下命令：**

Windows：
```bash
pip install pyperclip keyboard pystray Pillow
```

macOS / Linux：
```bash
pip install pyperclip pynput pystray Pillow
```

### 第二步：运行程序

**方式一：启动脚本（推荐，无终端窗口）**

| 平台 | 操作 |
|------|------|
| Windows | 双击 `start.vbs` |
| macOS | 终端执行 `bash start.sh`，或赋予执行权限后双击 `start.sh` |

启动后程序在后台运行，无需保持终端窗口，关闭终端不影响程序。

**方式二：命令行启动（调试用）**

```bash
python main.py
```

> 此方式会显示终端窗口，关闭终端程序将退出，适合调试时使用。

## 使用说明

### 快捷键

| 平台      | 快捷键            | 功能       |
| ------- | -------------- | -------- |
| Windows | `Ctrl+Shift+V` | 显示/隐藏主窗口 |
| macOS   | `Cmd+Shift+V`  | 显示/隐藏主窗口 |
| 通用      | `Escape`       | 隐藏窗口     |

### 操作说明

1. **复制内容** - 程序会自动监听并保存剪切板内容
2. **查看历史** - 按快捷键或点击托盘图标
3. **搜索** - 在搜索框输入关键词实时过滤
4. **分类筛选** - 点击分类标签查看特定类型内容
5. **复制** - 点击历史记录卡片中的"复制"按钮
6. **固定** - 点击"固定"将重要内容置顶
7. **删除** - 点击"删除"移除单条记录
8. **清空** - 点击"清空历史"清除所有记录（固定内容保留）
9. **切换主题** - 点击右上角月亮/太阳图标
10. **设置** - 点击"设置"配置开机自启、字体大小等选项

### 日志文件

程序运行日志保存在 `logs/` 目录下，文件名格式为 `YYYYMMDD.log`（如 `20260421.log`）。遇到问题时可查看日志定位原因。

## 配置文件

配置文件位于 `config.json`：

```json
{
    "max_history": 100,
    "theme": "light",
    "hotkey": "ctrl+shift+v",
    "autostart": true,
    "window_width": 500,
    "window_height": 600,
    "check_interval": 500,
    "font_scale": 1.0
}
```

| 配置项             | 说明              | 默认值                                    |
| --------------- | --------------- | -------------------------------------- |
| max\_history    | 最大历史记录数         | 100                                    |
| theme           | 主题 (light/dark) | light                                  |
| hotkey          | 全局快捷键           | ctrl+shift+v (Win) / cmd+shift+v (Mac) |
| autostart       | 开机自启动           | true                                   |
| window\_width   | 窗口宽度            | 500                                    |
| window\_height  | 窗口高度            | 600                                    |
| check\_interval | 剪切板检测间隔(ms)     | 500                                    |
| font\_scale     | 字体缩放比例          | 1.0                                    |

## 项目结构

```
clipboard-app/
├── main.py                     # 主程序入口
├── start.vbs                   # Windows 启动脚本（无终端）
├── start.sh                    # macOS/Linux 启动脚本（后台运行）
├── requirements.txt            # 依赖文件
├── config.json                 # 配置文件
├── core/
│   ├── clipboard_monitor.py    # 剪切板监听（跨平台后端）
│   ├── storage.py              # 数据存储
│   ├── hotkey.py               # 快捷键管理（跨平台后端）
│   └── autostart.py            # 开机自启（跨平台后端）
├── gui/
│   ├── styles.py               # 样式与主题
│   ├── main_window.py          # 主窗口
│   ├── tray.py                 # 系统托盘
│   └── components/
│       ├── search_bar.py       # 搜索栏
│       ├── category_tabs.py    # 分类标签
│       ├── history_card.py     # 历史卡片
│       └── action_bar.py       # 操作栏
└── utils/
    ├── platform_utils.py       # 平台检测工具
    ├── content_type.py         # 内容类型识别
    └── helpers.py              # 工具函数
```

## 跨平台架构

| 模块    | Windows            | macOS / Linux                   |
| ----- | ------------------ | ------------------------------- |
| 剪切板读写 | Win32 API (ctypes) | osascript / pyperclip           |
| 全局快捷键 | keyboard 库         | pynput 库                        |
| 开机自启  | 注册表 (winreg)       | LaunchAgent (plist)             |
| 数据目录  | 程序目录/data          | \~/Library/Application Support/ |
| 系统字体  | SegoeUI            | Helvetica Neue                  |

## 许可证

MIT License
