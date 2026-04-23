"""
AI视觉识别器 - 从PNG地图图像中智能识别坐标
通过MCP协议利用AI视觉能力识别栅格标注

核心功能：
将PNG栅格地图转换为结构化坐标数据，供AI视觉识别使用

设计原理：
参考 ai_translator_mcp.py 和 layer_visualizer.py 的成功模式：
- 使用 ImageContent 和 file:// URI 传递图片
- 返回识别指南引导AI完成识别
- 避免base64编码，减少数据传输
- 完全依赖AI的视觉理解能力

工作流程：
1. 接收图片目录路径或单个文件路径
2. 搜索并列出所有PNG文件
3. 生成识别指南（包含规则、任务、输出格式）
4. 通过file:// URI返回图片资源
5. AI视觉识别图片中的栅格标注
6. AI输出JSON格式的坐标数据

支持的输入：
- 目录路径：批量识别多层地图（如 mcp_test_maps/）
- 文件路径：识别单个地图文件（如 layer_0.png）
- 自动搜索：支持 layer_*.png 模式匹配

识别能力：
- 蓝色栅格 → 无人机位置
- 红色栅格 → 障碍物位置
- 文字标注 → 精确坐标 (x, y, z)
- 图片标题 → Z层信息提取
"""

import os
import glob
from typing import List, Tuple, Optional, Dict
from pathlib import Path


