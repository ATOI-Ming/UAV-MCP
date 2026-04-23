"""
简化版空间感知工具
快速启动，支持PNG图像输出给AI识别
"""

import os
import json
import base64
from typing import Dict, List, Tuple, Optional, Any, Union
from mcp.types import TextContent, ImageContent


def generate_layer_maps_optimized(arguments: Dict, grid_space, get_layer_visualizer) -> List[Any]:
    """生成2D PNG地图"""
    layers_str = arguments.get("layers", "null")
    output_dir = arguments.get("output_dir", "mcp_layer_maps")
    
    if layers_str == "null" or layers_str is None:
        layers = list(range(11))
    else:
        try:
            layers = json.loads(layers_str)
        except:
            layers = list(range(11))
    
    # 初始化可视化器
    try:
        layer_vis = get_layer_visualizer()
        # 强制同步栅格空间状态
        layer_vis.grid_space = grid_space
    except Exception as e:
        return [TextContent(type="text", text=f"错误: {str(e)}")]
    
    # 创建输出目录
    workspace_dir = r"i:\UAV-MCP"
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(workspace_dir, output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成地图
    generated_files = []
    layer_info = {}
    
    for z in layers:
        filename = f"layer_{z}.png"
        save_path = os.path.join(output_dir, filename)
        
        try:
            result = layer_vis.generate_layer_image(z=z, save_path=save_path)
            if result and os.path.exists(save_path):
                layer_data = grid_space.get_layer_data(z)
                if layer_data is None:
                    continue
                
                obstacles_in_layer = []
                uav_in_layer = None
                
                for cell in layer_data["cells"]:
                    if cell["type"] == "obstacle":
                        obstacles_in_layer.append(cell["position"])
                    elif cell["type"] == "uav":
                        uav_in_layer = cell["position"]
                
                layer_info[z] = {
                    "file": filename,
                    "obstacles": obstacles_in_layer,
                    "uav_position": uav_in_layer
                }
                generated_files.append(result)
        except Exception as e:
            print(f"错误: 第{z}层生成失败 - {e}")
    
    # 生成报告
    report = [f"✅ 生成了 {len(generated_files)} 个PNG地图文件\n"]
    report.append(f"📂 输出目录: {output_dir}\n")
    
    all_obstacles = []
    uav_pos = None
    for z, info in layer_info.items():
        all_obstacles.extend(info['obstacles'])
        if info['uav_position']:
            uav_pos = info['uav_position']
    
    if uav_pos:
        report.append(f"🔵 无人机: {uav_pos}")
    report.append(f"🔴 障碍物: {len(all_obstacles)}个")
    for obs in all_obstacles:
        report.append(f"   {obs}")
    
    return [TextContent(type="text", text="\n".join(report))]


