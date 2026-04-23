"""
AI图像航线规划器 - AI Image Flight Planner (增强版)

核心功能：
从航线规划图片中智能识别飞行意图，生成合理的飞行动作序列

设计理念升级：
1. 【智能理解】不仅识别航点，更要理解图片中的几何形状和飞行意图
2. 【灵活适应】支持有航点/无航点两种模式，自动推理合理的飞行路径
3. 【形状识别】识别几何图形（正方形、圆形、Z字形等），生成对应轨迹
4. 【意图推理】从图片整体布局推断用户的飞行目的和期望路径
5. 【智能补全】即使没有明确航点，也能根据图形生成合理的飞行方案

工作模式：
【模式1】有明确航点标记：
  - 识别航点位置、编号、顺序
  - 提取精确坐标
  - 生成精确的点到点飞行路径

【模式2】仅有几何图形（无航点）：
  - 识别图形类型（正方形、圆形、三角形、星形等）
  - 分析图形尺寸和位置
  - 推理合理的航点布局
  - 生成符合图形特征的飞行轨迹

【模式3】混合模式：
  - 部分航点 + 连线/图形
  - 结合两种模式的优势
  - 智能补全缺失的航点

支持的识别类型：
A. 精确航点型：
   - 地面站航线规划图（Mission Planner、QGroundControl）
   - 手绘标记航点图
   - 坐标标注图

B. 几何图形型：
   - 正方形/矩形轨迹
   - 圆形/椭圆形轨迹
   - 三角形/多边形轨迹
   - Z字形/S字形/螺旋形
   - 星形/米字形等特殊图案

C. 自由轨迹型：
   - 手绘曲线路径
   - 复杂组合图形
   - 艺术性图案

识别能力增强：
1. 航点识别（精确模式）
2. 图形识别（形状推理模式）
3. 意图理解（智能推理模式）
4. 尺寸估算（比例计算）
5. 路径优化（合理化调整）
6. 边界验证（安全检查）
"""

import os
from typing import Tuple, List
from mcp.types import TextContent, ImageContent


