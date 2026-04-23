"""
命令解析器
将自然语言命令转换为无人机动作序列
"""

import re
from typing import List, Tuple, Dict
from config import ACTION_NAMES_CN, GRID_UNIT


class CommandParser:
    """解析自然语言命令为无人机动作序列"""
    
    def __init__(self):
        # 数字映射 (支持中文数字)
        self.number_map = {
            "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
            "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
        }
        
    def parse_command(self, command: str) -> List[Dict]:
        """
        解析命令字符串
        
        Args:
            command: 自然语言命令,如 "上升一米,前进3米,左移一米"
            
        Returns:
            动作列表,每个动作包含 {action: str, distance: int}
        """
        actions = []
        
        # 去除空格,按逗号或句号分割（支持中英文标点）
        command = command.replace(" ", "")
        # 支持: 中文逗号，、英文逗号,、中文句号。、英文句号.、分号;、顿号、、换行
        segments = re.split(r'[,，。.;；、\n]', command)
        
        for segment in segments:
            if not segment.strip():
                continue
                
            action = self._parse_single_action(segment)
            if action:
                actions.append(action)
                
        return actions
    
    def _parse_single_action(self, segment: str) -> Dict:
        """
        解析单个动作段
        
        Args:
            segment: 单个动作描述,如 "上升一米" 或 "前进3米"
            
        Returns:
            动作字典 {action: str, distance: int, grids: int}
        """
        # 匹配模式: 动作 + 数字 + 单位
        # 支持: "上升1米", "上升一米", "前进3米", "悬停"
        
        # 先查找动作词
        action_word = None
        action_type = None
        
        for cn_name, en_name in ACTION_NAMES_CN.items():
            if cn_name in segment:
                action_word = cn_name
                action_type = en_name
                break
        
        if not action_type:
            return None
        
        # 悬停没有距离
        if action_type == "hover":
            return {
                "action": action_type,
                "action_cn": action_word,
                "distance": 0,
                "grids": 1,  # 悬停占用1个时间单位
            }
        
        # 提取距离
        # 匹配数字 (阿拉伯数字或中文数字)
        distance = 1  # 默认1米
        grids = 1     # 默认1格
        
        # 提取阿拉伯数字
        numbers = re.findall(r'\d+', segment)
        if numbers:
            distance = int(numbers[0])
        else:
            # 提取中文数字
            for cn_num, value in self.number_map.items():
                if cn_num in segment:
                    distance = value
                    break
        
        # 转换为网格数 (1米 = 1格)
        grids = int(distance / GRID_UNIT)
        if grids == 0:
            grids = 1  # 至少移动1格
        
        return {
            "action": action_type,
            "action_cn": action_word,
            "distance": distance,
            "grids": grids,
        }
    
    def actions_to_waypoints(self, actions: List[Dict], start_pos: Tuple[int, int, int]) -> List[Tuple[int, int, int]]:
        """
        将动作序列转换为航点序列
        
        Args:
            actions: 动作列表
            start_pos: 起始位置 (x, y, z)
            
        Returns:
            航点列表 [(x, y, z), ...]
        """
        from config import ACTIONS
        
        waypoints = [start_pos]
        current_pos = list(start_pos)
        
        for action in actions:
            action_type = action["action"]
            grids = action["grids"]
            
            if action_type not in ACTIONS:
                continue
            
            # 获取移动向量
            direction = ACTIONS[action_type]
            
            # 按网格数移动
            for _ in range(grids):
                current_pos[0] += direction[0]
                current_pos[1] += direction[1]
                current_pos[2] += direction[2]
                waypoints.append(tuple(current_pos))
        
        return waypoints


# 测试函数
def test_parser():
    parser = CommandParser()
    
    # 测试简单命令
    print("测试1: 上升一米")
    result = parser.parse_command("上升一米")
    print(result)
    
    # 测试复杂命令
    print("\n测试2: 上升一米,前进3米,左移一米,前进一米")
    result = parser.parse_command("上升一米,前进3米,左移一米,前进一米")
    print(result)
    
    # 测试航点生成
    print("\n测试3: 生成航点")
    waypoints = parser.actions_to_waypoints(result, (5, 5, 0))
    print(waypoints)


if __name__ == "__main__":
    test_parser()
