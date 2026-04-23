"""
AI智能重规划器 (MCP服务版本)

设计理念：
1. 与ai_translator_mcp.py设计完全一致
2. 输入：用户原始轨迹描述 + 障碍物坐标列表
3. 输出：规避障碍物的新轨迹指令
4. 核心：通过AI理解能力重新规划，而非A*算法

工作流程：
用户轨迹 + 障碍物信息 → AI重规划器 → 生成转换指南 → AI理解并输出新指令
"""

from typing import List, Tuple, Dict, Optional


class AIReplannerMCP:
    """AI智能重规划器 - 基于AI理解的障碍物规避"""
    
    def __init__(self):
        """初始化重规划器"""
        self.grid_bounds = (0, 10)  # [0, 10] × [0, 10]
        self.start_position = (5, 5, 0)  # 起点
    
    def create_replanning_guide(self, 
                                original_trajectory: str,
                                obstacles: List[Tuple[int, int, int]],
                                collision_points: Optional[List[Tuple[int, int, int]]] = None) -> str:
        """
        创建AI重规划指南（MCP工具返回内容）
        
        与ai_translator_mcp.create_conversion_guide()设计完全一致，
        只是增加了障碍物信息和碰撞点提示
        
        Args:
            original_trajectory: 用户原始轨迹描述（如"右移4米,前进3米"）
            obstacles: 障碍物坐标列表 [(x1,y1,z1), (x2,y2,z2), ...]
            collision_points: 碰撞点坐标列表（可选）
            
        Returns:
            转换指南文本（引导AI完成重规划）
        """
        
        guide_lines = []
        guide_lines.append("🤖 **AI智能重规划 - 障碍物规避轨迹生成**\n")
        guide_lines.append("─" * 80)
        guide_lines.append(f"\n📝 **原始轨迹指令**: {original_trajectory}\n")
        
        # 显示障碍物信息
        guide_lines.append("🚧 **环境障碍物信息**:")
        if obstacles:
            guide_lines.append(f"  - 障碍物总数: {len(obstacles)} 个")
            guide_lines.append(f"  - 障碍物坐标:")
            
            # 按层分组显示
            obstacles_by_layer = {}
            for obs in obstacles:
                z = obs[2]
                if z not in obstacles_by_layer:
                    obstacles_by_layer[z] = []
                obstacles_by_layer[z].append(obs)
            
            for z in sorted(obstacles_by_layer.keys()):
                obs_list = obstacles_by_layer[z]
                guide_lines.append(f"    • 第{z}层: {obs_list}")
        else:
            guide_lines.append(f"  - ✅ 空间内无障碍物")
        
        guide_lines.append("")
        
        # 显示碰撞点（如果有）
        if collision_points:
            guide_lines.append("⚠️ **检测到的碰撞点**:")
            for i, point in enumerate(collision_points, 1):
                guide_lines.append(f"  {i}. {point}")
            guide_lines.append("")
        
        guide_lines.append("🎯 **你的任务**: 重新规划飞行轨迹，确保绕过所有障碍物\n")
        guide_lines.append("─" * 80)
        guide_lines.append("")
        
        # 环境信息（与AI转换器一致）
        guide_lines.append("📐 **栅格空间环境**:")
        guide_lines.append(f"  - 起点位置: {self.start_position} （地面中心）")
        guide_lines.append(f"  - 空间范围: X∈[{self.grid_bounds[0]},{self.grid_bounds[1]}]米, Y∈[{self.grid_bounds[0]},{self.grid_bounds[1]}]米, Z∈[{self.grid_bounds[0]},{self.grid_bounds[1]}]米")
        guide_lines.append("  - 坐标系统:")
        guide_lines.append("    • X轴: 左(负) ← 0 → 右(正)")
        guide_lines.append("    • Y轴: 后(负) ← 0 → 前(正)")
        guide_lines.append("    • Z轴: 下(负) ← 0 → 上(正)")
        guide_lines.append("")
        
        # 可用动作（与AI转换器一致）
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
        
        # 重规划策略指导
        guide_lines.append("🧠 **避障策略建议**:")
        guide_lines.append("  1. **平面绕行**: 在同一高度层绕过障碍物")
        guide_lines.append("     • 识别障碍物位置，选择左侧或右侧绕行")
        guide_lines.append("     • 示例：障碍在(6,5,1)，可从(6,6,1)或(6,4,1)绕过")
        guide_lines.append("  2. **上升绕过**: 先上升到安全高度，越过障碍区")
        guide_lines.append("     • 计算障碍物最高层，上升到更高层")
        guide_lines.append("     • 示例：第1层有障碍，可上升到第2层或第3层再平移")
        guide_lines.append("  3. **下降绕过**: 先下降到更低层，绕过障碍区")
        guide_lines.append("     • 如果目标在低层，可以先下降再绕行")
        guide_lines.append("  4. **组合策略**: 结合上升、绕行、下降等动作")
        guide_lines.append("     • 示例：上升2米 → 右移绕过 → 前进 → 下降2米")
        guide_lines.append("  5. **优先原则**: 尽量保持路径简洁，减少不必要的转折")
        guide_lines.append("     • 优先选择最短的绕行路径")
        guide_lines.append("     • 避免复杂的之字形路径\n")
        
        guide_lines.append("─" * 80)
        guide_lines.append("")
        
        # 输出格式要求（与AI转换器一致）
        guide_lines.append("📋 **输出格式要求**:")
        guide_lines.append("  ✅ 只输出动作序列，不要任何前缀、解释或说明")
        guide_lines.append("  ✅ 使用逗号分隔各个动作")
        guide_lines.append("  ✅ 每个动作格式: `动作类型X米` 或 `悬停X秒`")
        guide_lines.append("  ✅ 确保从起点(5,5,0)开始，不超出边界[0,10]×[0,10]")
        guide_lines.append("  ✅ 确保所有航点都不在障碍物坐标上")
        guide_lines.append("  ✅ 输出示例格式: `上升2米,右移3米,前进3米,下降2米`\n")
        
        guide_lines.append("─" * 80)
        guide_lines.append("")
        
        # 重规划提示
        guide_lines.append(f"\n💭 **请重新规划以下轨迹**: \"{original_trajectory}\"\n")
        guide_lines.append("**重规划步骤**:")
        guide_lines.append("  1️⃣ **模拟原始轨迹**:")
        guide_lines.append("     - 从起点(5,5,0)开始，逐步执行原始动作")
        guide_lines.append("     - 记录每个动作后会到达的坐标点")
        guide_lines.append("  2️⃣ **检测碰撞点**:")
        guide_lines.append("     - 对比每个经过点与障碍物坐标")
        guide_lines.append("     - 标记所有碰撞的坐标点")
        guide_lines.append("  3️⃣ **分析障碍物分布**:")
        guide_lines.append("     - 识别障碍物的形状（点状、线状、面状）")
        guide_lines.append("     - 判断障碍物在哪些层、哪些区域")
        guide_lines.append("  4️⃣ **选择避障策略**:")
        guide_lines.append("     - 如果障碍物在单层：优先平面绕行")
        guide_lines.append("     - 如果障碍物跨多层：考虑上升/下降绕过")
        guide_lines.append("     - 如果障碍物密集：选择最简洁的组合策略")
        guide_lines.append("  5️⃣ **生成新动作序列**:")
        guide_lines.append("     - 将绕障策略转换为具体动作（上升、前进、右移等）")
        guide_lines.append("     - 确保新路径不经过任何障碍物坐标")
        guide_lines.append("     - 验证所有坐标在[0,10]×[0,10]范围内")
        guide_lines.append("  6️⃣ **输出结果**:")
        guide_lines.append("     - 直接输出新的动作序列（格式: 动作1,动作2,动作3）")
        guide_lines.append("     - 不要添加任何解释、前缀或后缀\n")
        
        guide_lines.append("─" * 80)
        guide_lines.append("\n✅ **请直接输出重规划后的动作序列**:")
        guide_lines.append("")
        
        return "\n".join(guide_lines)
    
    def parse_obstacles_from_json(self, obstacles_str: str) -> List[Tuple[int, int, int]]:
        """
        从 JSON 字符串解析障碍物坐标
        
        Args:
            obstacles_str: JSON格式的障碍物坐标字符串
            
        Returns:
            障碍物坐标列表
        """
        import json
        
        try:
            obstacles = json.loads(obstacles_str)
            # 确保每个元素是三元组
            result = []
            for obs in obstacles:
                if isinstance(obs, (list, tuple)) and len(obs) == 3:
                    result.append(tuple(obs))
            return result
        except:
            return []
    
    def validate_replanned_trajectory(self, 
                                     trajectory: str,
                                     obstacles: List[Tuple[int, int, int]]) -> Tuple[bool, str]:
        """
        验证重规划后的轨迹是否有效
        
        Args:
            trajectory: 重规划后的动作序列
            obstacles: 障碍物坐标列表
            
        Returns:
            (是否有效, 错误信息)
        """
        if not trajectory or not trajectory.strip():
            return False, "轨迹为空"
        
        # 基本动作关键词
        valid_actions = ['上升', '下降', '前进', '后退', '左移', '右移', '悬停']
        
        # 检查是否包含有效动作
        has_action = any(action in trajectory for action in valid_actions)
        if not has_action:
            return False, f"未识别到有效动作，需包含: {', '.join(valid_actions)}"
        
        # 检查是否包含单位
        has_unit = '米' in trajectory or '秒' in trajectory
        if not has_unit:
            return False, "动作必须包含距离单位（米）或时间单位（秒）"
        
        return True, "轨迹格式正确"
    
    def create_mcp_tool_description(self) -> Dict:
        """
        创建MCP工具描述（用于注册到server.py）
        
        Returns:
            工具描述字典
        """
        return {
            "name": "ai_replan_with_obstacles",
            "description": """
🤖 AI智能重规划 - 障碍物规避轨迹生成

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

【输入格式】
- original_trajectory: 原始动作序列字符串
  例如: "上升一米,右移4米,前进3米"
  
- obstacles: 障碍物坐标JSON字符串
  例如: "[(6,5,1), (7,5,1), (8,5,1)]"
  
- collision_points: 碰撞点坐标JSON字符串（可选）
  例如: "[(6,5,1)]"

【输出格式】
标准飞行动作序列，例如："上升2米,右移1米,前进4米,左移1米,下降2米"
可直接传递给parse_command解析。

【与AI转换器的区别】
- ai_translate_flight: 将抽象描述转为动作序列（无障碍物考虑）
- ai_replan_with_obstacles: 结合障碍物重新规划轨迹（避障）

【使用场景】
- parse_command检测到路径碰撞后调用
- 需要绕过障碍物重新规划路径
- AI理解环境信息并生成安全轨迹

【注意事项】
- 必须提供障碍物坐标列表
- 输出轨迹需确保不经过任何障碍物坐标
- 所有轨迹必须在[0,10]×[0,10]空间内
            """,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "original_trajectory": {
                        "type": "string",
                        "description": "原始轨迹的动作序列，如'上升一米,右移4米,前进3米'"
                    },
                    "obstacles": {
                        "type": "string",
                        "description": "障碍物坐标JSON字符串，如'[(6,5,1), (7,5,1)]'"
                    },
                    "collision_points": {
                        "type": "string",
                        "description": "碰撞点坐标JSON字符串（可选），如'[(6,5,1)]'",
                        "default": "[]"
                    }
                },
                "required": ["original_trajectory", "obstacles"]
            }
        }
    
    def __repr__(self):
        return f"AIReplannerMCP(bounds={self.grid_bounds}, start={self.start_position})"