class AIImageFlightPlanner:
    """AI图像航线规划器 - 基于AI视觉的航线识别"""
    
    def __init__(self, workspace_dir: str = r"i:\UAV-MCP"):
        """
        初始化图像航线规划器
        
        Args:
            workspace_dir: 工作目录路径
        """
        self.workspace_dir = workspace_dir
        self.grid_bounds = (0, 10)  # [0, 10] × [0, 10]
        self.start_position = (5, 5, 0)  # 起点
    
    def process_flight_image(
        self, 
        image_path: str,
        grid_size: str = "10x10x10",
        image_description: str = ""
    ) -> Tuple[bool, List, str]:
        """
        处理航线规划图片
        
        Args:
            image_path: 图片路径（相对或绝对）
            grid_size: 栅格空间大小
            image_description: 图片描述（可选，帮助AI理解）
            
        Returns:
            (success, result_contents, error_msg)
            - success: 是否成功
            - result_contents: MCP返回内容列表 [TextContent, ImageContent]
            - error_msg: 错误信息（如果失败）
        """
        print(f"\n[AIImageFlightPlanner] 处理航线规划图片")
        print(f"  图片路径: {image_path}")
        print(f"  栅格空间: {grid_size}")
        print(f"  图片描述: {image_description or '未提供'}")
        
        # 验证图片文件
        if not image_path:
            error_msg = "❌ 错误: 请提供航线规划图片路径\n\n💡 使用方法:\n  1. 准备航线规划图片（俯视角、标记航点）\n  2. 保存到项目目录\n  3. 调用工具并传入文件名\n  4. 或直接拖拽图片到对话框"
            return False, [TextContent(type="text", text=error_msg)], error_msg
        
        # 转换为绝对路径
        if not os.path.isabs(image_path):
            image_path = os.path.join(self.workspace_dir, image_path)
        
        # 检查文件是否存在
        if not os.path.exists(image_path):
            error_msg = f"❌ 错误: 图片文件不存在\n\n文件路径: {image_path}\n\n💡 请确保图片已保存到项目目录"
            return False, [TextContent(type="text", text=error_msg)], error_msg
        
        print(f"[AIImageFlightPlanner] 图片文件存在: {image_path}")
        
        # 生成file:// URI
        file_uri = image_path.replace(chr(92), '/')
        file_uri = f"file:///{file_uri}"
        
        print(f"[AIImageFlightPlanner] 文件URI: {file_uri}")
        
        # 生成AI识别指南
        guide_text = self._generate_flight_recognition_guide(image_description, grid_size)
        
        # 返回识别指南和图片
        result_contents = [
            TextContent(type="text", text=guide_text),
            ImageContent(type="image", data=file_uri, mimeType="image/jpeg")
        ]
        
        print(f"[AIImageFlightPlanner] 成功生成识别指南和图片URI")
        return True, result_contents, ""
    
    def _generate_flight_recognition_guide(self, image_description: str, grid_size: str) -> str:
        """
        生成AI航线识别指南（核心设计）
        
        设计参考：
        - ai_translator_mcp.create_conversion_guide() - 转换指南模式
        - real_image_recognizer._generate_recognition_guide() - 图片识别指南
        
        Args:
            image_description: 图片描述
            grid_size: 栅格空间大小
            
        Returns:
            完整的AI识别指南文本
        """
        guide_lines = []
        
        # === 标题和任务说明 ===
        guide_lines.append("🛩️ **AI图像航线规划智能识别任务（增强版）**")
        guide_lines.append("=" * 80)
        guide_lines.append("")
        guide_lines.append("📸 **任务说明**:")
        guide_lines.append("你是一名资深无人机航线规划专家，具备强大的空间推理和几何识别能力。")
        guide_lines.append("请仔细查看用户上传的航线规划图片，**智能理解用户的飞行意图**。")
        guide_lines.append("")
        guide_lines.append("🎯 **核心任务**:")
        guide_lines.append("不仅要识别图片中的航点标记，更要**理解图形含义和飞行目的**。")
        guide_lines.append("即使图片中没有明确的航点标记，也要根据图形形状推理出合理的飞行路径。")
        guide_lines.append("")
        
        if image_description:
            guide_lines.append(f"📝 **图片描述**: {image_description}")
            guide_lines.append("")
        
        # === 栅格空间环境 ===
        guide_lines.append("📐 **栅格空间环境**:")
        guide_lines.append(f"  - 起点位置: {self.start_position} （地面中心）")
        guide_lines.append(f"  - 空间范围: X∈[{self.grid_bounds[0]},{self.grid_bounds[1]}]米, Y∈[{self.grid_bounds[0]},{self.grid_bounds[1]}]米, Z∈[{self.grid_bounds[0]},{self.grid_bounds[1]}]米")
        guide_lines.append("  - 坐标系统:")
        guide_lines.append("    • X轴: 左(负) ← 0 → 右(正)")
        guide_lines.append("    • Y轴: 后(负) ← 0 → 前(正)")
        guide_lines.append("    • Z轴: 下(负) ← 0 → 上(正)")
        guide_lines.append("  - 边界约束: 所有航点必须在[0,10]×[0,10]平面内")
        guide_lines.append("")
        
        # === 智能识别策略（三种模式） ===
        guide_lines.append("🎯 **智能识别策略（三种工作模式）**:")
        guide_lines.append("")
        guide_lines.append("**【模式判断】首先判断图片属于哪种类型**:")
        guide_lines.append("  - 有明确航点标记 → 使用【精确航点模式】")
        guide_lines.append("  - 仅有几何图形无航点 → 使用【形状推理模式】")
        guide_lines.append("  - 部分航点+图形 → 使用【混合智能模式】")
        guide_lines.append("")
        guide_lines.append("="*80)
        guide_lines.append("**【模式1】精确航点模式** - 有明确航点标记时使用")
        guide_lines.append("="*80)
        guide_lines.append("")
        guide_lines.append("**1️⃣ 航点识别**:")
        guide_lines.append("  - **标记类型**: 圆点、方块、星号、数字、字母、箭头等")
        guide_lines.append("  - **起点标识**: 绿色、编号1、START、起点等特殊标记")
        guide_lines.append("  - **终点标识**: 红色、最大编号、END、终点等特殊标记")
        guide_lines.append("  - **中间航点**: 按编号、颜色渐变、连线顺序识别")
        guide_lines.append("  - **坐标提取**: 如果图片上有网格或坐标标注，直接读取坐标值")
        guide_lines.append("")
        guide_lines.append("**2️⃣ 航线顺序识别**:")
        guide_lines.append("  - **连线方向**: 箭头指向、线条走向")
        guide_lines.append("  - **数字编号**: 1→2→3→4的顺序")
        guide_lines.append("  - **颜色渐变**: 从冷色（蓝绿）到暖色（黄红）")
        guide_lines.append("  - **默认规则**: 如无明确顺序，按从左到右、从下到上识别")
        guide_lines.append("")
        guide_lines.append("**3️⃣ 高度信息识别**:")
        guide_lines.append("  - **标注信息**: 航点旁的高度数值（如\"1m\", \"2米\", \"Z=3\"）")
        guide_lines.append("  - **颜色编码**: 不同颜色代表不同高度层")
        guide_lines.append("  - **图例说明**: 查找图例中的高度-颜色对应关系")
        guide_lines.append("  - **默认高度**: 如无明确标注，默认起飞后在Z=1层飞行")
        guide_lines.append("")
        guide_lines.append("="*80)
        guide_lines.append("**【模式2】形状推理模式** - 仅有几何图形时使用（核心增强）")
        guide_lines.append("="*80)
        guide_lines.append("")
        guide_lines.append("**🔷 几何图形识别与推理**:")
        guide_lines.append("")
        guide_lines.append("  **A. 正方形/矩形识别**:")
        guide_lines.append("     - 识别四个角的位置")
        guide_lines.append("     - 测量边长（长和宽）")
        guide_lines.append("     - 推理：在四个角设置航点，顺时针或逆时针飞行")
        guide_lines.append("     - 示例：3米×3米正方形 → 4个角航点 + 闭环路径")
        guide_lines.append("")
        guide_lines.append("  **B. 圆形/椭圆形识别**:")
        guide_lines.append("     - 识别圆心位置和半径")
        guide_lines.append("     - 推理：用正多边形（如正八边形）近似圆形")
        guide_lines.append("     - 在圆周上均匀设置8-12个航点")
        guide_lines.append("     - 示例：半径3米圆形 → 8个均匀航点 + 闭环")
        guide_lines.append("")
        guide_lines.append("  **C. 三角形识别**:")
        guide_lines.append("     - 识别三个顶点位置")
        guide_lines.append("     - 推理：在三个顶点设置航点，三角形飞行")
        guide_lines.append("     - 示例：等边三角形 → 3个顶点航点 + 闭环")
        guide_lines.append("")
        guide_lines.append("  **D. Z字形/S字形识别**:")
        guide_lines.append("     - 识别关键转折点位置")
        guide_lines.append("     - 分析每段的方向和长度")
        guide_lines.append("     - 推理：在转折点设置航点")
        guide_lines.append("     - 示例：Z字形 → 4个转折点航点 + 折线路径")
        guide_lines.append("")
        guide_lines.append("  **E. 星形/米字形识别**:")
        guide_lines.append("     - 识别中心点和辐射方向")
        guide_lines.append("     - 推理：从中心向外辐射再返回")
        guide_lines.append("     - 示例：五角星 → 中心+5个尖端 → 往返路径")
        guide_lines.append("")
        guide_lines.append("  **F. 螺旋形识别**:")
        guide_lines.append("     - 识别螺旋的起点、终点、圈数")
        guide_lines.append("     - 推理：递增半径的圆周运动")
        guide_lines.append("     - 同时增加高度（螺旋上升）或保持高度（平面螺旋）")
        guide_lines.append("")
        guide_lines.append("  **G. 自由曲线识别**:")
        guide_lines.append("     - 沿曲线提取关键控制点")
        guide_lines.append("     - 推理：用直线段连接控制点近似曲线")
        guide_lines.append("     - 航点间距约1-2米，确保平滑")
        guide_lines.append("")
        guide_lines.append("**🔷 图形参数推理规则**:")
        guide_lines.append("  - 识别图形的中心位置（相对于栅格空间）")
        guide_lines.append("  - 估算图形的实际尺寸（映射到米）")
        guide_lines.append("  - 确定飞行方向（顺时针/逆时针）")
        guide_lines.append("  - 计算合理的航点数量（根据图形复杂度）")
        guide_lines.append("  - 确保所有航点在边界[0,10]×[0,10]内")
        guide_lines.append("")
        guide_lines.append("**🔷 智能补全策略**:")
        guide_lines.append("  - 图形不完整时，推理完整形状")
        guide_lines.append("  - 自动添加起降点（从中心起飞，飞完回中心降落）")
        guide_lines.append("  - 优化航点间距，避免过密或过疏")
        guide_lines.append("  - 添加必要的悬停点（如拍照点）")
        guide_lines.append("")
        guide_lines.append("="*80)
        guide_lines.append("**【模式3】混合智能模式** - 部分航点+图形时使用")
        guide_lines.append("="*80)
        guide_lines.append("")
        guide_lines.append("  - 以明确的航点为基准")
        guide_lines.append("  - 根据图形推理中间的过渡航点")
        guide_lines.append("  - 智能连接已知航点和推理航点")
        guide_lines.append("  - 确保路径平滑合理")
        guide_lines.append("")
        guide_lines.append("**4️⃣ 特殊轨迹处理**:")
        guide_lines.append("  - **直线轨迹**: 航点间直线连接 → 拆分为前进/后退/左移/右移")
        guide_lines.append("  - **折线轨迹**: 多段直线组合 → 按顺序执行各段")
        guide_lines.append("  - **曲线轨迹**: 圆弧、螺旋等 → 近似为多段小直线")
        guide_lines.append("  - **复杂图形**: 组合多种识别策略")
        guide_lines.append("")
        
        # === 坐标映射规则 ===
        guide_lines.append("📏 **坐标映射规则**:")
        guide_lines.append("")
        guide_lines.append(f"**空间定义**:")
        guide_lines.append(f"  - 栅格空间: {grid_size}（默认[0,10]×[0,10]×[0,10]）")
        guide_lines.append("  - 每格代表: 1米×1米×1米的真实空间")
        guide_lines.append("  - 坐标原点: 图片左下角为(0,0)，或根据网格标注")
        guide_lines.append("  - 图片映射: 将图片范围映射到[0,10]×[0,10]栅格空间")
        guide_lines.append("")
        guide_lines.append("**映射方法**:")
        guide_lines.append("  - **有网格/标尺**: 直接读取航点的栅格坐标")
        guide_lines.append("  - **无网格**: 将图片宽度映射到X轴[0,10]，高度映射到Y轴[0,10]")
        guide_lines.append("  - **示例**: 图片中心的航点 → 栅格坐标(5,5)")
        guide_lines.append("  - **精度**: 坐标精确到整数（1米），小数部分四舍五入")
        guide_lines.append("")
        
        # === 动作转换规则 ===
        guide_lines.append("🎮 **动作转换规则**:")
        guide_lines.append("")
        guide_lines.append("**可用的基本动作**:")
        guide_lines.append("  - `上升X米` - 向上飞行X米（Z轴正方向）")
        guide_lines.append("  - `下降X米` - 向下飞行X米（Z轴负方向）")
        guide_lines.append("  - `前进X米` - 向前飞行X米（Y轴正方向）")
        guide_lines.append("  - `后退X米` - 向后飞行X米（Y轴负方向）")
        guide_lines.append("  - `右移X米` - 向右飞行X米（X轴正方向）")
        guide_lines.append("  - `左移X米` - 向左飞行X米（X轴负方向）")
        guide_lines.append("  - `悬停X秒` - 在当前位置悬停X秒")
        guide_lines.append("")
        guide_lines.append("**转换方法**:")
        guide_lines.append("  1. **提取航点坐标**: 按顺序识别所有航点的(x,y,z)坐标")
        guide_lines.append("  2. **计算位移向量**: 当前航点到下一航点的Δx, Δy, Δz")
        guide_lines.append("  3. **分解为基本动作**: 先垂直移动(上升/下降)，再水平移动(前后左右)")
        guide_lines.append("  4. **生成动作序列**: 按顺序拼接所有动作")
        guide_lines.append("")
        guide_lines.append("**转换示例**:")
        guide_lines.append("  - 从(5,5,0)到(6,6,1): 上升1米,右移1米,前进1米")
        guide_lines.append("  - 从(6,6,1)到(6,8,1): 前进2米")
        guide_lines.append("  - 从(6,8,1)到(4,8,1): 左移2米")
        guide_lines.append("  - 从(4,8,1)到(5,5,0): 后退3米,右移1米,下降1米")
        guide_lines.append("")
        
        # === 输出格式要求 ===
        guide_lines.append("📋 **输出格式要求（分两阶段输出）**:")
        guide_lines.append("")
        guide_lines.append("**第一阶段：详细图片分析与智能推理**")
        guide_lines.append("  📸 必须先详细分析和描述图片内容，包括：")
        guide_lines.append("")
        guide_lines.append("  **🔍 步骤0: 模式判断（新增）**")
        guide_lines.append("     - **判断图片类型**: 有航点标记？仅有图形？还是混合？")
        guide_lines.append("     - **选择工作模式**: 精确航点模式/形状推理模式/混合模式")
        guide_lines.append("     - **说明判断依据**: 为什么选择该模式")
        guide_lines.append("     - 示例: '图片中绘制了一个正方形，但没有航点标记 → 使用【形状推理模式】'")
        guide_lines.append("")
        guide_lines.append("  1️⃣ **图形/航点识别分析（增强）**")
        guide_lines.append("     【如果有航点】：")
        guide_lines.append("       - 总共识别到多少个航点")
        guide_lines.append("       - 每个航点的位置、标记类型、编号")
        guide_lines.append("       - 起点和终点的具体位置和特征")
        guide_lines.append("     【如果无航点】：")
        guide_lines.append("       - 识别图形类型（正方形/圆形/三角形/Z字形/螺旋形等）")
        guide_lines.append("       - 分析图形的关键特征点（角、中心、半径、转折点等）")
        guide_lines.append("       - **推理合理的航点位置**（如正方形的4个角）")
        guide_lines.append("       - 说明推理依据（为什么在这些位置设置航点）")
        guide_lines.append("     - 示例1: '识别到5个航点：起点(5,5)绿色圆点、P1(7,5)蓝色方块编号1、...'")
        guide_lines.append("     - 示例2: '识别到正方形图形，边长约4米，推理在4个角设置航点：...'" )
        guide_lines.append("")
        guide_lines.append("  2️⃣ **航线形状分析（增强）**")
        guide_lines.append("     - 整体轨迹形状（矩形、Z字形、圆形、螺旋、自由曲线等）")
        guide_lines.append("     - 关键特征描述（对称性、转折点、曲率等）")
        guide_lines.append("     - 航线的大致尺寸（长宽高）")
        guide_lines.append("     - **几何特征**: 是否封闭？是否对称？有几个边/角？")
        guide_lines.append("     - **飞行意图推断**: 用户想要无人机做什么？（环绕/巡检/拍照/测绘）")
        guide_lines.append("     - 示例: '整体为正方形闭环轨迹，4个直角，边长4米，对称性强，推断意图为正方形环绕飞行'")
        guide_lines.append("")
        guide_lines.append("  3️⃣ **航线顺序分析（增强）**")
        guide_lines.append("     【如果有明确顺序】：")
        guide_lines.append("       - 按标记/箭头指示的顺序")
        guide_lines.append("     【如果无明确顺序】：")
        guide_lines.append("       - **推理合理的飞行顺序**（顺时针/逆时针）")
        guide_lines.append("       - 说明选择该顺序的原因（路径最优/符合习惯）")
        guide_lines.append("     - 飞行路径的完整顺序描述")
        guide_lines.append("     - 每段航线的方向和距离估算")
        guide_lines.append("     - 转折点的位置和角度")
        guide_lines.append("     - 示例: '推理顺时针飞行：起点(5,5)→右上角(8,8)→左上角(2,8)→左下角(2,2)→右下角(8,2)→起点'")
        guide_lines.append("")
        guide_lines.append("  4️⃣ **高度层级分析**")
        guide_lines.append("     - 飞行高度变化情况")
        guide_lines.append("     - 是否有高度标注或颜色编码")
        guide_lines.append("     - 工作高度层（默认1米或根据标注）")
        guide_lines.append("     - **如无标注，推理合理高度**（平面图形默认1米，螺旋可递增）")
        guide_lines.append("     - 示例: '无高度标注，推理为平面飞行，统一工作高度Z=1米'")
        guide_lines.append("")
        guide_lines.append("  5️⃣ **坐标计算过程（增强）**")
        guide_lines.append("     【精确模式】：")
        guide_lines.append("       - 详细列出每个标记航点的栅格坐标")
        guide_lines.append("     【推理模式】：")
        guide_lines.append("       - **推理并计算每个航点的合理坐标**")
        guide_lines.append("       - 说明计算方法（几何关系、比例映射）")
        guide_lines.append("       - 确保坐标在边界内且间距合理")
        guide_lines.append("     - 说明坐标是如何从图片映射/推理得出的")
        guide_lines.append("     - 示例1: '起点(5,5,0)、P1(7,5,1)、P2(7,7,1)、P3(4,7,1)、终点(4,7,0)'")
        guide_lines.append("     - 示例2: '推理正方形4个角坐标：左下(3,3,1)、右下(7,3,1)、右上(7,7,1)、左上(3,7,1)'")
        guide_lines.append("")
        guide_lines.append("  6️⃣ **动作序列推导（增强）**")
        guide_lines.append("     - 逐段计算位移向量(Δx, Δy, Δz)")
        guide_lines.append("     - 说明每段如何分解为基本动作")
        guide_lines.append("     - **确保路径合理性**（不走回头路、路径最优）")
        guide_lines.append("     - **补充必要动作**（起飞上升、降落下降）")
        guide_lines.append("     - 示例: '(5,5,0)→(5,5,1)→(7,3,1): 先上升1米，再右移2米后退2米'")
        guide_lines.append("")
        guide_lines.append("**第二阶段：标准动作序列输出**")
        guide_lines.append("  ✅ 在完成详细分析后，最后单独输出标准动作序列")
        guide_lines.append("  ✅ 使用逗号分隔各个动作")
        guide_lines.append("  ✅ 每个动作格式: `动作类型X米` 或 `悬停X秒`")
        guide_lines.append("  ✅ 确保从起点(5,5,0)开始，不超出边界[0,10]×[0,10]")
        guide_lines.append("  ✅ 先执行垂直移动，再执行水平移动")
        guide_lines.append("  ✅ 输出示例格式: `上升1米,右移2米,前进3米,左移1米,下降1米`")
        guide_lines.append("")
        
        # === 识别步骤指导 ===
        guide_lines.append("🧠 **识别步骤指导**:")
        guide_lines.append("")
        guide_lines.append("  **步骤1: 识别所有航点**")
        guide_lines.append("    - 仔细查看图片，找出所有标记点")
        guide_lines.append("    - 识别起点、终点和中间航点")
        guide_lines.append("    - 记录每个航点的大致位置")
        guide_lines.append("")
        guide_lines.append("  **步骤2: 确定航线顺序**")
        guide_lines.append("    - 根据编号、箭头、连线确定飞行顺序")
        guide_lines.append("    - 如无明确标识，按合理路径规划（避免交叉、回头）")
        guide_lines.append("")
        guide_lines.append("  **步骤3: 提取坐标信息**")
        guide_lines.append("    - 如有网格/坐标标注，直接读取")
        guide_lines.append("    - 如无标注，估算航点在[0,10]×[0,10]空间中的位置")
        guide_lines.append("    - 识别高度信息（标注、颜色、图例）")
        guide_lines.append("")
        guide_lines.append("  **步骤4: 计算动作序列**")
        guide_lines.append("    - 从起点(5,5,0)开始")
        guide_lines.append("    - 逐个航点计算位移向量(Δx, Δy, Δz)")
        guide_lines.append("    - 转换为基本动作（上升、下降、前进、后退、左移、右移）")
        guide_lines.append("")
        guide_lines.append("  **步骤5: 生成标准输出**")
        guide_lines.append("    - 按顺序拼接所有动作")
        guide_lines.append("    - 使用逗号分隔")
        guide_lines.append("    - 直接输出，不添加任何解释")
        guide_lines.append("")
        
        # === 注意事项 ===
        guide_lines.append("⚠️ **注意事项**:")
        guide_lines.append("")
        guide_lines.append("  🔸 如果图片模糊或标记不清晰，做出合理推测并说明")
        guide_lines.append("  🔸 优先识别明确的标注信息（数字、文字、箭头）")
        guide_lines.append("  🔸 如果航点过多，可适当简化为关键航点")
        guide_lines.append("  🔸 确保输出的动作序列可以直接被parse_command解析")
        guide_lines.append("  🔸 所有坐标必须在[0,10]×[0,10]范围内")
        guide_lines.append("  🔸 动作距离使用整数（1米、2米等），避免小数")
        guide_lines.append("")
        
        # === 任务提示 ===
        guide_lines.append("=" * 80)
        guide_lines.append("📸 **请查看下面的航线规划图片并进行识别**:")
        guide_lines.append("")
        guide_lines.append("💭 **识别任务（按顺序完成）**:")
        guide_lines.append("")
        guide_lines.append("  **🔍 第一步：详细图片分析（必须完成）**")
        guide_lines.append("    1. 识别所有航点标记（位置、类型、编号）")
        guide_lines.append("    2. 分析航线形状（整体轨迹特征）")
        guide_lines.append("    3. 确定飞行顺序（完整路径描述）")
        guide_lines.append("    4. 分析高度层级（工作高度、升降点）")
        guide_lines.append("    5. 计算栅格坐标（每个航点的精确坐标）")
        guide_lines.append("    6. 推导动作序列（逐段位移计算）")
        guide_lines.append("")
        guide_lines.append("  **✅ 第二步：输出标准动作序列**")
        guide_lines.append("    7. 在分析完成后，单独输出完整的动作序列")
        guide_lines.append("    8. 格式: 动作1,动作2,动作3,...")
        guide_lines.append("")
        guide_lines.append("⚠️ **重要提示**:")
        guide_lines.append("  - 必须先完成详细分析，再输出动作序列")
        guide_lines.append("  - 分析内容要具体、详细，不能省略")
        guide_lines.append("  - 最后的动作序列要单独成行，方便提取")
        guide_lines.append("")
        
        return "\n".join(guide_lines)
    
    def create_mcp_tool_description(self) -> dict:
        """
        创建MCP工具描述（用于注册到server.py）
        
        Returns:
            工具描述字典
        """
        return {
            "name": "ai_flight_image_planner",
            "description": """🛩️ AI图像航线规划器（增强版） - 智能理解图片意图，生成飞行动作序列

【核心能力升级】
不仅识别航点，更能智能理解几何图形和飞行意图！
即使图片中没有明确的航点标记，也能根据图形形状推理出合理的飞行路径。

【三种工作模式】

**模式1：精确航点模式** - 有明确航点标记时使用
  - 识别航点位置、编号、顺序
  - 提取精确坐标
  - 生成精确的点到点路径
  - 适用：地面站航线图、手绘标记图

**模式2：形状推理模式** - 仅有几何图形时使用（★核心增强）
  - 识别图形类型（正方形、圆形、三角形、Z字形、星形等）
  - 分析图形尺寸和位置
  - **智能推理合理的航点布局**
  - 生成符合图形特征的飞行轨迹
  - 适用：纯图形图片（如一个正方形框、一个圆圈）

**模式3：混合智能模式** - 部分航点+图形时使用
  - 结合两种模式的优势
  - 智能补全缺失的航点
  - 确保路径平滑合理

【支持的图形类型】
A. 基本图形：正方形/矩形、圆形/椭圆形、三角形/多边形
B. 特殊轨迹：Z字形、S字形、螺旋形
C. 复杂图案：星形、米字形、自由曲线

【工作流程】
1. 用户上传图片（可有航点或无航点）
2. AI智能判断图片类型，选择工作模式
3. 按模式进行详细分析：
   - 模式1：识别航点位置和顺序
   - 模式2：识别图形并推理航点
   - 模式3：混合分析与智能补全
4. 计算坐标和位移向量
5. 生成标准动作序列
6. 传递给parse_command进行后续处理

【智能推理示例】

**场景1：纯正方形图片（无航点）**
  输入：一张绘有正方形框的图片
  AI推理：
    - 识别为正方形，边长4米
    - 在四个角设置航点：(3,3)、(7,3)、(7,7)、(3,7)
    - 顺时针飞行，工作高度1米
  输出：“上升1米,左移2米,前进4米,右移4米,后退4米,左移2米,下降1米”

**场景2：圆形图案（无航点）**
  输入：一个圆圈
  AI推理：
    - 识别为圆形，半径3米
    - 用正八边形近似圆，8个均匀航点
    - 从右侧开始顺时针环绕
  输出：“上升1米,右移3米,前进3米,左移6米,后退6米,右移6米,前进3米,左移3米,下降1米”

**场景3：Z字形轨迹（无航点）**
  输入：一个Z字形线条
  AI推理：
    - 识别为Z字形，3个转折点
    - 在转折点设置航点
    - 按Z字形飞行路径
  输出：“上升1米,右移2米,前进1米,左移3米,前进1米,右移2米,前进1米,下降1米”

【使用场景】
- 快速导入地面站规划的航线（有航点）
- 手绘图形快速转换为飞行指令（无航点）
- 基于几何形状设计航线（无航点）
- 复杂轨迹的智能规划（混合模式）

【与ai_translate_flight的区别】
- ai_translate_flight: 文字描述 → 动作序列（如“Z字形飞行”）
- ai_flight_image_planner: 图片（有无航点均可）→ 动作序列（智能理解图片）

【注意事项】
- 图片不需要有航点标记，纯几何图形即可
- 所有推理的航点必须在[0,10]×[0,10]空间内
- AI会智能选择最合理的航点数量和路径
- 支持复杂图形的近似处理（圆形用多边形近似）
            """,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "image_path": {
                        "type": "string",
                        "description": "航线规划图片路径（相对于工作目录），如 'flight_plan.jpg'。如果用户拖拽图片，路径会自动传递。",
                    },
                    "image_description": {
                        "type": "string",
                        "description": "图片描述（可选），帮助AI理解图片内容，如'4个航点的正方形航线'、'螺旋上升轨迹'",
                        "default": ""
                    },
                    "grid_size": {
                        "type": "string",
                        "description": "目标栅格空间大小（默认10×10×10），如需自定义可指定，如'[0,10]×[0,10]×[0,10]'",
                        "default": "10x10x10"
                    }
                },
                "required": ["image_path"],
            }
        }
    
    def __repr__(self):
        return f"AIImageFlightPlanner(workspace={self.workspace_dir})"


