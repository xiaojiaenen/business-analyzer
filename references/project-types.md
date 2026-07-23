# 项目类型分析指南

每种项目类型的业务入口不同、搜索模式不同、流程追踪路径不同。本文档是 Phase 1 第二步「项目类型识别」的操作手册。

---

## 无数据库项目的分析路径（先看这个）

很多项目没有数据库（CLI 工具、SDK、游戏、纯计算库）。这类项目**跳过 Phase 2.0 数据库分析**，从代码维度直接入手：

| 项目类型 | 业务信源（替代数据库） | 核心分析对象 |
|---------|---------------------|------------|
| CLI 工具 | 命令参数 + README 示例 | 命令=业务操作，参数=业务输入 |
| 库 / SDK | 公开 API + 类型定义 + 示例代码 | 公开接口=业务能力，类型=业务实体 |
| 游戏 | 游戏模式 + 核心循环 + 经济系统 | 游戏模式=业务域，核心循环=业务流程 |
| 定时任务 | 调度配置 + 任务逻辑 | 任务=业务流程，调度=触发条件 |
| 桌面 GUI | UI 回调 + 菜单结构 | 按钮/菜单=业务操作 |

**无 DB 项目的 Phase 2 调整**：
- 跳过 `scripts/db-introspect.py` 和 `scripts/analyze-schema.py`
- "业务实体"从代码类型定义提取（struct/class/interface/数据类），不从表结构
- "状态机"从代码里的状态变量 + 状态校验逻辑提取，不从 ENUM 字段
- 其他维度（流程、规则、角色、领域）分析方法不变

**判断项目有无数据库**：
- 有 `CREATE TABLE` / ORM model / migration 文件 / `.env` 里的 DB 连接 → 有 DB
- 只有内存数据结构 / 文件存储 / 无持久化 → 无 DB，走本表路径

---

## 桌面 GUI 应用

**典型框架**：tkinter / customtkinter / PyQt / PySide / WPF / WinForms / Electron / Swing / JavaFX / GTK / wxWidgets

### 识别特征

- 目录中有 `gui_app.py` / `mainwindow.py` / `MainWindow.xaml` / `app.js`（Electron）
- 依赖中有 `tkinter` / `customtkinter` / `PyQt5` / `electron`
- 代码中有 `tk.Tk()` / `CTk()` / `QApplication` / `JFrame` / `BrowserWindow`

### 业务入口搜索

```bash
# Python tkinter / customtkinter
grep -rn "command=" --include="*.py"
grep -rn "CTkButton\|ttk.Button\|tk.Button" --include="*.py"
grep -rn "bind(" --include="*.py"
grep -rn "\.configure(command" --include="*.py"

# PyQt / PySide
grep -rn "clicked\.connect\|pressed\.connect\|triggered\.connect" --include="*.py"
grep -rn "QPushButton\|QAction\|QMenu" --include="*.py"

# Electron
grep -rn "ipcMain\.(on\|handle)" --include="*.js" --include="*.ts"
grep -rn "ipcRenderer\.(send\|invoke)" --include="*.js" --include="*.ts"

# WPF / WinForms (C#)
grep -rn "Button_Click\|MenuItem_Click\|OnClick" --include="*.cs"
grep -rn "EventHandler\|RoutedEventHandler" --include="*.cs"

# Java Swing / JavaFX
grep -rn "addActionListener\|setOnAction\|ActionEvent" --include="*.java"
```

### 流程追踪路径

```
UI 回调（button click / menu action）
  → Coordinator/Controller（协调业务逻辑）
  → Service（执行操作）
  → External（数据库/API/文件系统）
  → UI 更新（状态栏/表格刷新/弹窗）
```

### ERP-AutoBot 示例

```
CTkButton(command=self.on_import)     → 导入按钮
  → ImportController.import_excel()   → 读取 Excel
  → ImportValidationService.validate()  → 校验数据
  → DatabaseService.insert_invoice()  → 写入 SQLite
  → StatusBar.update("导入完成 15 条")  → UI 反馈
```

