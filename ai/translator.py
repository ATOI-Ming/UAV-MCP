"""
AI驱动的自然语言转换器 (重新设计版本)

核心功能：
将任意自然语言飞行描述转换为 parse_command 可识别的标准动作序列

设计原理：
参考 analyze_grid_space 的成功模式，通过MCP工具返回特殊格式的提示，
引导AI完成转换工作，AI的下一条消息就是转换结果。

工作流程：
1. 用户输入自然语言描述（如"Z字形飞行3米"、"画个正方形"、"写个A字"）
2. MCP工具返回转换指南（包含环境信息、示例、格式要求）
3. AI阅读指南后，直接输出转换后的动作序列
4. 转换结果自动传递给 parse_command

支持的输入类型：
- 几何图形：Z字形、正方形、矩形、圆形、三角形、五角星
- 字母数字：A、B、C、1、2、3等
- 汉字轨迹：王、日、月、田等
- 坐标序列：[(5,5,0), (6,6,1), (7,7,2)]
- 抽象描述：螺旋上升、环绕飞行、之字形巡航
- 组合任务：先上升5米，画个正方形，再下降
"""

import re
from typing import Dict, Optional, List, Tuple


class AITranslatorMCP:
    """AI智能转换器 - 将自然语言转换为动作指令"""
    
    def __init__(self):
        """初始化转换器"""
        # 栅格空间配置
        self.grid_bounds = (0, 10)  # [0, 10] × [0, 10]
        self.start_position = (5, 5, 0)  # 起点
    
    def get_supported_patterns(self) -> Dict[str, List[str]]:
        """获取支持的轨迹模式分类"""
        return {
            "几何图形": [
                "Z字形", "正方形", "矩形", "圆形", "三角形",
                "五角星", "8字形", "菱形", "梯形"
            ],
            "字母数字": [
                "A", "B", "C", "D", "E", "F", "G", "H",
                "1", "2", "3", "4", "5", "6", "7", "8", "9", "0"
            ],
            "汉字轨迹": [
                "王", "日", "月", "田", "目", "口", "工", "干", "十"
            ],
            "三维轨迹": [
                "螺旋上升", "螺旋下降", "立体8字", "环绕飞行"
            ],
            "其他": [
                "坐标序列", "抽象描述", "组合任务"
            ]
        }
    
    def create_conversion_guide(self, user_description: str) -> str:
        """
        创建AI转换指南（MCP工具返回内容）
        
        参考 analyze_grid_space 的设计：让AI直接读取输入并输出结果。
        不使用预设示例，完全依赖AI的理解能力。
        
        Args:
            user_description: 用户的自然语言描述
            
        Returns:
            转换指南文本（引导AI完成转换）
        """
        
        guide_lines = []
        guide_lines.append("🤖 **AI轨迹理解与转换**\n")
        guide_lines.append("─" * 80)
        guide_lines.append(f"\n📝 **用户描述**: {user_description}\n")
        guide_lines.append("🎯 **你的任务**: 理解上述描述，将其转换为无人机可执行的飞行动作序列\n")
        guide_lines.append("─" * 80)
        guide_lines.append("")
        
        # 环境信息
        guide_lines.append("📐 **栅格空间环境**:")
        guide_lines.append(f"  - 起点位置: {self.start_position} （地面中心）")
        guide_lines.append(f"  - 空间范围: X∈[{self.grid_bounds[0]},{self.grid_bounds[1]}]米, Y∈[{self.grid_bounds[0]},{self.grid_bounds[1]}]米, Z∈[{self.grid_bounds[0]},{self.grid_bounds[1]}]米")
        guide_lines.append("  - 坐标系统:")
        guide_lines.append("    • X轴: 左(负) ← 0 → 右(正)")
        guide_lines.append("    • Y轴: 后(负) ← 0 → 前(正)")
        guide_lines.append("    • Z轴: 下(负) ← 0 → 上(正)")
        guide_lines.append("  - 边界约束: 所有航点必须在[0,10]×[0,10]平面内\n")
        
        # 可用动作
        guide_lines.append("🎮 **可用的基本动作**:")
        guide_lines.append("  - `上升X米` - 向上飞行X米（Z轴正方向）")
        guide_lines.append("  - `下降X米` - 向下飞行X米（Z轴负方向）")
        guide_lines.append("  - `前进X米` - 向前飞行X米（Y轴正方向）")
        guide_lines.append("  - `后退X米` - 向后飞行X米（Y轴负方向）")
        guide_lines.append("  - `右移X米` - 向右飞行X米（X轴正方向）")
        guide_lines.append("  - `左移X米` - 向左飞行X米（X轴负方向）")
        guide_lines.append("  - `悬停X秒` - 在当前位置悬停X秒\n")
        
        guide_lines.append("─" * 80)
        guide_lines.append("")
        
        # 理解指导（不是示例，是方法论）
        guide_lines.append("🧠 **理解方法**:")
        guide_lines.append("  1. **几何图形**: 分析形状特征，分解为基本直线段")
        guide_lines.append("     （如Z字形=斜上+横+斜下，正方形=4条边）")
        guide_lines.append("  2. **字母/汉字**: 识别笔画结构，转换为移动轨迹")
        guide_lines.append("     （如A=左斜+右斜+横，王=三横一竖）")
        guide_lines.append("  3. **坐标序列**: 计算从当前位置到目标点的位移")
        guide_lines.append("     （如从(5,5,0)到(6,6,1)=右移1米,前进1米,上升1米）")
        guide_lines.append("  4. **抽象描述**: 理解意图，设计合理的飞行路径")
        guide_lines.append("     （如螺旋上升=圆周运动+持续上升）")
        guide_lines.append("  5. **组合任务**: 分阶段规划，串联多个子任务\n")
        
        guide_lines.append("─" * 80)
        guide_lines.append("")
        
        # 输出格式
        guide_lines.append("📋 **输出格式要求**:")
        guide_lines.append("  ✅ 只输出动作序列，不要任何前缀、解释或说明")
        guide_lines.append("  ✅ 使用逗号分隔各个动作")
        guide_lines.append("  ✅ 每个动作格式: `动作类型X米` 或 `悬停X秒`")
        guide_lines.append("  ✅ 确保从起点(5,5,0)开始，不超出边界[0,10]×[0,10]")
        guide_lines.append("  ✅ 输出示例格式: `上升2米,右移3米,前进3米,下降2米`\n")
        
        guide_lines.append("─" * 80)
        guide_lines.append("")
        
        # 直接提示
        guide_lines.append(f"\n💭 **请理解并转换以下描述**: \"{user_description}\"\n")
        guide_lines.append("  - 分析其几何特征、含义或意图")
        guide_lines.append("  - 设计从起点(5,5,0)开始的飞行路径")
        guide_lines.append("  - 直接输出动作序列（格式: 动作1,动作2,动作3）")
        guide_lines.append("  - 不要添加任何解释或前缀\n")
        
        guide_lines.append("─" * 80)
        guide_lines.append("\n✅ **请直接输出转换后的动作序列**:")
        guide_lines.append("")
        
        return "\n".join(guide_lines)
    
    
    def validate_command(self, command: str) -> Tuple[bool, str]:
        """
        验证转换后的指令是否合法
        
        Args:
            command: 转换后的动作序列
            
        Returns:
            (是否合法, 错误信息)
        """
        if not command or not command.strip():
            return False, "动作序列为空"
        
        # 基本动作关键词
        valid_actions = ['上升', '下降', '前进', '后退', '左移', '右移', '悬停']
        
        # 检查是否包含有效动作
        has_action = any(action in command for action in valid_actions)
        if not has_action:
            return False, f"未识别到有效动作，需包含: {', '.join(valid_actions)}"
        
        # 检查是否包含单位
        has_unit = '米' in command or '秒' in command
        if not has_unit:
            return False, "动作必须包含距离单位（米）或时间单位（秒）"
        
        # 检查格式（应该是逗号分隔）
        if ',' not in command and len(command.split()) > 1:
            return False, "多个动作应使用逗号分隔"
        
        return True, "指令格式正确"
    
    def get_example_conversions(self) -> List[Dict[str, str]]:
        """
        获取转换示例列表
        
        Returns:
            示例字典列表 [{"input": ..., "output": ...}, ...]
        """
        return [
            {
                "type": "几何图形",
                "input": "Z字形飞行3米",
                "output": "右移3米,前进3米,右移3米",
                "analysis": "Z字形 = 右上斜线 + 横线 + 右下斜线"
            },
            {
                "type": "几何图形",
                "input": "画个边长4米的正方形",
                "output": "右移4米,前进4米,左移4米,后退4米",
                "analysis": "正方形 = 4条边，顺时针飞行"
            },
            {
                "type": "字母",
                "input": "飞出字母A",
                "output": "上升4米,右移2米,下降2米,右移2米,上升4米,下降2米,左移2米",
                "analysis": "A = 左斜线 + 右斜线 + 中间横线"
            },
            {
                "type": "汉字",
                "input": "画汉字'王'",
                "output": "右移3米,后退1米,左移3米,前进2米,右移3米,后退1米,左移1.5米,前进2米",
                "analysis": "王 = 三条横线 + 一条竖线"
            },
            {
                "type": "坐标序列",
                "input": "经过坐标(6,6,1), (7,7,2)",
                "output": "右移1米,前进1米,上升1米,右移1米,前进1米,上升1米",
                "analysis": "从(5,5,0)依次到达各坐标点"
            },
            {
                "type": "组合任务",
                "input": "先上升5米,画个Z字形3米,再下降",
                "output": "上升5米,右移3米,前进3米,右移3米,下降5米",
                "analysis": "分阶段规划: 上升 + Z字形 + 下降"
            },
            {
                "type": "三维轨迹",
                "input": "螺旋上升，半径2米，高度4米",
                "output": "右移1.4米,上升0.5米,前进1.4米,上升0.5米,左移1.4米,上升0.5米,后退1.4米,上升0.5米,右移1.4米,上升0.5米,前进1.4米,上升0.5米,左移1.4米,上升0.5米,后退1.4米,上升0.5米",
                "analysis": "螺旋 = 圆形路径 + 持续上升"
            },
        ]
    
    def create_mcp_tool_description(self) -> Dict:
        """
        创建MCP工具描述（用于注册到server.py）
        
        Returns:
            工具描述字典
        """
        return {
            "name": "ai_translate_flight",
            "description": """
🤖 AI智能转换飞行轨迹描述

【核心功能】
将任意自然语言飞行描述转换为具体的飞行动作序列。
AI自动理解轨迹特征，生成parse_command可识别的标准指令。

【支持的输入类型】（无限扩展）
- 几何图形：Z字形、正方形、矩形、圆形、三角形、五角星、菱形
- 字母数字：A、B、C、1、2、3等任意字符轨迹
- 汉字轨迹：王、日、月、田、口等简单汉字
- 坐标序列：[(5,5,0), (6,6,1), (7,7,2)]等坐标路径
- 三维轨迹：螺旋上升、环绕飞行、立体8字
- 组合任务：先上升再画图形再下降等复杂任务

【输入示例】
- "Z字形飞行3米"
- "画个边长5米的正方形"
- "飞出字母A"
- "画汉字'王'"
- "经过坐标(6,6,1), (7,7,2)"
- "先上升5米，画个Z字形，再下降"

【输出格式】
标准飞行动作序列，例如："右移3米,前进3米,右移3米"
可直接传递给parse_command解析。

【使用流程】
1. 调用ai_translate_flight转换抽象描述
2. AI返回转换后的动作序列
3. 将结果传递给parse_command进行解析

【注意事项】
- 所有轨迹必须在[0,10]×[0,10]栅格空间内
- 从起点(5,5,0)开始规划
- 如果输入已是具体动作，可直接使用parse_command
            """,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "用户用自然语言描述的飞行轨迹、图形、字母、汉字或任意路径"
                    }
                },
                "required": ["description"]
            }
        }
    
    def __repr__(self):
        return f"AITranslatorMCP(bounds={self.grid_bounds}, start={self.start_position})"


