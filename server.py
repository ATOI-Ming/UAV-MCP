# -*- coding: utf-8 -*-
"""
无人机MCP服务器
提供自然语言控制、仿真可视化、代码生成功能
"""

import sys
import io

# 设置标准输出为UTF-8编码
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import asyncio
import json
from typing import Any, Sequence
from mcp.server import Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
from mcp.server.stdio import stdio_server

# 导入模块
from ai.translator import AITranslatorMCP
from ai.replanner import AIReplannerMCP  # 🆕 AI智能重规划器
from core.command_parser import CommandParser
from core.flight_planner import FlightPlanner
from codegen.generator import UAVCodeGenerator
from core.grid_space import GridSpace
from config import INITIAL_POSITION, GRID_SIZE

# 🆕 导入简化版的空间感知工具（避免启动超时）
from tools.layer_tools import (
    generate_layer_maps_optimized,
)

# 🆕 导入AI视觉识别器（利用AI视觉能力识别栅格地图）
from ai.vision_recognizer import AIVisionRecognizer

# 🆕 导入真实图片识别器（模块化）
from ai.real_image_recognizer import get_real_image_recognizer

# 🆕 导入环境可视化器（模块化）
from visualization.environment_visualizer import get_environment_visualizer

# 🆕 导入AI图像航线规划器
from ai.image_flight_planner import get_ai_image_flight_planner

# 初始化组件（避免重量级初始化）
app = Server("uav-mcp-server")
ai_translator_mcp = AITranslatorMCP()  # 🆕 AI智能转换器
ai_replanner_mcp = AIReplannerMCP()    # 🆕 AI智能重规划器
command_parser = CommandParser()
flight_planner = FlightPlanner()
code_generator = UAVCodeGenerator()

# 🆕 初始化AI视觉识别器
ai_vision_recognizer = AIVisionRecognizer()

# 初始化栅格空间管理
grid_space = GridSpace(grid_size=GRID_SIZE)

# 设置初始位置
flight_planner.set_start_position(INITIAL_POSITION)
grid_space.set_uav_position(INITIAL_POSITION)

# 延迟导入重量级模块（避免启动时加载matplotlib）
visualizer = None
layer_visualizer = None

def get_visualizer():
    """延迟初始化可视化器"""
    global visualizer
    if visualizer is None:
        from visualization.visualizer_3d import GridVisualizer
        visualizer = GridVisualizer()
    return visualizer

def get_layer_visualizer():
    """延迟初始化图层可视化器"""
    global layer_visualizer
    if layer_visualizer is None:
        from visualization.layer_visualizer import LayerVisualizer
        layer_visualizer = LayerVisualizer(grid_space)
    return layer_visualizer


@app.list_resources()
async def list_resources() -> list[Resource]:
    """列出可用资源"""
    return [
        Resource(
            uri="uav://config",
            name="无人机配置",
            mimeType="application/json",
            description="查看当前无人机和仿真空间配置",
        ),
        Resource(
            uri="uav://status",
            name="无人机状态",
            mimeType="application/json",
            description="查看当前无人机位置和航线信息",
        ),
        Resource(
            uri="uav://waypoints",
            name="航点列表",
            mimeType="application/json",
            description="查看当前规划的所有航点",
        ),
    ]


@app.read_resource()
async def read_resource(uri: str) -> str:
    """读取资源"""
    if uri == "uav://config":
        from config import GRID_SIZE, GRID_UNIT, MOVEMENT_SPEED, HOVER_TIME
        config_data = {
            "grid_size": GRID_SIZE,
            "grid_unit": GRID_UNIT,
            "movement_speed": MOVEMENT_SPEED,
            "hover_time": HOVER_TIME,
            "initial_position": INITIAL_POSITION,
        }
        return json.dumps(config_data, ensure_ascii=False, indent=2)
    
    elif uri == "uav://status":
        path_info = flight_planner.get_path_info()
        status_data = {
            "current_position": flight_planner.current_position,
            "path_info": path_info,
        }
        return json.dumps(status_data, ensure_ascii=False, indent=2)
    
    elif uri == "uav://waypoints":
        waypoints = flight_planner.get_waypoints()
        waypoints_data = {
            "total": len(waypoints),
            "waypoints": waypoints,
        }
        return json.dumps(waypoints_data, ensure_ascii=False, indent=2)
    
    else:
        raise ValueError(f"未知资源: {uri}")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出可用工具"""
    return [
        Tool(
            name="ai_flight_image_planner",
            description="""🛪️ AI图像航线规划器 - 从航线规划图片生成飞行动作序列

【核心功能】
从航线规划图片中识别航点、轨迹和顺序，自动转换为标准飞行动作序列。
类似地面站的俯视角航线规划功能，支持手绘、软件生成、卫星视图等多种图片类型。

【工作流程】
1. 用户上传航线规划图片（俯视角、标记航点）
2. AI视觉识别航点位置、飞行顺序、高度信息
3. 计算航点间的位移向量(Δx, Δy, Δz)
4. 转换为标准动作序列（上升、下降、前进、后退、左移、右移）
5. 输出结果传递给parse_command进行后续处理

【支持的图片类型】
- 地面站俯视角航线规划图
- 手绘航点标记图（纸笔绘制）
- 带坐标标注的航线示意图
- 卫星/地图视图的航线规划
- 软件生成的航线图（Mission Planner、QGroundControl等）

