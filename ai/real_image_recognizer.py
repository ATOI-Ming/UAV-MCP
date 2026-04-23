"""
真实环境照片识别模块 - Real Image Recognizer

功能：
- 处理用户上传的真实环境照片
- 生成AI识别指南（包含详细的识别规则和坐标系统）
- 返回图片URI和识别指南供MCP调用

"""

import os
from typing import Tuple, List
from mcp.types import TextContent, ImageContent


class RealImageRecognizer:
    """真实环境照片识别器
    
    负责处理真实环境照片识别请求，生成AI识别指南
    """
    
    def __init__(self, workspace_dir: str = r"i:\UAV-MCP"):
        """初始化识别器
        
        Args:
            workspace_dir: 工作目录路径
        """
        self.workspace_dir = workspace_dir
    
    def process_image_recognition(
        self, 
        image_path: str, 
        scene_description: str = "",
        grid_size: str = "10x10x10"
    ) -> Tuple[bool, List, str]:
        """处理图片识别请求
        
        Args:
            image_path: 图片路径（相对或绝对）
            scene_description: 场景描述（可选）
            grid_size: 栅格空间大小
            
        Returns:
            (success, result_contents, error_msg)
            - success: 是否成功
            - result_contents: MCP返回内容列表 [TextContent, ImageContent]
            - error_msg: 错误信息（如果失败）
        """
        print(f"\n[RealImageRecognizer] 处理图片识别请求")
        print(f"  图片路径: {image_path}")
        print(f"  场景描述: {scene_description or '未提供'}")
        print(f"  栅格空间: {grid_size}")
        
        # 验证图片文件
        if not image_path:
            error_msg = "❌ 错误: 请提供图片路径\n\n💡 使用方法:\n  1. 将照片保存到项目目录（如 my_room.jpg）\n  2. 调用工具并传入文件名\n  3. 或者直接拖拽图片到对话框"
            return False, [TextContent(type="text", text=error_msg)], error_msg
        
        # 转换为绝对路径
        if not os.path.isabs(image_path):
            image_path = os.path.join(self.workspace_dir, image_path)
        
        # 检查文件是否存在
        if not os.path.exists(image_path):
            error_msg = f"❌ 错误: 图片文件不存在\n\n文件路径: {image_path}\n\n💡 请确保图片已保存到项目目录"
            return False, [TextContent(type="text", text=error_msg)], error_msg
        
        print(f"[RealImageRecognizer] 图片文件存在: {image_path}")
        
        # 生成file:// URI
        file_uri = image_path.replace(chr(92), '/')
        file_uri = f"file:///{file_uri}"
        
        print(f"[RealImageRecognizer] 文件URI: {file_uri}")
        
        # 生成AI识别指南
        guide_text = self._generate_recognition_guide(scene_description, grid_size)
        
        # 返回识别指南和图片
        result_contents = [
            TextContent(type="text", text=guide_text),
            ImageContent(type="image", data=file_uri, mimeType="image/jpeg")
        ]
        
        print(f"[RealImageRecognizer] 成功生成识别指南和图片URI")
        return True, result_contents, ""
    
    def _generate_recognition_guide(self, scene_description: str, grid_size: str) -> str:
        """生成AI识别指南
        
        Args:
            scene_description: 场景描述
            grid_size: 栅格空间大小
            
        Returns:
            完整的AI识别指南文本
        """
        guide_lines = []
        guide_lines.append("🚀 **真实环境障碍物识别任务**")
        guide_lines.append("=" * 80)
        guide_lines.append("")
        guide_lines.append("📸 **任务说明**:")
        guide_lines.append("你是一名无人机环境建模专家。请仔细查看用户上传的真实环境照片，")
        guide_lines.append("识别出所有可能阻碍无人机飞行的障碍物，并转换为栅格坐标。")
        guide_lines.append("")
        guide_lines.append("🎯 **识别目标与环境理解**:")
        guide_lines.append("")
        guide_lines.append("⚠️ **核心原则**: 所有影响无人机飞行的物体和区域都必须标记为障碍物")
        guide_lines.append("")
        guide_lines.append("**必须识别的障碍物类型**:")
        guide_lines.append("  1️⃣ **建筑结构** (最重要！):")
        guide_lines.append("     - 墙壁: 必须标记为连续的障碍物链（多个连续格点）")
        guide_lines.append("     - 柱子: 占据1-4个格点，高度延伸到天花板")
        guide_lines.append("     - 天花板: 如果高度低于2.5米，标记为Z轴上限障碍")
        guide_lines.append("     - 门框、窗框: 标记边界障碍物")
        guide_lines.append("")
        guide_lines.append("  2️⃣ **家具设备**:")
        guide_lines.append("     - 桌子: 占据2x2或3x3格点（根据实际尺寸）")
        guide_lines.append("     - 椅子: 占据1-2个格点")
        guide_lines.append("     - 柜子、书架: 占据多个格点，高度可达2米")
        guide_lines.append("     - 沙发: 占据2-4个格点")
        guide_lines.append("")
        guide_lines.append("  3️⃣ **人物与动态障碍**:")
        guide_lines.append("     - 人: 占据1个格点，高度1.7-2米")
        guide_lines.append("     - 移动设备: 标记当前位置")
        guide_lines.append("")
        guide_lines.append("  4️⃣ **小型物品**:")
        guide_lines.append("     - 电脑、杯子、鼠标等: 占据1个格点")
        guide_lines.append("")
        guide_lines.append("  5️⃣ **室外障碍**:")
        guide_lines.append("     - 树木: 占据多个格点，高度可达10米")
        guide_lines.append("     - 建筑物外墙: 连续障碍物链")
        guide_lines.append("     - 栏杆、围栏: 连续低矮障碍物")
        guide_lines.append("")
        
        if scene_description:
            guide_lines.append(f"📏 **场景描述**: {scene_description}")
            guide_lines.append("")
        
        guide_lines.append(f"📐 **坐标系统与栅格映射规则**:")
        guide_lines.append("")
        guide_lines.append(f"**空间定义**:")
        guide_lines.append(f"  - 栅格空间: {grid_size}（默认[0,10]×[0,10]×[0,10]）")
        guide_lines.append("  - 每格代表: 1米×1米×1米的真实空间")
        guide_lines.append("  - 坐标原点: 照片左下角为(0,0,0)")
        guide_lines.append("  - X轴: 向右为正 (0→10)")
        guide_lines.append("  - Y轴: 向前为正（远离观察者，0→10）")
        guide_lines.append("  - Z轴: 向上为正（地面为Z=0，天花板通常为Z=3）")
        guide_lines.append("")
        guide_lines.append("**障碍物占据规则**:")
        guide_lines.append("  - 小物体(≤0.5米): 占据1个格点")
        guide_lines.append("  - 中型物体(0.5-1.5米): 占据2-4个格点")
        guide_lines.append("  - 大型物体(>1.5米): 占据4-9个格点")
        guide_lines.append("  - 墙壁: 连续占据一整条线的格点")
        guide_lines.append("  - 高度: 每0.5米占据一层，向上累积")
        guide_lines.append("")
        guide_lines.append("**示例**:")
        guide_lines.append("  - 2米长的桌子 → 占据 [(3,4,1), (4,4,1)] 两个相邻格点")
        guide_lines.append("  - 左侧墙壁(10米长) → 占据 [(0,0,1~3), (0,1,1~3), ..., (0,10,1~3)]")
        guide_lines.append("  - 2米高的柱子 → 占据 [(x,y,1), (x,y,2)] 垂直两层")
        guide_lines.append("")
        guide_lines.append("📊 **输出JSON格式（增强版）**:")
        guide_lines.append("```json")
        guide_lines.append("{")
        guide_lines.append('  "scene_analysis": "详细的场景描述，包括房间类型、主要区域划分",')  
        guide_lines.append('  "estimated_size": "真实尺寸估算（长×宽×高），如10米×8米×3米",')  
        guide_lines.append('  "room_boundaries": {  // 房间边界信息（重要！）')  
        guide_lines.append('    "left_wall": [[0,0,1], [0,0,2], [0,1,1], [0,1,2], ...],  // 左墙所有格点')  
        guide_lines.append('    "right_wall": [[10,0,1], [10,0,2], [10,1,1], ...],')  
        guide_lines.append('    "front_wall": [[0,10,1], [1,10,1], [2,10,1], ...],')  
        guide_lines.append('    "back_wall": [[0,0,1], [1,0,1], [2,0,1], ...]')  
        guide_lines.append('  },')  
        guide_lines.append('  "obstacles": [')  
        guide_lines.append('    {')  
        guide_lines.append('      "name": "会议桌",')  
        guide_lines.append('      "type": "furniture",  // furniture/structure/person/equipment')  
        guide_lines.append('      "center_position": [5.0, 5.0, 0.8],  // 物体中心位置')  
        guide_lines.append('      "occupied_grids": [  // 占据的所有格点（关键！）')  
        guide_lines.append('        [4,4,1], [4,5,1], [4,6,1],  // 第一排')  
        guide_lines.append('        [5,4,1], [5,5,1], [5,6,1],  // 第二排')  
        guide_lines.append('        [6,4,1], [6,5,1], [6,6,1]   // 第三排')  
        guide_lines.append('      ],')  
        guide_lines.append('      "dimensions": "3米×3米×0.8米",')  
        guide_lines.append('      "height_meters": 0.8,')  
        guide_lines.append('      "confidence": "高"')  
        guide_lines.append('    },')  
        guide_lines.append('    {')  
        guide_lines.append('      "name": "左侧墙壁",')  
        guide_lines.append('      "type": "structure",')  
        guide_lines.append('      "occupied_grids": [  // 墙壁必须是连续格点链')  
        guide_lines.append('        [0,0,1], [0,0,2], [0,0,3],  // 第一列，高3米')  
        guide_lines.append('        [0,1,1], [0,1,2], [0,1,3],  // 第二列')  
        guide_lines.append('        ...  // 延续到整面墙')  
        guide_lines.append('      ],')  
        guide_lines.append('      "dimensions": "10米长×3米高",')  
        guide_lines.append('      "confidence": "高"')  
        guide_lines.append('    }')  
        guide_lines.append('  ],')  
        guide_lines.append('  "total_obstacles": 2,')  
        guide_lines.append('  "total_grid_points": 120,  // 所有障碍物占据的格点总数')  
        guide_lines.append('  "coordinate_list": [  // 所有障碍物格点的扁平列表（用于add_obstacles）')  
        guide_lines.append('    [4,4,1], [4,5,1], [4,6,1], [5,4,1], [5,5,1], [5,6,1],  // 会议桌9个格点')  
        guide_lines.append('    [0,0,1], [0,0,2], [0,0,3], [0,1,1], ...  // 墙壁所有格点')  
        guide_lines.append('  ],')  
        guide_lines.append('  "free_space_analysis": {  // 可飞行空间分析（可选）')  
        guide_lines.append('    "safe_corridors": ["中央区域(1-9, 1-9)", "走廊区域"],')  
        guide_lines.append('    "suggested_flight_height": "1.5-2.5米（Z=2层）"')  
        guide_lines.append('  }')  
        guide_lines.append("}")
        guide_lines.append("```")
        guide_lines.append("")
        guide_lines.append("⚠️ **关键要求与注意事项**:")
        guide_lines.append("")
        guide_lines.append("  ✅ **必须做到**:")
        guide_lines.append("  1. 所有坐标必须在[0,10]范围内")
        guide_lines.append("  2. 墙壁必须标记为连续的障碍物链（不能有缺口）")
        guide_lines.append("  3. 大型物体必须占据多个格点（不能只用1个点）")
        guide_lines.append("  4. 高度必须精确计算（每0.5米一层，向上累积）")
        guide_lines.append("  5. coordinate_list中包含所有障碍物的所有格点（扁平化列表）")
        guide_lines.append("")
        guide_lines.append("  📏 **高度映射规则**:")
        guide_lines.append("  - 0-0.5米 → Z=1层")
        guide_lines.append("  - 0.5-1.5米 → Z=1,2层")
        guide_lines.append("  - 1.5-2.5米 → Z=1,2,3层")
        guide_lines.append("  - 2.5米以上 → 根据实际高度累积")
        guide_lines.append("")
        guide_lines.append("  🔍 **环境理解要点**:")
        guide_lines.append("  - 仔细识别墙壁、柱子等结构性障碍")
        guide_lines.append("  - 估算物体的真实尺寸（长×宽×高）")
        guide_lines.append("  - 将真实尺寸映射到栅格空间（每格=1米）")
        guide_lines.append("  - 空白区域=可飞行空间，不要遗漏任何障碍物")
        guide_lines.append("")
        guide_lines.append("="* 80)
        guide_lines.append("📸 **请查看下面的环境照片并进行识别**:")
        guide_lines.append("")
        
        return "\n".join(guide_lines)


# 全局单例实例（延迟加载）
_real_image_recognizer = None

def get_real_image_recognizer() -> RealImageRecognizer:
    """获取真实图片识别器的全局单例
    
    Returns:
        RealImageRecognizer实例
    """
    global _real_image_recognizer
    if _real_image_recognizer is None:
        _real_image_recognizer = RealImageRecognizer()
    return _real_image_recognizer
