"""
航线规划器
管理无人机航点、路径验证和航线优化
支持障碍物检测和碰撞预防

注意：
- 碰撞检测：检测航点是否与障碍物冲突
- 路径重规划：由AI智能重规划器(ai_replan_with_obstacles)通过MCP工具完成
"""

from typing import List, Tuple, Dict, Optional
from config import GRID_SIZE, GRID_UNIT, ACTIONS

try:
    from core.grid_space import GridSpace
    GRID_SPACE_AVAILABLE = True
except ImportError:
    GRID_SPACE_AVAILABLE = False
    GridSpace = None


class FlightPlanner:
    """航线规划和管理（支持障碍物检测）"""
    
    def __init__(self, grid_size: Tuple[int, int, int] = GRID_SIZE, 
                 grid_space: Optional['GridSpace'] = None):
        self.grid_size = grid_size
        self.waypoints: List[Tuple[int, int, int]] = []
        self.current_position: Tuple[int, int, int] = (0, 0, 0)
        self.grid_space = grid_space  # 栅格空间引用（用于障碍物检测）
        self.collision_check_enabled = grid_space is not None
        
    def set_grid_space(self, grid_space: 'GridSpace'):
        """设置栅格空间（用于障碍物检测）"""
        self.grid_space = grid_space
        self.collision_check_enabled = True
    
    def set_start_position(self, position: Tuple[int, int, int]):
        """设置起始位置"""
        self.current_position = position
        self.waypoints = [position]
        
    def add_waypoint(self, waypoint: Tuple[int, int, int]) -> bool:
        """
        添加单个航点
        
        Args:
            waypoint: 航点坐标 (x, y, z)
            
        Returns:
            是否成功添加
        """
        if not self._is_valid_position(waypoint):
            return False
        
        # 检查障碍物碰撞
        if self.collision_check_enabled and self.grid_space:
            if waypoint in self.grid_space.obstacles:
                return False  # 航点与障碍物冲突
        
        self.waypoints.append(waypoint)
        self.current_position = waypoint
        return True
    
    def add_waypoints(self, waypoints: List[Tuple[int, int, int]]) -> Tuple[bool, str, Optional[Tuple[int, int, int]]]:
        """
        添加多个航点（带碰撞检测）
        
        Args:
            waypoints: 航点列表
            
        Returns:
            (是否成功, 消息, 第一个碰撞点或None)
            
        注意:
            - 如果检测到碰撞，返回(False, 错误信息, 碰撞点坐标)
            - AI可以使用ai_replan_with_obstacles工具进行重规划
            - 返回值为3个元素的元组，可以使用 _ 接收不需要的值
        """
        # 先进行基本验证
        for i, waypoint in enumerate(waypoints):
            if not self._is_valid_position(waypoint):
                return False, f"航点 {i} {waypoint} 超出边界", None
        
        # 检查障碍物碰撞
        if self.collision_check_enabled and self.grid_space:
            collision_index = None
            collision_point = None
            
            for i, waypoint in enumerate(waypoints):
                if waypoint in self.grid_space.obstacles:
                    collision_index = i
                    collision_point = waypoint
                    break
            
            # 发现碰撞，返回碰撞信息
            if collision_point is not None:
                print(f"\n[FlightPlanner] ⚠️ 检测到碰撞: 航点 {collision_index} {collision_point}")
                print(f"[FlightPlanner] 💡 建议: 使用 ai_replan_with_obstacles 工具进行智能重规划")
                return False, f"航点 {collision_index} {collision_point} 与障碍物冲突", collision_point
        
        # 无碰撞，直接添加
        self.waypoints.extend(waypoints)
        if waypoints:
            self.current_position = waypoints[-1]
        return True, "成功", None
    

    
    def check_path_collision(self, path: List[Tuple[int, int, int]]) -> Tuple[bool, Optional[Tuple[int, int, int]]]:
        """
        检查路径是否与障碍物碰撞
        
        Args:
            path: 航点列表
            
        Returns:
            (是否畅通, 第一个碰撞点或None)
        """
        if not self.collision_check_enabled or not self.grid_space:
            return True, None  # 未启用碰撞检测
        
        return self.grid_space.is_path_clear(path)
    
    def _is_valid_position(self, position: Tuple[int, int, int]) -> bool:
        """检查位置是否在有效范围内"""
        x, y, z = position
        return (0 <= x < self.grid_size[0] and 
                0 <= y < self.grid_size[1] and 
                0 <= z < self.grid_size[2])
    
    def get_path_info(self) -> Dict:
        """
        获取路径信息
        
        Returns:
            路径统计信息
        """
        if len(self.waypoints) < 2:
            return {
                "total_waypoints": len(self.waypoints),
                "total_distance": 0,
                "total_grids": 0,
                "start": self.waypoints[0] if self.waypoints else None,
                "end": self.waypoints[-1] if self.waypoints else None,
            }
        
        total_distance = 0.0
        for i in range(len(self.waypoints) - 1):
            dist = self._calculate_distance(self.waypoints[i], self.waypoints[i+1])
            total_distance += dist
        
        return {
            "total_waypoints": len(self.waypoints),
            "total_distance": total_distance,
            "total_grids": len(self.waypoints) - 1,
            "start": self.waypoints[0],
            "end": self.waypoints[-1],
        }
    
    def _calculate_distance(self, p1: Tuple[int, int, int], p2: Tuple[int, int, int]) -> float:
        """计算两点之间的曼哈顿距离"""
        return (abs(p2[0] - p1[0]) + abs(p2[1] - p1[1]) + abs(p2[2] - p1[2])) * GRID_UNIT
    
    def get_waypoints(self) -> List[Tuple[int, int, int]]:
        """获取所有航点"""
        return self.waypoints.copy()
    
    def clear_waypoints(self):
        """清除所有航点"""
        start = self.waypoints[0] if self.waypoints else (0, 0, 0)
        self.waypoints = [start]
        self.current_position = start
    
    def generate_action_sequence(self) -> List[Dict]:
        """
        根据航点生成动作序列
        
        Returns:
            动作序列
        """
        if len(self.waypoints) < 2:
            return []
        
        actions = []
        
        for i in range(len(self.waypoints) - 1):
            current = self.waypoints[i]
            next_point = self.waypoints[i + 1]
            
            # 计算差值
            dx = next_point[0] - current[0]
            dy = next_point[1] - current[1]
            dz = next_point[2] - current[2]
            
            # 确定动作类型（支持斜向移动）
            action_type = None
            action_cn = None
            
            # 先检查是否是斜向移动（平面斜向，dz=0）
            if dz == 0 and dx != 0 and dy != 0:
                # 斜向移动（4个方向）
                if dx > 0 and dy > 0:
                    action_type = "forward_right"
                    action_cn = "右上"
                elif dx < 0 and dy > 0:
                    action_type = "forward_left"
                    action_cn = "左上"
                elif dx > 0 and dy < 0:
                    action_type = "backward_right"
                    action_cn = "右下"
                elif dx < 0 and dy < 0:
                    action_type = "backward_left"
                    action_cn = "左下"
            # 再检查单轴移动
            elif dx > 0 and dy == 0 and dz == 0:
                action_type = "forward"
                action_cn = "前进"
            elif dx < 0 and dy == 0 and dz == 0:
                action_type = "backward"
                action_cn = "后退"
            elif dy > 0 and dx == 0 and dz == 0:
                action_type = "right"
                action_cn = "右移"
            elif dy < 0 and dx == 0 and dz == 0:
                action_type = "left"
                action_cn = "左移"
            elif dz > 0 and dx == 0 and dy == 0:
                action_type = "up"
                action_cn = "上升"
            elif dz < 0 and dx == 0 and dy == 0:
                action_type = "down"
                action_cn = "下降"
            else:
                action_type = "hover"
                action_cn = "悬停"
            
            actions.append({
                "action": action_type,
                "action_cn": action_cn,
                "from": current,
                "to": next_point,
                "grids": 1,
            })
        
        return actions


# 测试
if __name__ == "__main__":
    planner = FlightPlanner()
    planner.set_start_position((5, 5, 0))
    
    # 添加航点
    waypoints = [(5, 5, 1), (6, 5, 1), (7, 5, 1), (8, 5, 1), (8, 4, 1), (9, 4, 1)]
    success, msg, _ = planner.add_waypoints(waypoints)
    
    print(f"添加航点: {success}, {msg}")
    print(f"路径信息: {planner.get_path_info()}")
    print(f"动作序列: {planner.generate_action_sequence()}")