【识别能力】
- 航点位置识别（圆点、方块、星号、数字、字母等标记）
- 航线顺序识别（连线、箭头方向、数字编号）
- 高度信息识别（标注、颜色、图例）
- 起点/终点识别（特殊标记、颜色区分）

【输出格式】
标准飞行动作序列，例如：“上升1米,右移3米,前进2米,左移1米,下降1米”
可直接传递给parse_command解析。

【使用场景】
- 快速导入地面站规划的航线
- 手绘航线快速转换为飞行指令
- 基于地图/卫星视图规划航线
- 复杂航线的可视化规划

【与ai_translate_flight的区别】
- ai_translate_flight: 文字描述 → 动作序列（如“Z字形飞行”）
- ai_flight_image_planner: 图片航线 → 动作序列（识别图片中的航点）

【使用流程】
1. 调用ai_flight_image_planner识别航线图片
2. AI返回动作序列
3. 将结果传递给parse_command进行解析
4. 可视化、生成代码、执行任务

【注意事项】
- 图片应清晰标记航点和航线
- 所有航点必须在[0,10]×[0,10]栅格空间内
- 建议使用明确的数字编号或箭头指示顺序
- 高度信息需通过标注或图例说明
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "image_path": {
                        "type": "string",
                        "description": "航线规划图片路径（相对于工作目录），如 'flight_plan.jpg'。如果用户拖拽图片，路径会自动传递。",
                    },
                    "image_description": {
                        "type": "string",
                        "description": "图片描述（可选），帮助AI理解图片内容，如4个航点的正方形航线、螺旋上升轨迹",
                        "default": ""
                    },
                    "grid_size": {
                        "type": "string",
                        "description": "目标栅格空间大小（默认10×10×10），如需自定义可指定，如'[0,10]×[0,10]×[0,10]'",
                        "default": "10x10x10"
                    }
                },
                "required": ["image_path"],
            },
        ),
        Tool(
            name="ai_translate_flight",
            description="""🤖 AI智能转换飞行轨迹描述。
            
功能：将抽象的飞行轨迹（如Z字形、矩形、圆形、螺旋等）转换为具体的飞行动作序列。。
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "用户用自然语言描述的飞行轨迹，可以包含抽象描述（如'Z字形'、'正方形'）和具体动作（如'上升2米'）的混合",
                    }
                },
                "required": ["description"],
            },
        ),
        Tool(
            name="parse_command",
            description="解析自然语言命令为无人机动作序列。支持: 前进、后退、上升、下降、左移、右移、悬停。示例: '上升一米,前进3米,左移一米'",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "自然语言命令,如'上升一米,前进3米,左移一米,前进一米'",
                    }
                },
                "required": ["command"],
            },
        ),
        Tool(
            name="generate_layer_maps",
            description="生成2D栅格地图（各层俭视图），用于AI读取和理解3D栅格空间。必须在规划航线前调用，让AI感知环境中的障碍物分布。",
            inputSchema={
                "type": "object",
                "properties": {
                    "layers": {
                        "type": "string",
                        "description": "要生成的层数列表，JSON格式，例如'[0,1,2]'。默认生成所有层。",
                        "default": "null"
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "输出目录，默认为mcp_layer_maps",
                        "default": "mcp_layer_maps"
                    }
                },
            },
        ),
        Tool(
            name="analyze_grid_space_vision",
            description="""🔍 AI视觉识别 - 从PNG地图图像中智能识别无人机和障碍物坐标。

【核心功能】
利用AI视觉识别能力，直接"读取"PNG地图图像中的栅格标注，提取结构化坐标数据。
这比像素颜色匹配更强大、更准确，能够识别图片中的文字坐标标注。

【工作原理】
1. 接收图片目录路径（或单个图片路径）
2. 列出目录中的PNG文件
3. 通过file:// URI将图片传递给AI
4. AI视觉识别图片中的栅格标注（如"(5,5,1)"）
5. 返回结构化的坐标数据（JSON格式）

【识别规则】
- 蓝色栅格 = 无人机位置
- 红色栅格 = 障碍物位置
- 白色栅格 = 可通行区域
- 从图片标题提取Z层信息（如"第1层栅格地图" → Z=1）

【适用场景】
- 识别generate_layer_maps生成的PNG地图
- 处理用户上传的栅格地图图片
- 批量识别多层地图文件

【输出格式】
返回包含图片资源和识别指南的内容，AI需要：
1. 查看所有图片
2. 识别每个图片中的蓝色/红色栅格标注
3. 提取坐标并输出JSON格式结果
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "input_path": {
                        "type": "string",
                        "description": "PNG文件路径或包含PNG文件的目录路径（相对于工作目录i:\\UAV-MCP）",
                        "default": "mcp_test_maps"
                    },
                    "is_directory": {
                        "type": "boolean",
                        "description": "是否为目录（true=处理目录中所有PNG，false=处理单个文件）",
                        "default": True
                    }
                },
            },
        ),
        Tool(
            name="upload_map_image",
            description="""🚀 【革命性功能】真实环境照片识别 - 自动提取障碍物坐标

【核心功能】
用户上传一张真实环境照片（如室内、操场、客厅、办公室），
AI自动识别所有障碍物（桌子、椅子、人、柱子、墙壁等）并转换为栅格坐标！

【工作流程】
1. 用户上传真实环境照片（支持单张或多张）
2. AI视觉识别照片中的所有障碍物
3. AI理解场景尺寸并估算物体位置
4. 将物理坐标转换为[0,10]×[0,10]栅格空间
5. 输出JSON格式的障碍物坐标列表

【识别目标】
- 🪑 家具：桌子、椅子、沙发、柜子
- 🧍 人物：站立或移动的人
- 🏛️ 建筑：柱子、墙壁、门框
- 📦 物品：箱子、设备、装饰物
- 🌳 室外：树木、石头、栏杆

【坐标转换规则】
- 假设地面为Z=0
- 照片左下角为坐标原点(0,0)
- 场景映射到[0,10]×[0,10]×[0,10]栅格空间
- 障碍物高度根据实际物体估算（如桌子0.8米，人1.7米）

【输出格式】
JSON数组，每个障碍物包含：
- name: 物体名称
- position: [x, y, z]栅格坐标
- size: 尺寸描述（小/中/大）
- confidence: 识别置信度（可选）

【使用场景】
- 室内飞行任务规划（客厅、办公室、仓库）
- 室外环境扫描（操场、公园、广场）
- 快速环境建模（无需手动输入障碍物）
- 真实场景仿真测试

【下一步】
识别完成后，使用 `add_obstacles` 将坐标添加到栅格空间，
即可进行避障路径规划和飞行仿真！
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "image_path": {
                        "type": "string",
                        "description": "上传的环境照片路径（相对于工作目录），如 'my_room.jpg'。如果用户拖拽图片，路径会自动传递。",
                    },
                    "scene_description": {
                        "type": "string",
                        "description": "场景描述（可选），帮助AI理解环境，如'10米×8米的客厅'、'20米×15米的操场'",
                        "default": ""
                    },
                    "grid_size": {
                        "type": "string",
                        "description": "目标栅格空间大小（默认10×10×10），如需自定义可指定，如'[0,10]×[0,10]×[0,10]'",
                        "default": "10x10x10"
                    }
                },
                "required": ["image_path"],
            },
        ),
        
        Tool(
            name="plan_flight",
            description="根据解析的动作序列规划航线,生成航点。必须先使用parse_command解析命令",
            inputSchema={
                "type": "object",
                "properties": {
                    "actions": {
                        "type": "string",
                        "description": "动作序列的JSON字符串,由parse_command生成",
                    }
                },
                "required": ["actions"],
            },
        ),
        Tool(
            name="ai_replan_with_obstacles",
            description="""🤖 AI智能重规划 - 障碍物规避轨迹生成。
            
【核心功能】
当检测到原始轨迹与障碍物发生碰撞时，结合环境障碍物信息，
让AI重新规划一条绕过障碍物的安全飞行轨迹。

【设计理念】
- 与ai_translate_flight设计完全一致
- 不使用A*算法，完全依赖AI理解能力
- 输入：原始轨迹 + 障碍物坐标
- 输出：避障后的新轨迹指令

【工作流程】
1. 接收原始轨迹描述（如"右移4米,前进3米"）
2. 接收环境障碍物坐标列表
3. 生成重规划指南（包含障碍物信息和避障策略）
4. AI阅读指南，理解障碍物分布
5. AI输出绕障后的新动作序列

【与AI转换器的区别】
- ai_translate_flight: 将抽象描述转为动作序列（无障碍物考虑）
- ai_replan_with_obstacles: 结合障碍物重新规划轨迹（避障）

【使用场景】
- parse_command检测到路径碰撞后调用
- 需要绕过障碍物重新规划路径
- AI理解环境信息并生成安全轨迹
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "original_trajectory": {
                        "type": "string",
                        "description": "原始轨迹的动作序列，如'上升一米,右移4米,前进3米'",
                    },
                    "obstacles": {
                        "type": "string",
                        "description": "障碍物坐标JSON字符串，如'[(6,5,1), (7,5,1)]'",
                    },
                    "collision_points": {
                        "type": "string",
                        "description": "碰撞点坐标JSON字符串（可选），如'[(6,5,1)]'",
                        "default": "[]"
                    }
                },
                "required": ["original_trajectory", "obstacles"],
            },
        ),
        Tool(
            name="visualize_flight",
            description="在3D仿真空间中可视化航线,打开实时3D窗口显示",
            inputSchema={
                "type": "object",
                "properties": {
                    "animate": {
                        "type": "boolean",
                        "description": "是否使用动画模式,默认false",
                        "default": False,
                    },
                    "save_image": {
                        "type": "string",
                        "description": "保存图像文件名(可选),例如flight.png",
                    }
                },
            },
        ),
        Tool(
            name="visualize_grid_environment",
            description="""🎬 3D栅格环境可视化 - 独立的环境预览工具
            
【核心功能】
在不需要航点或飞行轨迹的情况下，直接可视化栅格空间环境，
查看障碍物的三维分布情况。

【使用场景】
- 初步设置完栅格环境后，查看障碍物分布是否合理
- 上传图片识别后，验证障碍物是否正确添加
- 规划路径之前，预览环境的三维结构
- 不需要生成航点，只想查看环境

【显示内容】
- 🟦 栅格空间边界：10×10×10的立方体框架
- 🔴 障碍物：红色立方体，显示所有障碍物位置
- 🔵 无人机起始位置：蓝色标记点
- 📊 坐标轴：X/Y/Z轴标注，方便理解空间关系

【交互功能】
- 鼠标拖拽：旋转视角
- 滚轮：缩放视图
- 双击：重置视角

【与其他工具的区别】
- generate_layer_maps: 生成2D PNG地图（平面视图）
- visualize_flight: 3D飞行轨迹可视化（需要航点数据）
- visualize_grid_environment: 3D环境可视化（只需障碍物，无需航点）
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "show_grid": {
                        "type": "boolean",
                        "description": "是否显示栅格线，默认true",
                        "default": True,
                    },
                    "save_image": {
                        "type": "string",
                        "description": "保存图像文件名(可选),例如environment.png",
                    }
                },
            },
        ),
        Tool(
            name="generate_uav_code",
            description="生成可执行的无人机控制Python代码（支持双版本：仿真+DroneKit真实硬件）",
            inputSchema={
                "type": "object",
                "properties": {
                    "output_file": {
                        "type": "string",
                        "description": "输出Python文件名（基础名，不含扩展名），默认为uav_mission",
                        "default": "uav_mission",
                    },
                    "generate_dronekit": {
                        "type": "boolean",
                        "description": "是否同时生成DroneKit真实硬件版本（默认true）",
                        "default": True,
                    }
                },
            },
        ),
        Tool(
            name="reset_position",
            description="重置无人机位置到初始点,清除所有航点",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_flight_info",
            description="获取当前航线的详细信息",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="add_obstacles",
            description="在3D栅格空间中添加障碍物。障碍物会显示在2D地图中（红色），并在路径规划时进行碰撞检测。必须在parse_command之前调用，以便测试避障功能。",
            inputSchema={
                "type": "object",
                "properties": {
                    "obstacles": {
                        "type": "string",
                        "description": "障碍物坐标列表JSON字符串，如'[(5,7,1), (5,7,2), (5,7,3)]'",
                    }
                },
                "required": ["obstacles"],
            },
        ),
        Tool(
            name="clear_obstacles",
            description="清除所有障碍物，重置环境到初始状态。",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_obstacles",
            description="获取当前环境中的所有障碍物坐标列表。",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """调用工具"""
    
    if name == "ai_translate_flight":
        description = arguments.get("description", "")
        
        print(f"\n[DEBUG] AI转换器收到描述: {description}")
        
        # 🆕 重新设计的AI转换逻辑
        # 参考 analyze_grid_space 的成功模式：
        # 返回一个引导性的内容，让AI在下一条消息中直接输出转换结果
        
        # 生成转换指南（引导AI完成转换）
        conversion_guide = ai_translator_mcp.create_conversion_guide(description)
        
        # 返回格式化的指南，引导AI输出转换结果
        return [TextContent(
            type="text",
            text=conversion_guide,
        )]
    
    elif name == "ai_replan_with_obstacles":
        # 🆕 AI智能重规划器（与ai_translate_flight设计完全一致）
        original_trajectory = arguments.get("original_trajectory", "")
        obstacles_str = arguments.get("obstacles", "[]")
        collision_points_str = arguments.get("collision_points", "[]")
        
        print(f"\n[DEBUG] AI重规划器收到:")
        print(f"  原始轨迹: {original_trajectory}")
        print(f"  障碍物: {obstacles_str}")
        print(f"  碰撞点: {collision_points_str}")
        
        # 解析障碍物坐标
        obstacles = ai_replanner_mcp.parse_obstacles_from_json(obstacles_str)
        collision_points = ai_replanner_mcp.parse_obstacles_from_json(collision_points_str) if collision_points_str != "[]" else None
        
        print(f"  解析后障碍物: {obstacles}")
        print(f"  解析后碰撞点: {collision_points}")
        
        # 生成重规划指南（引导AI完成重规划）
        replanning_guide = ai_replanner_mcp.create_replanning_guide(
            original_trajectory,
            obstacles,
            collision_points
        )
        
        print(f"[DEBUG] 重规划指南已生成，长度: {len(replanning_guide)} 字符")
        
        # 返回格式化的指南，引导AI输出重规划结果
        return [TextContent(
            type="text",
            text=replanning_guide,
        )]
    
    elif name == "parse_command":
        command = arguments.get("command", "")
        
        print(f"\n[DEBUG] 收到命令: {command}")
        
        # 解析命令
        actions = command_parser.parse_command(command)
        
        if not actions:
            return [TextContent(
                type="text",
                text="错误: 无法解析命令。\n\n支持的动作: 前进、后退、上升、下降、左移、右移、悬停\n示例: '上升一米,前进3米,左移一米'",
            )]
        
        print(f"[DEBUG] 解析结果: {actions}")
        
        # 生成航点
        waypoints = command_parser.actions_to_waypoints(actions, INITIAL_POSITION)
        
        print(f"[DEBUG] 航点数量: {len(waypoints)}")
        print(f"[DEBUG] 航点列表: {waypoints}")
        
        # 清空旧航点并验证
        flight_planner.clear_waypoints()
        flight_planner.set_start_position(INITIAL_POSITION)
        success, msg, replanned_path = flight_planner.add_waypoints(waypoints[1:])  # 跳过起点
        
        print(f"[DEBUG] 验证结果: {success}, {msg}")
        
        # 生成详细报告
        report_lines = []
        report_lines.append(f"✅ 命令解析成功!\n")
        report_lines.append(f"📝 **命令**: {command}\n")
        report_lines.append(f"🎯 **动作解析** (共{len(actions)}个):")
        
        for i, action in enumerate(actions, 1):
            report_lines.append(f"  {i}. {action['action_cn']} {action['grids']}格 ({action['distance']}米)")
        
        report_lines.append(f"\n[航点生成] (共{len(waypoints)}个):")
        
        for i, wp in enumerate(waypoints):
            if i == 0:
                report_lines.append(f"  🟢 起点: {wp}")
            elif i == len(waypoints) - 1:
                report_lines.append(f"  🔴 终点: {wp}")
            else:
                report_lines.append(f"  🔵 P{i}: {wp}")
        
        if success:
            path_info = flight_planner.get_path_info()
            report_lines.append(f"\n[成功] 航线验证通过:")
            report_lines.append(f"  - 总距离: {path_info['total_distance']}米")
            report_lines.append(f"  - 网格数: {path_info['total_grids']}格")
            
            from config import MOVEMENT_SPEED
            flight_time = path_info['total_distance'] / MOVEMENT_SPEED
            report_lines.append(f"  - 预计时间: {flight_time:.1f}秒")
            
            report_lines.append(f"\n[下一步]:")
            report_lines.append(f"  1. 使用 `visualize_flight` 查看3D可视化")
            report_lines.append(f"  2. 使用 `generate_uav_code` 生成控制代码")
        else:
            report_lines.append(f"\n[错误] 航线验证失败: {msg}")
        
        result = {
            "command": command,
            "actions": actions,
            "waypoints": waypoints,
            "validation": {"success": success, "message": msg},
        }
        
        return [TextContent(
            type="text",
            text="\n".join(report_lines),
        )]
    
    elif name == "plan_flight":
        actions_str = arguments.get("actions", "[]")
        
        try:
            actions = json.loads(actions_str)
        except:
            return [TextContent(
                type="text",
                text="错误: actions参数格式不正确,需要JSON字符串",
            )]
        
        # 生成航点
        waypoints = command_parser.actions_to_waypoints(actions, INITIAL_POSITION)
        
        # 清除旧航点并添加新航点
        flight_planner.clear_waypoints()
        success, msg, _ = flight_planner.add_waypoints(waypoints[1:])
        
        path_info = flight_planner.get_path_info()
        
        result = {
            "success": success,
            "message": msg,
            "path_info": path_info,
            "waypoints": waypoints,
        }
        
        return [TextContent(
            type="text",
            text=f"✅ 航线规划完成!\n\n{json.dumps(result, ensure_ascii=False, indent=2)}",
        )]
    
    elif name == "visualize_flight":
        animate = arguments.get("animate", False)
        save_image = arguments.get("save_image", None)
        
        waypoints = flight_planner.get_waypoints()
        
        print(f"\n[DEBUG] 可视化航点数量: {len(waypoints)}")
        print(f"[DEBUG] 航点: {waypoints}")
        
        if len(waypoints) < 2:
            return [TextContent(
                type="text",
                text="❌ 错误: 没有足够的航点进行可视化。\n\n💡 请先使用 `parse_command` 解析命令。\n\n示例:\n```\nparse_command(“上升一米,前进3米,左移一米”)\n```",
            )]
        
        # 生成可视化
        try:
            print(f"[DEBUG] 开始创建可视化...")
            # 使用延迟加载的可视化器
            visualizer_new = get_visualizer()
            visualizer_new.grid_space = grid_space  # 传递栅格空间引用
            
            report_lines = []
            report_lines.append("[3D可视化] 可视化窗口\n")
            report_lines.append(f"[航点信息]:")
            report_lines.append(f"  - 航点数: {len(waypoints)}")
            report_lines.append(f"  - 起点: {waypoints[0]}")
            report_lines.append(f"  - 终点: {waypoints[-1]}")
            
            path_info = flight_planner.get_path_info()
            report_lines.append(f"  - 总距离: {path_info['total_distance']}米")
            
            report_lines.append(f"\n[操作方式]:")
            report_lines.append(f"  - 鼠标拖拽 = 旋转视图")
            report_lines.append(f"  - 滚轮 = 缩放视图")
            report_lines.append(f"  - 关闭窗口继续")
            
            report_lines.append(f"\n[显示模式]: {'Dynamic Animation' if animate else 'Static View'}")
            
            if save_image:
                report_lines.append(f"\n[保存图像]: {save_image}")
            
            report_lines.append(f"\n[状态] 正在打开3D窗口...")
            
            # 【关键优化】使用异步渲染模式(完全不阻塞)
            print(f"[DEBUG] 使用异步渲染模式...")
            
            import time
            start_time = time.time()
            
            # 【异步渲染】一次性调用visualize_flight，同时处理保存和显示
            print(f"[DEBUG] 调用visualize_flight(async_mode=True, save_image={save_image})...")
            image_file = visualizer_new.visualize_flight(
                waypoints,
                save_image=save_image,  # 传递保存参数
                show_window=True, 
                animate=animate, 
                async_mode=True  # ⭐ 启用异步模式
            )
            
            if save_image and image_file:
                report_lines.append(f"\n[成功] 图像已保存: {image_file}")
            
            elapsed = time.time() - start_time
            
            print(f"[DEBUG] 异步可视化已启动，主流程阻塞时间: {elapsed*1000:.1f}ms")
            
            report_lines.append(f"\n[成功] 3D窗口已启动! (异步渲染模式)")
            report_lines.append(f"\n[性能优化]: 主流程阻塞时间仅 {elapsed*1000:.1f}ms")
            report_lines.append(f"\n[提示]: 窗口正在后台线程独立渲染")
            report_lines.append(f"  - 完全不阻塞工作流 (0ms延迟)")
            report_lines.append(f"  - 您可以立即继续下一步操作")
            report_lines.append(f"  - 窗口在后台独立运行")
            report_lines.append(f"  - 3D视图将在几秒内完成渲染")
            
            result = {
                "success": True,
                "waypoints_count": len(waypoints),
                "mode": "async" if not animate else "animate",
                "blocking_time_ms": round(elapsed * 1000, 1),
                "message": "3D窗口已异步启动",
            }
            
            return [TextContent(
                type="text",
                text="\n".join(report_lines),
            )]
            
        except Exception as e:
            import traceback
            error_msg = f"[错误] 可视化错误: {str(e)}\n\n{traceback.format_exc()}"
            print(f"[ERROR] {error_msg}")
            return [TextContent(
                type="text",
                text=error_msg,
            )]
    
    elif name == "visualize_grid_environment":
        # 🎬 3D栅格环境可视化 - 独立的环境预览工具（模块化）
        show_grid = arguments.get("show_grid", True)
        save_image = arguments.get("save_image", None)
        
        print(f"\n[DEBUG] 🎬 3D栅格环境可视化（调用模块）")
        
        # 调用 EnvironmentVisualizer 处理请求
        env_visualizer = get_environment_visualizer()
        success, result_contents, error_msg = env_visualizer.visualize_environment(
            grid_space, 
            flight_planner,
            get_visualizer,
            show_grid, 
            save_image
        )
        
        if success:
            print(f"[DEBUG] 3D环境可视化成功")
        else:
            print(f"[DEBUG] 可视化失败: {error_msg}")
        
        return result_contents
    
    elif name == "generate_uav_code":
        output_file = arguments.get("output_file", "uav_mission")
        generate_dronekit = arguments.get("generate_dronekit", True)
        
        waypoints = flight_planner.get_waypoints()
        
        print(f"\n[DEBUG] 生成代码,航点数: {len(waypoints)}")
        print(f"[DEBUG] MCP工具'generate_uav_code'已注册并正常工作")
        print(f"[DEBUG] 生成DroneKit版本: {generate_dronekit}")
        
        if len(waypoints) < 2:
            return [TextContent(
                type="text",
                text="❌ 错误: 没有足够的航点生成代码。\n\n💡 请先使用 `parse_command` 解析命令。",
            )]
        
        try:
            import os
            # 确保文件生成到工作目录 i:\UAV-MCP\
            workspace_dir = r"i:\UAV-MCP"
            
            # 移除扩展名（如果有）
            if output_file.endswith('.py'):
                output_file = output_file[:-3]
            
            report_lines = []
            report_lines.append("💻 **无人机控制代码已生成**\n")
            
            if generate_dronekit:
                # 生成两个版本：仿真 + DroneKit
                print(f"[DEBUG] 生成双版本代码")
                
                sim_file, dronekit_file = code_generator.generate_from_waypoints_dual(
                    waypoints, 
                    output_file
                )
                
                # 验证文件是否生成成功
                sim_exists = os.path.exists(sim_file)
                dronekit_exists = dronekit_file and os.path.exists(dronekit_file)
                
                if sim_exists:
                    sim_size = os.path.getsize(sim_file)
                    report_lines.append(f"✅ **仿真版本**:")
                    report_lines.append(f"  💾 文件名: `{os.path.basename(sim_file)}`")
                    report_lines.append(f"  📂 完整路径: `{sim_file}`")
                    report_lines.append(f"  📏 文件大小: {sim_size} bytes")
                    report_lines.append(f"")
                
                if dronekit_exists:
                    dronekit_size = os.path.getsize(dronekit_file)
                    report_lines.append(f"✅ **DroneKit真实硬件版本**:")
                    report_lines.append(f"  💾 文件名: `{os.path.basename(dronekit_file)}`")
                    report_lines.append(f"  📂 完整路径: `{dronekit_file}`")
                    report_lines.append(f"  📏 文件大小: {dronekit_size} bytes")
                    report_lines.append(f"  ⚠️  适用于: Pixhawk飞控 + 光流定位")
                    report_lines.append(f"  📦 依赖: dronekit-python, pymavlink")
                    report_lines.append(f"")
                
                output_file_final = sim_file  # 用于后续统计
                
            else:
                # 只生成仿真版本
                output_file_final = os.path.join(workspace_dir, f"{output_file}.py")
                code = code_generator.generate_from_waypoints(waypoints, output_file_final)
                
                if not os.path.exists(output_file_final):
                    raise FileNotFoundError(f"文件生成失败: {output_file_final}")
                
                file_size = os.path.getsize(output_file_final)
                report_lines.append(f"💾 **文件名**: `{os.path.basename(output_file_final)}`")
                report_lines.append(f"📂 **完整路径**: `{output_file_final}`")
                report_lines.append(f"📏 **文件大小**: {file_size} bytes")
            
            # 任务信息（通用）
            report_lines.append(f"📍 **航点数**: {len(waypoints)}")
            
            path_info = flight_planner.get_path_info()
            report_lines.append(f"📊 **任务信息**:")
            report_lines.append(f"  - 总距离: {path_info['total_distance']}米")
            report_lines.append(f"  - 网格数: {path_info['total_grids']}格")
            
            from config import MOVEMENT_SPEED
            flight_time = path_info['total_distance'] / MOVEMENT_SPEED
            report_lines.append(f"  - 预计时间: {flight_time:.1f}秒")
            
            report_lines.append(f"\n🚀 **运行方式**:")
            
            if generate_dronekit and dronekit_exists:
                report_lines.append(f"\n**仿真模式**:")
                report_lines.append(f"```bash")
                report_lines.append(f"python {os.path.basename(sim_file)}")
                report_lines.append(f"```")
                
                report_lines.append(f"\n**真实硬件模式** (⚠️ 请先阅读代码中的安全说明):")
                report_lines.append(f"```bash")
                report_lines.append(f"# 1. 安装依赖")
                report_lines.append(f"pip install dronekit pymavlink")
                report_lines.append(f"")
                report_lines.append(f"# 2. SITL仿真测试")
                report_lines.append(f"dronekit-sitl copter  # 新终端")
                report_lines.append(f"python {os.path.basename(dronekit_file)}  # 另一终端")
                report_lines.append(f"")
                report_lines.append(f"# 3. 真实硬件测试（修改代码中的CONNECTION_STRING）")
                report_lines.append(f"python {os.path.basename(dronekit_file)}")
                report_lines.append(f"```")
            else:
                report_lines.append(f"```bash")
                report_lines.append(f"python {os.path.basename(output_file_final)}")
                report_lines.append(f"```")
            
            report_lines.append(f"\n✅ **代码包含**:")
            if generate_dronekit and dronekit_exists:
                report_lines.append(f"  - 💻 仿真版: UAVController 控制类 + 实时可视化")
                report_lines.append(f"  - 🛩️ DroneKit版: 光流定位 + MAVLink命令 + 安全检查")
            else:
                report_lines.append(f"  - UAVController 控制类")
            report_lines.append(f"  - 完整的任务执行序列")
            report_lines.append(f"  - 位置跟踪和日志输出")
            report_lines.append(f"  - 错误处理机制")
            
            result = {
                "success": True,
                "simulation_file": sim_file if generate_dronekit else output_file_final,
                "dronekit_file": dronekit_file if generate_dronekit else None,
                "waypoints_count": len(waypoints),
                "dual_mode": generate_dronekit,
            }
            
            return [TextContent(
                type="text",
                text="\n".join(report_lines),
            )]
            
        except Exception as e:
            import traceback
            error_msg = f"❌ 代码生成错误: {str(e)}\n\n{traceback.format_exc()}"
            print(f"[ERROR] {error_msg}")
            return [TextContent(
                type="text",
                text=error_msg,
            )]
    
    elif name == "reset_position":
        flight_planner.clear_waypoints()
        flight_planner.set_start_position(INITIAL_POSITION)
        
        return [TextContent(
            type="text",
            text=f"✅ 位置已重置到初始点: {INITIAL_POSITION}",
        )]
    
    elif name == "get_flight_info":
        path_info = flight_planner.get_path_info()
        waypoints = flight_planner.get_waypoints()
        
        result = {
            "current_position": flight_planner.current_position,
            "path_info": path_info,
            "waypoints": waypoints,
        }
        
        return [TextContent(
            type="text",
            text=f"📊 航线信息:\n\n{json.dumps(result, ensure_ascii=False, indent=2)}",
        )]
    
    elif name == "generate_layer_maps":
        # 🔧 使用优化版实现
        return generate_layer_maps_optimized(arguments, grid_space, get_layer_visualizer)
    
    
    elif name == "add_obstacles":
        # 🆕 添加障碍物到栅格空间
        obstacles_str = arguments.get("obstacles", "[]")
        
        print(f"\n[DEBUG] 添加障碍物: {obstacles_str}")
        
        try:
            # 解析障碍物坐标
            obstacles = json.loads(obstacles_str)
            
            if not isinstance(obstacles, list):
                return [TextContent(
                    type="text",
                    text=f"❌ 错误: obstacles参数格式不正确\n\n需要JSON数组格式，如: '[(5,7,1), (5,7,2)]'\n实际收到: {obstacles_str}",
                )]
            
            # 转换为元组列表
            obstacle_positions = [tuple(obs) if isinstance(obs, list) else obs for obs in obstacles]
            
            print(f"[DEBUG] 解析后的障碍物坐标: {obstacle_positions}")
            
            # 添加障碍物到栅格空间
            success_count, errors = grid_space.add_obstacles(obstacle_positions)
            
            # 同时将栅格空间关联到flight_planner（启用碰撞检测）
            flight_planner.set_grid_space(grid_space)
            
            print(f"[DEBUG] 成功添加 {success_count}/{len(obstacle_positions)} 个障碍物")
            print(f"[DEBUG] 当前总障碍物数: {len(grid_space.obstacles)}")
            
            report_lines = []
            report_lines.append("✅ **障碍物添加完成**\n")
            report_lines.append(f"📍 **添加结果**:")
            report_lines.append(f"  - 请求数量: {len(obstacle_positions)}")
            report_lines.append(f"  - 成功添加: {success_count}")
            report_lines.append(f"  - 添加失败: {len(errors)}")
            report_lines.append(f"  - 环境总障碍物: {len(grid_space.obstacles)}")
            report_lines.append(f"")
            
            if success_count > 0:
                report_lines.append(f"🔴 **已添加的障碍物坐标**:")
                for idx, obs in enumerate(obstacle_positions[:success_count], 1):
                    report_lines.append(f"  {idx}. {obs}")
                report_lines.append(f"")
            
            if errors:
                report_lines.append(f"⚠️ **错误信息**:")
                for err in errors:
                    report_lines.append(f"  - {err}")
                report_lines.append(f"")
            
            report_lines.append(f"💡 **下一步**:")
            report_lines.append(f"  1. 使用 `generate_layer_maps` 生成包含障碍物的2D地图")
            report_lines.append(f"  2. 使用 `parse_command` 规划飞行路径（会自动检测碰撞）")
            report_lines.append(f"  3. 如检测到碰撞，使用 `ai_replan_with_obstacles` 重新规划")
            
            return [TextContent(type="text", text="\n".join(report_lines))]
            
        except json.JSONDecodeError as e:
            return [TextContent(
                type="text",
                text=f"❌ JSON解析错误: {str(e)}\n\n💡 正确格式示例: '[(5,7,1), (5,7,2), (5,7,3)]'\n实际收到: {obstacles_str}",
            )]
        except Exception as e:
            import traceback
            return [TextContent(
                type="text",
                text=f"❌ 添加障碍物失败: {str(e)}\n\n{traceback.format_exc()}",
            )]
    
    elif name == "clear_obstacles":
        # 🆕 清除所有障碍物
        print(f"\n[DEBUG] 清除所有障碍物")
        
        old_count = len(grid_space.obstacles)
        grid_space.clear_obstacles()
        
        print(f"[DEBUG] 已清除 {old_count} 个障碍物")
        
        return [TextContent(
            type="text",
            text=f"✅ **障碍物已清除**\n\n已移除 {old_count} 个障碍物\n环境已重置为初始状态",
        )]
    
    elif name == "analyze_grid_space_vision":
        # 🔍 AI视觉识别 - 从 PNG 图像中识别坐标（调用独立模块）
        input_path = arguments.get("input_path", "mcp_test_maps")
        is_directory = arguments.get("is_directory", True)
        
        print(f"\n[DEBUG] 🔍 AI视觉识别: {input_path} (is_dir={is_directory})")
        
        # 调用 AIVisionRecognizer 处理请求
        success, result_contents, error_msg = ai_vision_recognizer.process_recognition_request(
            input_path, is_directory
        )
        
        if success:
            print(f"[DEBUG] 成功生成 {len(result_contents)} 个返回内容")
        else:
            print(f"[DEBUG] 识别失败: {error_msg}")
        
        return result_contents
    
    elif name == "upload_map_image":
        # 🚀 真实环境照片识别 - 自动提取障碍物坐标（模块化）
        image_path = arguments.get("image_path", "")
        scene_description = arguments.get("scene_description", "")
        grid_size = arguments.get("grid_size", "10x10x10")
        
        print(f"\n[DEBUG] 🚀 真实环境照片识别（调用模块）")
        
        # 调用 RealImageRecognizer 处理请求
        real_image_recognizer = get_real_image_recognizer()
        success, result_contents, error_msg = real_image_recognizer.process_image_recognition(
            image_path, scene_description, grid_size
        )
        
        if success:
            print(f"[DEBUG] 成功生成 {len(result_contents)} 个返回内容")
        else:
            print(f"[DEBUG] 识别失败: {error_msg}")
        
        return result_contents
    
    elif name == "ai_flight_image_planner":
        # 🛪️ AI图像航线规划器 - 从航线规划图片生成飞行动作序列
        image_path = arguments.get("image_path", "")
        image_description = arguments.get("image_description", "")
        grid_size = arguments.get("grid_size", "10x10x10")
        
        print(f"\n[DEBUG] 🛪️ AI图像航线规划器（调用模块）")
        
        # 调用 AIImageFlightPlanner 处理请求
        image_flight_planner = get_ai_image_flight_planner()
        success, result_contents, error_msg = image_flight_planner.process_flight_image(
            image_path, grid_size, image_description
        )
        
        if success:
            print(f"[DEBUG] 成功生成 {len(result_contents)} 个返回内容")
        else:
            print(f"[DEBUG] 识别失败: {error_msg}")
        
        return result_contents
    
    elif name == "get_obstacles":
        # 🆕 获取当前所有障碍物
        print(f"\n[DEBUG] 获取障碍物列表")
        
        obstacles = list(grid_space.obstacles)
        
        print(f"[DEBUG] 当前障碍物数量: {len(obstacles)}")
        
        report_lines = []
        report_lines.append(f"📍 **当前环境障碍物**\n")
        report_lines.append(f"🔴 **总数量**: {len(obstacles)}\n")
        
        if len(obstacles) > 0:
            report_lines.append(f"🔴 **障碍物坐标列表**:")
            for idx, obs in enumerate(obstacles, 1):
                report_lines.append(f"  {idx}. {obs}")
            
            report_lines.append(f"\n📦 **JSON格式**:")
            report_lines.append(f"```json")
            report_lines.append(f"{json.dumps(obstacles, ensure_ascii=False, indent=2)}")
            report_lines.append(f"```")
        else:
            report_lines.append(f"✅ 环境中无障碍物")
        
        return [TextContent(type="text", text="\n".join(report_lines))]
    
    else:
        raise ValueError(f"未知工具: {name}")


async def main():
    """主函数"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
