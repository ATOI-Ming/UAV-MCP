"""
优化版的空间感知工具实现
用于 server.py 中的 generate_layer_maps 和 analyze_grid_space 工具

优化点：
1. 增强错误处理
2. 输出完整的障碍物和无人机坐标
3. 优化报告格式，便于AI理解
4. 添加数据验证
"""

import os
import json
import base64
from typing import Dict, List, Tuple, Optional, Any, Union
from mcp.types import TextContent, ImageContent


def generate_layer_maps_optimized(arguments: Dict, grid_space, get_layer_visualizer) -> List[Any]:
    """
    优化版的 generate_layer_maps 工具实现
    
    功能：
    1. 生成每一层的2D PNG图片
    2. 保存到指定文件夹
    3. 输出详细的坐标信息（无人机+障碍物）
    
    Args:
        arguments: 工具参数字典
        grid_space: GridSpace实例
        get_layer_visualizer: 获取可视化器的函数
        
    Returns:
        MCP TextContent列表
    """
    layers_str = arguments.get("layers", "null")
    output_dir = arguments.get("output_dir", "mcp_layer_maps")
    
    # 解析层数列表
    if layers_str == "null" or layers_str is None:
        layers = list(range(11))  # 生成所有层 (0-10)
    else:
        try:
            layers = json.loads(layers_str)
        except Exception as e:
            print(f"[ERROR] 解析layers参数失败: {e}")
            layers = list(range(11))
    
    print(f"\n[DEBUG] 🗺️  生成2D栅格地图: {layers}")
    print(f"[DEBUG] 📂 输出目录: {output_dir}")
    
    # 🔧 初始化图层可视化器（延迟加载）
    try:
        layer_vis = get_layer_visualizer()
        print("[DEBUG] ✅ LayerVisualizer初始化成功")
    except Exception as e:
        print(f"[ERROR] ❌ LayerVisualizer初始化失败: {e}")
        return [TextContent(
            type="text",
            text=f"❌ 错误: 图层可视化器初始化失败\n\n详细信息: {str(e)}",
        )]
    
    # 创建输出目录（绝对路径）
    workspace_dir = r"i:\UAV-MCP"
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(workspace_dir, output_dir)
    
    os.makedirs(output_dir, exist_ok=True)
    print(f"[DEBUG] 📁 输出目录已创建: {output_dir}")
    
    # 生成各层地图
    generated_files = []
    layer_info = {}
    errors = []
    
    for z in layers:
        filename = f"layer_{z}.png"
        save_path = os.path.join(output_dir, filename)
        
        try:
            # 生成图像
            result = layer_vis.generate_layer_image(z=z, save_path=save_path)
            
            if result and os.path.exists(save_path):
                file_size = os.path.getsize(save_path)
                generated_files.append(result)
                
                # 获取该层的详细信息
                layer_data = grid_space.get_layer_data(z)
                
                if layer_data is None:
                    print(f"[WARNING] ⚠️  第{z}层数据为空")
                    continue
                
                # 统计障碍物和无人机
                obstacles_in_layer = []
                uav_in_layer = None
                
                for cell in layer_data["cells"]:
                    if cell["type"] == "obstacle":
                        obstacles_in_layer.append(cell["position"])
                    elif cell["type"] == "uav":
                        uav_in_layer = cell["position"]
                
                layer_info[z] = {
                    "file": filename,
                    "file_path": save_path,
                    "file_size": file_size,
                    "obstacles_count": len(obstacles_in_layer),
                    "obstacles": obstacles_in_layer,
                    "uav_present": uav_in_layer is not None,
                    "uav_position": uav_in_layer
                }
                
                print(f"[DEBUG] ✅ 第{z}层: {len(obstacles_in_layer)}个障碍物, 文件大小{file_size}bytes")
            else:
                errors.append(f"第{z}层图像生成失败")
                print(f"[ERROR] ❌ 第{z}层图像生成失败")
                
        except Exception as e:
            errors.append(f"第{z}层: {str(e)}")
            print(f"[ERROR] 生成第{z}层时出错: {e}")
            import traceback
            traceback.print_exc()
    
    # ========================================
    # 生成详细报告
    # ========================================
    report_lines = []
    report_lines.append("🗺️ **2D栅格地图生成完成**\n")
    report_lines.append(f"📊 **生成统计**:")
    report_lines.append(f"  - 请求生成: {len(layers)}层")
    report_lines.append(f"  - 成功生成: {len(generated_files)}层")
    report_lines.append(f"  - 失败数量: {len(errors)}层")
    report_lines.append(f"  - 输出目录: `{output_dir}/`")
    
    if errors:
        report_lines.append(f"\n⚠️ **错误信息**:")
        for err in errors[:5]:  # 最多显示5个错误
            report_lines.append(f"  - {err}")
    
    # ========================================
    # 生成每层的详细坐标信息
    # ========================================
    report_lines.append(f"\n📋 **各层详细坐标信息**:")
    report_lines.append(f"")
    
    for z in sorted(layer_info.keys()):
        info = layer_info[z]
        report_lines.append(f"**━━━ 第{z}米高度 ━━━**")
        report_lines.append(f"  📄 文件: `{info['file']}` ({info['file_size']} bytes)")
        
        # 无人机坐标
        if info['uav_present']:
            x, y, z_coord = info['uav_position']
            report_lines.append(f"  🔵 **无人机坐标**: ({x}, {y}, {z_coord})")
        else:
            report_lines.append(f"  ⚪ **无人机**: 不在此层")
        
        # 障碍物坐标
        if info['obstacles_count'] > 0:
            report_lines.append(f"  🔴 **障碍物坐标** (共{info['obstacles_count']}个):")
            # 显示所有障碍物坐标（不限制数量）
            for obs in info['obstacles']:
                x, y, z_coord = obs
                report_lines.append(f"       • ({x}, {y}, {z_coord})")
        else:
            report_lines.append(f"  ⚪ **障碍物**: 无")
        
        report_lines.append("")  # 空行分隔
    
    # ========================================
    # 全局坐标汇总
    # ========================================
    all_obstacles = []
    uav_position = None
    for z, info in layer_info.items():
        all_obstacles.extend(info['obstacles'])
        if info['uav_present']:
            uav_position = info['uav_position']
    
    report_lines.append(f"📍 **全局坐标汇总**:")
    if uav_position:
        report_lines.append(f"  🔵 **无人机位置**: {uav_position}")
    else:
        report_lines.append(f"  ⚪ **无人机**: 未设置")
    
    report_lines.append(f"  🔴 **障碍物总数**: {len(all_obstacles)}个")
    if len(all_obstacles) > 0:
        report_lines.append(f"  🔴 **所有障碍物坐标列表**:")
        for obs in all_obstacles:
            report_lines.append(f"     • {obs}")
    
    # ========================================
    # JSON格式数据（便于AI解析）
    # ========================================
    json_data = {
        "uav_position": uav_position,
        "obstacles": all_obstacles,
        "total_obstacles": len(all_obstacles),
        "layers_generated": list(layer_info.keys())
    }
    
    report_lines.append(f"\n```json")
    report_lines.append(f"{json.dumps(json_data, ensure_ascii=False, indent=2)}")
    report_lines.append(f"```")
    
    # ========================================
    # 完成提示
    # ========================================
    report_lines.append(f"\n✅ **地图已生成**: {len(generated_files)}个PNG文件已保存到 `{output_dir}/`")
    report_lines.append(f"\n🚀 **下一步**:")
    report_lines.append(f"  1. 使用 `analyze_grid_space` 让AI读取PNG图像")
    report_lines.append(f"  2. AI将通过视觉识别每层的障碍物分布")
    report_lines.append(f"  3. 基于上述坐标数据进行智能避障航线规划")
    
    return [TextContent(
        type="text",
        text="\n".join(report_lines),
    )]