# 测试代码
def test_ai_translator():
    """测试AI转换器"""
    translator = AITranslatorMCP()
    
    print("\n" + "=" * 80)
    print("📝 测试AI转换器")
    print("=" * 80)
    
    # 测试用例
    test_cases = [
        "Z字形飞行3米",
        "画个边长5米的正方形",
        "飞出字母A",
        "画汉字'王'",
        "先上升5米，然后Z字形3米，最后下降",
        "经过坐标(6,6,1), (7,7,2)",
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n【测试 {i}】")
        print(f"输入: {case}")
        
        # 生成转换指南
        guide = translator.create_conversion_guide(case)
        print(f"\n生成的转换指南（前300字符）:")
        print("─" * 80)
        print(guide[:300] + "...")
        print("─" * 80)
        
        print("\n⚠️ 注意：这个指南会作为MCP工具的返回值")
        print("AI阅读后会直接输出转换后的动作序列")
    
    # 显示支持的模式
    print("\n" + "=" * 80)
    print("📋 支持的轨迹模式分类")
    print("=" * 80)
    patterns = translator.get_supported_patterns()
    for category, items in patterns.items():
        print(f"\n{category}:")
        print("  " + ", ".join(items))
    
    # 显示示例转换
    print("\n" + "=" * 80)
    print("💡 转换示例")
    print("=" * 80)
    examples = translator.get_example_conversions()
    for i, example in enumerate(examples[:3], 1):
        print(f"\n示例 {i} ({example['type']})")
        print(f"  输入: {example['input']}")
        print(f"  分析: {example['analysis']}")
        print(f"  输出: {example['output']}")


if __name__ == "__main__":
    test_ai_translator()