---

## CLI 工具

**典型框架**：argparse / click / typer / cobra / commander / clap / docopt

### 识别特征

- 代码中有 `add_argument` / `@click.command` / `cobra.Command`
- 顶层有 `if __name__ == "__main__"` 或 `func main()`
- 依赖中有 `click` / `typer` / `cobra` / `commander`

### 业务入口搜索

```bash
# Python
grep -rn "add_argument\|@click\.\(command\|option\)\|@app\.command" --include="*.py"

# Go
grep -rn "cobra\.Command\|\.Commands = " --include="*.go"

# Node.js
grep -rn "\.command(\|\.option(" --include="*.js" --include="*.ts"

# Rust
grep -rn "#\[clap\|\.arg(" --include="*.rs"
```

### 流程追踪路径

```
CLI 命令（$ tool do-something --flag）
  → 参数解析 + 校验
  → 核心逻辑
  → 副作用（文件/网络/数据库）
  → stdout 输出 / 退出码
```

---

## 游戏

**典型引擎**：Unity / Unreal Engine / Godot / pygame / Phaser / Bevy

### 识别特征

- 目录中有 `.unity` / `.uproject` / `project.godot` / `Assets/`
- 代码中有 `MonoBehaviour` / `AActor` / `Node` / `pygame.init`
- 依赖中有 `pygame` / `unity` / `godot`

### 游戏业务视角

游戏的核心"业务"是：
- **游戏模式**（主菜单、战斗、探索、建造）
- **核心循环**（玩家做什么→系统反馈→驱动下一步）
- **经济系统**（货币、物品、交易）
- **进度系统**（等级、成就、解锁）

### 入口搜索

```bash
# Unity (C#)
grep -rn "class.*MonoBehaviour\|class.*ScriptableObject" --include="*.cs"
grep -rn "SceneManager\|LoadScene" --include="*.cs"

# Godot
grep -rn "extends Node\|extends Area2D\|extends KinematicBody" --include="*.gd"

# pygame
grep -rn "pygame.init\|screen.*set_mode\|game_loop\|main_loop" --include="*.py"
```

---

## 库 / SDK

### 识别特征

- 无 `main()` 入口、无 GUI、无 HTTP server
- 有 `setup.py` / `package.json` 的 `main` 字段
- 有 `__init__.py` 导出 / `index.ts` re-export
- 有 API 文档 / typedoc / sphinx

### 分析策略

库的业务分析不是追踪"用户操作"，而是：
- **公开接口清单**（类/函数/方法列表）
- **数据模型**（输入类型、输出类型、核心数据结构）
- **使用场景**（README 中的示例代码 = 最佳业务文档）

---

## 定时任务 / 批处理

### 识别特征

- 代码中有 `@Scheduled` / `cron` / `schedule` / `setInterval`
- 无持续运行的 HTTP server 或 GUI
- 目录中有 `jobs/` / `tasks/` / `cron/`

### 入口搜索

```bash
grep -rn "@Scheduled\|@Cron\|@Task\|cron\.\|setInterval\|setTimeout" --include="*.ts" --include="*.java" --include="*.py"
grep -rn "schedule\.\|APScheduler\|node-cron\|bull" --include="*.ts" --include="*.js" --include="*.py"
```

### 流程追踪路径

```
调度器
  → 任务触发（时间/事件/消息）
  → 数据查询（处理哪些数据）
  → 业务逻辑（做了什么操作）
  → 结果输出（写回数据库/发通知/生成文件）
```

---

## 无类型匹配时

如果项目不属于以上任何类型，回退到**通用方法**：

1. 读 README 功能列表 —— 这是最直接的业务能力清单
2. 搜入口函数：`def main` / `func main` / `if __name__`
3. 搜文件名中的动词：`create_` / `process_` / `export_` / `import_` / `handle_`
4. 问用户："这个项目是怎么用的？"（命令行？双击图标？API 调用？定时运行？）