# 测试代码
def test_ai_replanner():
    """测试AI重规划器"""
    replanner = AIReplannerMCP()
    
    print("\n" + "=" * 80)
    print("📝 测试AI智能重规划器")
    print("=" * 80)
    
    # 测试场景1: 简单障碍物
    print("\n【测试场景1】简单障碍物绕行")
    original_trajectory = "上升一米,右移4米"
    obstacles = [(6, 5, 1), (7, 5, 1)]
    collision_points = [(6, 5, 1)]
    
    print(f"原始轨迹: {original_trajectory}")
    print(f"障碍物: {obstacles}")
    print(f"碰撞点: {collision_points}")
    
    guide = replanner.create_replanning_guide(
        original_trajectory,
        obstacles,
        collision_points
    )
    
    print(f"\n生成的重规划指南（前500字符）:")
    print("─" * 80)
    print(guide[:500] + "...")
    print("─" * 80)
    
    # 测试场景2: 复杂多层障碍物
    print("\n【测试场景2】多层障碍物")
    original_trajectory = "上升2米,右移3米,前进3米"
    obstacles = [
        (6, 5, 1), (7, 5, 1), (8, 5, 1),  # 第1层障碍墙
        (6, 6, 2), (7, 6, 2),              # 第2层障碍
    ]
    
    print(f"原始轨迹: {original_trajectory}")
    print(f"障碍物: {obstacles}")
    
    guide = replanner.create_replanning_guide(
        original_trajectory,
        obstacles
    )
    
    print(f"\n✅ 重规划指南生成成功")
    print(f"引导内容长度: {len(guide)} 字符")
    
    # 测试MCP工具描述
    print("\n【MCP工具描述】")
    tool_desc = replanner.create_mcp_tool_description()
    print(f"工具名称: {tool_desc['name']}")
    print(f"必需参数: {tool_desc['inputSchema']['required']}")


if __name__ == "__main__":
    test_ai_replanner()