class AIVisionRecognizer:
    """AI视觉识别器 - 利用AI视觉能力识别栅格地图坐标"""
    
    def __init__(self, workspace_dir: str = r"i:\UAV-MCP"):
        """
        初始化AI视觉识别器
        
        Args:
            workspace_dir: 工作目录路径（默认为项目根目录）
        """
        self.workspace_dir = workspace_dir
        
    def find_images(self, input_path: str, is_directory: bool = True) -> Tuple[bool, List[str], str]:
        """
        查找PNG图片文件
        
        Args:
            input_path: 输入路径（相对或绝对路径）
            is_directory: 是否为目录
            
        Returns:
            (成功标志, 图片文件列表, 错误消息)
        """
        # 转换为绝对路径
        if not os.path.isabs(input_path):
            input_path = os.path.join(self.workspace_dir, input_path)
        
        # 查找PNG文件
        if is_directory:
            # 目录模式：搜索 layer_*.png
            if not os.path.exists(input_path):
                return False, [], f"目录不存在: {input_path}"
            
            search_pattern = os.path.join(input_path, "layer_*.png")
            image_files = sorted(glob.glob(search_pattern))
            
            if len(image_files) == 0:
                return False, [], f"目录中未找到PNG文件\n搜索目录: {input_path}\n搜索模式: layer_*.png"
        else:
            # 单文件模式
            if not os.path.exists(input_path):
                return False, [], f"文件不存在: {input_path}"
            image_files = [input_path]
        
        return True, image_files, ""
    
    def generate_file_uri(self, file_path: str) -> str:
        """
        生成file:// URI格式
        
        Args:
            file_path: 文件绝对路径
            
        Returns:
            file:// URI字符串
        """
        # 将Windows路径转换为URI格式（反斜杠转斜杠）
        uri_path = file_path.replace(chr(92), '/')
        return f"file:///{uri_path}"
    
    def create_recognition_guide(self, image_files: List[str]) -> str:
        """
        创建AI识别指南（MCP工具返回内容）
        
        参考 ai_translator_mcp.py 的设计：
        - 清晰的任务说明
        - 详细的识别规则
        - 标准的输出格式
        - 直接引导AI完成识别
        
        Args:
            image_files: 图片文件路径列表
            
        Returns:
            识别指南文本
        """
        guide_lines = []
        
        # 标题和分隔符
        guide_lines.append("🔍 **AI视觉识别 - 栅格地图坐标提取**\n")
        guide_lines.append("─" * 80)
        
        # 图片信息
        guide_lines.append(f"\n📂 **图片目录**: {os.path.basename(os.path.dirname(image_files[0])) if len(image_files) > 1 else os.path.dirname(image_files[0])}")
        guide_lines.append(f"📊 **图片数量**: {len(image_files)} 个PNG文件\n")
        guide_lines.append("─" * 80)
        guide_lines.append("")
        
        # 识别规则
        guide_lines.append("🎯 **识别规则**:")
        guide_lines.append("  - 🔵 **蓝色栅格** = 无人机位置")
        guide_lines.append("  - 🔴 **红色栅格** = 障碍物位置")
        guide_lines.append("  - ⚪ **白色栅格** = 可通行区域")
        guide_lines.append("  - 📌 **坐标格式**: (x, y, z) - x横坐标, y纵坐标, z层高度")
        guide_lines.append("")
        
        # 任务说明
        guide_lines.append("✅ **你的任务**:")
        guide_lines.append(f"  1️⃣ 查看下面的 {len(image_files)} 张图片")
        guide_lines.append("  2️⃣ 识别每张图片中的栅格标注（如'(5,5,1)'）")
        guide_lines.append("  3️⃣ 从图片标题提取Z层信息（如'第1层栅格地图' → Z=1）")
        guide_lines.append("  4️⃣ 按照下面的JSON格式输出识别结果")
        guide_lines.append("")
        
        # 输出格式说明
        guide_lines.append("📊 **输出JSON格式**:")
        guide_lines.append("```json")
        guide_lines.append("{")
        guide_lines.append('  "uav_position": [x, y, z],  // 无人机坐标，如未找到则为null')
        guide_lines.append('  "obstacles": [             // 所有障碍物坐标数组')
        guide_lines.append('    [x1, y1, z1],')
        guide_lines.append('    [x2, y2, z2],')
        guide_lines.append('    ...')
        guide_lines.append('  ],')
        guide_lines.append('  "total_obstacles": 数字,  // 障碍物总数')
        guide_lines.append('  "layer_results": {         // 每层详细结果')
        guide_lines.append('    "layer_0": {')
        guide_lines.append('      "z": 0,')
        guide_lines.append('      "uav_position": [x,y,z] 或 null,')
        guide_lines.append('      "obstacles": [[x1,y1,z1], ...]')
        guide_lines.append('    },')
        guide_lines.append('    ...')
        guide_lines.append('  }')
        guide_lines.append("}")
        guide_lines.append("```")
        guide_lines.append("")
        
        guide_lines.append("─" * 80)
        guide_lines.append("\n📸 **以下是需要识别的图片**:\n")
        
        return "\n".join(guide_lines)
    
    def create_image_content_list(self, image_files: List[str]) -> List[Dict]:
        """
        创建图片内容列表（用于MCP返回）
        
        Args:
            image_files: 图片文件路径列表
            
        Returns:
            ImageContent字典列表
        """
        from mcp.types import ImageContent
        
        image_contents = []
        
        for image_file in image_files:
            file_uri = self.generate_file_uri(image_file)
            
            # 创建ImageContent对象
            image_contents.append(ImageContent(
                type="image",
                data=file_uri,
                mimeType="image/png"
            ))
        
        return image_contents
    
    def process_recognition_request(self, input_path: str, is_directory: bool = True) -> Tuple[bool, List, str]:
        """
        处理识别请求（MCP工具调用的核心逻辑）
        
        Args:
            input_path: 输入路径
            is_directory: 是否为目录
            
        Returns:
            (成功标志, 返回内容列表, 错误消息)
        """
        from mcp.types import TextContent
        
        # 查找图片
        success, image_files, error_msg = self.find_images(input_path, is_directory)
        
        if not success:
            error_content = TextContent(
                type="text",
                text=f"❌ 错误: {error_msg}\n\n💡 请先使用 `generate_layer_maps` 生成地图文件"
            )
            return False, [error_content], error_msg
        
        # 生成识别指南
        guide_text = self.create_recognition_guide(image_files)
        
        # 构建返回内容
        result_contents = []
        
        # 添加文字指南
        result_contents.append(TextContent(
            type="text",
            text=guide_text
        ))
        
        # 添加图片资源
        image_contents = self.create_image_content_list(image_files)
        result_contents.extend(image_contents)
        
        return True, result_contents, ""
    
    def get_statistics(self, image_files: List[str]) -> Dict:
        """
        获取图片统计信息
        
        Args:
            image_files: 图片文件列表
            
        Returns:
            统计信息字典
        """
        return {
            "total_images": len(image_files),
            "file_names": [os.path.basename(f) for f in image_files],
            "file_paths": image_files,
            "file_uris": [self.generate_file_uri(f) for f in image_files]
        }
    
    def create_mcp_tool_description(self) -> Dict:
        """
        创建MCP工具描述（用于注册到server.py）
        
        Returns:
            工具描述字典
        """
        return {
            "name": "analyze_grid_space_vision",
            "description": """🔍 AI视觉识别 - 从PNG地图图像中智能识别无人机和障碍物坐标。

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
            "inputSchema": {
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
                }
            }
        }
    
    def __repr__(self):
        return f"AIVisionRecognizer(workspace={self.workspace_dir})"


# 测试代码
def test_ai_vision_recognizer():
    """测试AI视觉识别器"""
    recognizer = AIVisionRecognizer()
    
    print("\n" + "=" * 80)
    print("🔍 测试AI视觉识别器")
    print("=" * 80)
    
    # 测试用例
    test_input = "mcp_test_maps"
    
    print(f"\n📂 测试输入: {test_input}")
    print(f"📊 模式: 目录批量识别")
    
    # 查找图片
    success, image_files, error_msg = recognizer.find_images(test_input, is_directory=True)
    
    if not success:
        print(f"\n❌ 错误: {error_msg}")
        return
    
    print(f"\n✅ 找到 {len(image_files)} 个PNG文件:")
    for idx, file in enumerate(image_files, 1):
        print(f"  {idx}. {os.path.basename(file)}")
        print(f"     路径: {file}")
    
    # 生成file:// URI
    print(f"\n📸 生成的file:// URI:")
    for idx, file in enumerate(image_files, 1):
        uri = recognizer.generate_file_uri(file)
        print(f"  {idx}. {uri}")
    
    # 生成识别指南
    print(f"\n📋 生成识别指南:")
    print("─" * 80)
    guide = recognizer.create_recognition_guide(image_files)
    print(guide)
    print("─" * 80)
    
    # 统计信息
    stats = recognizer.get_statistics(image_files)
    print(f"\n📊 统计信息:")
    print(f"  - 图片总数: {stats['total_images']}")
    print(f"  - 文件名: {', '.join(stats['file_names'])}")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成!")
    print("=" * 80)
    
    print("\n💡 使用说明:")
    print("  1. 在server.py中导入: from ai_vision_recognizer import AIVisionRecognizer")
    print("  2. 创建实例: recognizer = AIVisionRecognizer()")
    print("  3. 处理请求: success, contents, error = recognizer.process_recognition_request(input_path, is_directory)")
    print("  4. 返回内容: return contents")


if __name__ == "__main__":
    test_ai_vision_recognizer()
