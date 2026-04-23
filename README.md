# UAV-MCP

> 🛺 基于 Model Context Protocol (MCP) 的智能无人机控制服务器——用自然语言规划飞行、感知环境、生成可执行代码。

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 项目简介

UAV-MCP 是一个运行在 MCP 协议上的无人机控制后端服务，让 AI 助手（如 Claude）直接通过对话控制无人机仿真系统。用户无需编写任何代码，只需用自然语言描述飞行意图，系统就能完成从指令解析、路径规划、障碍物感知、可视化预览到生成可执行代码的全流程。

**核心特点：**

- 🗣️ **自然语言驱动**：直接用中文描述飞行任务，无需了解底层接口
- 🧠 **AI 驱动避障**：不依赖传统 A* 算法，通过引导 AI 理解障碍物分布，自主重规划绕障路径
- 📷 **图像识别建模**：上传真实照片或航线规划图，AI 自动提取障碍物坐标或航点
- 🗺️ **3D 栅格空间**：10×10×10 米的三维仿真环境，起点在中心 (5,5,0)
- 💻 **双版本代码生成**：同一航线同时输出仿真版和 DroneKit 真实硬件版 Python 代码

---

## 功能架构

```
用户自然语言 / 图片
        ↓
   AI 翻译 / 图像识别
        ↓
  指令解析 & 路径规划
        ↓
   碰撞检测 → AI 避障重规划
        ↓
  3D 可视化 & 2D 地图
        ↓
  生成可执行代码（仿真 / DroneKit）
```

---

## 目录结构

```
UAV-MCP/
├── server.py                  # MCP 服务器入口
├── config.py                  # 全局参数配置
├── core/                      # 核心引擎
│   ├── grid_space.py          # 3D 栅格空间管理
│   ├── flight_planner.py      # 路径规划与碰撞检测
│   └── command_parser.py      # 自然语言指令解析
├── ai/                        # AI 智能层
│   ├── translator.py          # 自然语言 → 动作序列转换器
│   ├── replanner.py           # AI 障碍物避障重规划器
│   ├── vision_recognizer.py   # 栅格地图视觉识别器
│   ├── image_flight_planner.py# 航线图片 → 动作序列规划器
│   └── real_image_recognizer.py# 真实照片障碍物识别器
├── visualization/             # 可视化层
│   ├── visualizer_3d.py       # 3D 飞行轨迹可视化
│   ├── layer_visualizer.py    # 分层 2D PNG 地图生成
│   └── environment_visualizer.py # 独立 3D 环境预览
├── codegen/                   # 代码生成层
│   ├── generator.py           # 仿真版代码生成器
│   └── dronekit_generator.py  # DroneKit 真实硬件代码生成器
├── tools/                     # MCP 工具适配层
│   └── layer_tools.py         # 空间感知工具
└── missions/                  # 任务脚本示例
    ├── simple_mission_sim.py
    └── simple_mission_dronekit.py
```

---

## MCP 工具列表

| 工具名 | 功能描述 |
|--------|----------|
| `ai_translate_flight` | 将自然语言轨迹描述（Z字形、螺旋、矩形等）转换为动作序列 |
| `ai_flight_image_planner` | 识别航线规划图片中的航点，生成飞行动作序列 |
| `parse_command` | 解析标准动作指令（上升/下降/前进/后退/左移/右移） |
| `plan_flight` | 根据动作序列规划三维航线，生成航点列表 |
| `ai_replan_with_obstacles` | 检测到障碍物碰撞后，AI 自动重规划绕障路径 |
| `generate_layer_maps` | 生成各高度层的 2D PNG 俯视地图（供 AI 视觉感知） |
| `analyze_grid_space_vision` | AI 视觉识别 PNG 地图中的无人机和障碍物坐标 |
| `upload_map_image` | 上传真实环境照片，AI 自动识别障碍物并转换为栅格坐标 |
| `add_obstacles` | 手动向栅格空间添加障碍物 |
| `clear_obstacles` | 清除所有障碍物，重置环境 |
| `get_obstacles` | 获取当前环境中所有障碍物坐标 |
| `visualize_flight` | 在 3D 窗口中实时可视化飞行轨迹 |
| `visualize_grid_environment` | 独立预览 3D 栅格环境（无需航点） |
| `generate_uav_code` | 生成可执行的无人机控制代码（仿真版 + DroneKit 版） |
| `reset_position` | 重置无人机到初始位置，清除所有航点 |
| `get_flight_info` | 获取当前航线详细信息 |