# 全局单例实例（延迟加载）
_ai_image_flight_planner = None

def get_ai_image_flight_planner() -> AIImageFlightPlanner:
    """
    获取AI图像航线规划器的全局单例
    
    Returns:
        AIImageFlightPlanner实例
    """
    global _ai_image_flight_planner
    if _ai_image_flight_planner is None:
        _ai_image_flight_planner = AIImageFlightPlanner()
    return _ai_image_flight_planner


# 测试代码
if __name__ == "__main__":
    planner = AIImageFlightPlanner()
    
    print("\n" + "=" * 80)
    print("🛩️ 测试AI图像航线规划器")
    print("=" * 80)
    
    # 测试用例
    test_image = "flight_plan_example.jpg"
    
    print(f"\n📂 测试图片: {test_image}")
    print(f"📊 场景: 航线规划图片识别")
    
    # 生成识别指南
    guide = planner._generate_flight_recognition_guide("4个航点的正方形航线", "10x10x10")
    
    print(f"\n📋 生成识别指南:")
    print("─" * 80)
    print(guide[:500] + "...")
    print("─" * 80)
    
    print("\n✅ 模块测试完成!")
    print("\n💡 使用说明:")
    print("  1. 在server.py中导入: from ai_image_flight_planner import get_ai_image_flight_planner")
    print("  2. 注册MCP工具: planner.create_mcp_tool_description()")
    print("  3. 处理请求: success, contents, error = planner.process_flight_image(image_path)")
    print("  4. 返回内容: return contents")