---

## 快速开始

### 1. 环境要求

- Python 3.10+
- 支持 MCP 的 AI 客户端（推荐 Claude Desktop）

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

或使用 `pyproject.toml`：

```bash
pip install mcp numpy matplotlib Pillow
```

### 3. 配置 MCP 客户端

根据你使用的客户端，选择对应的配置方式：

#### 方式一：Qoder IDE

找到并编辑 MCP 配置文件：

```
C:\Users\<你的用户名>\AppData\Roaming\Qoder\SharedClientCache\mcp.json
```

在 `mcpServers` 中添加以下内容：

```json
"uav-mcp-server": {
  "timeout": 60,
  "type": "stdio",
  "command": "D:\\Anaconda3\\python.exe",
  "args": [
    "i:\\UAV\\UAV-MCP\\server.py"
  ],
  "env": {},
  "disabled": false
}
```

> **注意**：
> - `command` 填写你的 Python 解释器完整路径（推荐 Anaconda 环境）
> - `args` 填写 `server.py` 的实际绝对路径
> - `disabled` 必须设为 `false` 才会生效

#### 方式二：Claude Desktop

找到并编辑：

```
C:\Users\<你的用户名>\AppData\Roaming\Claude\claude_desktop_config.json
```

添加：

```json
{
  "mcpServers": {
    "uav-mcp-server": {
      "command": "D:\\Anaconda3\\python.exe",
      "args": ["i:\\UAV\\UAV-MCP\\server.py"]
    }
  }
}
```

#### 方式三：其他支持 MCP 的客户端

配置 stdio 类型服务器，命令为：

```
D:\Anaconda3\python.exe i:\UAV\UAV-MCP\server.py
```

### 4. 验证安装

修改配置后重启 MCP 客户端，在对话中输入：

```
获取无人机当前状态
```

如果返回位置信息（起点 5,5,0），说明连接成功。

---

## 使用示例

### 基础飞行指令

```
用户: 上升2米，前进5米，右移3米，下降1米

AI → parse_command → plan_flight → visualize_flight
```

### 自然语言轨迹

```
用户: 帮我规划一个Z字形飞行轨迹

AI → ai_translate_flight → parse_command → plan_flight
```

### 图片识别建模

```
用户: [上传一张室内照片] 识别房间内的障碍物并规划飞行路径

AI → upload_map_image → add_obstacles → plan_flight → ai_replan_with_obstacles
```

### 生成真实硬件代码

```
用户: 生成可以在真实无人机上执行的代码

AI → generate_uav_code（同时输出仿真版和DroneKit版）
```

---

## 仿真空间说明

| 参数 | 值 |
|------|----|
| 空间大小 | 10×10×10 米 |
| 坐标范围 | X: [0,10]，Y: [0,10]，Z: [0,10] |
| 起始位置 | (5, 5, 0) — 地图中心底部 |
| 移动速度 | 0.5 米/秒 |
| 悬停时间 | 2.0 秒 |
| 坐标轴方向 | X→右，Y→前，Z→上 |

---

## 依赖库

| 库 | 用途 |
|----|------|
| `mcp >= 0.9.0` | MCP 服务器协议 |
| `numpy >= 1.20.0` | 数值计算 |
| `matplotlib >= 3.3.0` | 2D/3D 可视化 |
| `Pillow >= 8.0.0` | 图像处理 |
| `scipy >= 1.6.0` | 科学计算 |

---

## 项目特色

### AI 驱动的避障设计

不同于传统 A* 寻路，本项目采用 **"指南引导"** 模式：当检测到路径碰撞时，系统生成包含障碍物分布的详细描述，引导 AI 自行理解空间关系并输出绕障轨迹。这使得系统具备更强的灵活性，能处理复杂的空间推理任务。

### 延迟加载策略

Matplotlib 等重量级模块在 MCP 服务器启动时不加载（避免超时），仅在实际调用可视化工具时才初始化，确保服务器快速响应。

### 双版本代码生成

同一套航点数据可同时生成：
- **仿真版**：使用 `time.sleep()` 模拟飞行时序，可在任何电脑上直接运行
- **DroneKit 版**：通过 MAVLink 协议连接 Pixhawk 飞控，直接控制真实硬件

---

## 联系方式

- **GitHub**: [ATOI-Ming/UAV-MCP](https://github.com/ATOI-Ming/UAV-MCP)
- **Email**: 1757772673@qq.com
- **WeChat**: flytoworldenddream

---

## License

MIT License
