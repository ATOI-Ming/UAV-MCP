"""
三维栅格空间管理模块
支持障碍物管理、无人机位置跟踪、碰撞检测
"""

from typing import Tuple, List, Dict, Optional, Set
from enum import Enum
import json


class CellType(Enum):
    """栅格单元类型"""
    EMPTY = "empty"        # 空白栅格
    UAV = "uav"           # 无人机                            
    OBSTACLE = "obstacle"  # 障碍物


class GridCell:
    """栅格单元"""
    
    def __init__(self, position: Tuple[int, int, int], cell_type: CellType = CellType.EMPTY):
        self.position = position  # (x, y, z) 坐标
        self.cell_type = cell_type
        self.color = self._get_color()
    
    def _get_color(self) -> str:
        """获取单元格颜色"""
        color_map = {
            CellType.EMPTY: "white",
            CellType.UAV: "blue",
            CellType.OBSTACLE: "red"
        }
        return color_map[self.cell_type]
    
    def set_type(self, cell_type: CellType):
        """设置单元格类型"""
        self.cell_type = cell_type
        self.color = self._get_color()
    
    def is_walkable(self) -> bool:
        """是否可通行"""
        return self.cell_type != CellType.OBSTACLE
    
    def __repr__(self):
        return f"GridCell({self.position}, {self.cell_type.value})"


class GridSpace:
    """三维栅格空间管理器
    
    坐标系统：
    - 用户坐标：[0, 10] × [0, 10] × [0, 10]
    - 内部存储：[0, 10] × [0, 10] × [0, 10]
    - 转换公式： internal = user (直接映射)
    """
    
    def __init__(self, grid_size: Tuple[int, int, int] = (10, 10, 10)):
        """
        初始化栅格空间
        
        Args:
            grid_size: 空间大小 (x_size, y_size, z_size)
        """
        self.grid_size = grid_size
        self.offset = 0  # 坐标偏移量（改为0，直接映射）
        self.cells: Dict[Tuple[int, int, int], GridCell] = {}
        self.uav_position: Optional[Tuple[int, int, int]] = None
        self.obstacles: Set[Tuple[int, int, int]] = set()
        
        # 初始化所有栅格为空白
        self._initialize_cells()
    
    def _user_to_internal(self, pos: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """将用户坐标[0,10]转换为内部坐标[0,10]（直接映射）"""
        return (pos[0] + self.offset, pos[1] + self.offset, pos[2] + self.offset)
    
    def _internal_to_user(self, pos: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """将内部坐标[0,10]转换为用户坐标[0,10]（直接映射）"""
        return (pos[0] - self.offset, pos[1] - self.offset, pos[2] - self.offset)
    
    def _initialize_cells(self):
        """初始化所有栅格单元"""
        for x in range(self.grid_size[0]):
            for y in range(self.grid_size[1]):
                for z in range(self.grid_size[2]):
                    pos = (x, y, z)
                    self.cells[pos] = GridCell(pos, CellType.EMPTY)
    
    def is_valid_position(self, position: Tuple[int, int, int]) -> bool:
        """检查位置是否在有效范围内（用户坐标）"""
        x, y, z = position
        return (0 <= x <= 10 and
                0 <= y <= 10 and
                0 <= z <= 10)
    
    def add_obstacle(self, position: Tuple[int, int, int]) -> bool:
        """
        添加障碍物（用户坐标）
        
        Args:
            position: 障碍物坐标 (用户坐标)
            
        Returns:
            是否添加成功
        """
        if not self.is_valid_position(position):
            return False
        
        if position == self.uav_position:
            return False  # 不能在无人机位置添加障碍物
        
        # 转换为内部坐标
        internal_pos = self._user_to_internal(position)
        self.cells[internal_pos].set_type(CellType.OBSTACLE)
        self.obstacles.add(position)  # 用户坐标存储
        return True
    
    def add_obstacles(self, positions: List[Tuple[int, int, int]]) -> Tuple[int, List[str]]:
        """
        批量添加障碍物
        
        Args:
            positions: 障碍物坐标列表
            
        Returns:
            (成功数量, 错误信息列表)
        """
        success_count = 0
        errors = []
        
        for pos in positions:
            if self.add_obstacle(pos):
                success_count += 1
            else:
                errors.append(f"无法在 {pos} 添加障碍物")
        
        return success_count, errors
    
    def remove_obstacle(self, position: Tuple[int, int, int]) -> bool:
        """移除障碍物（用户坐标）"""
        if position in self.obstacles:
            internal_pos = self._user_to_internal(position)
            self.cells[internal_pos].set_type(CellType.EMPTY)
            self.obstacles.remove(position)
            return True
        return False
    
    def clear_obstacles(self):
        """清除所有障碍物"""
        for pos in list(self.obstacles):
            internal_pos = self._user_to_internal(pos)
            self.cells[internal_pos].set_type(CellType.EMPTY)
        self.obstacles.clear()
    
    def set_uav_position(self, position: Tuple[int, int, int]) -> bool:
        """
        设置无人机位置（用户坐标）
        
        Args:
            position: 新位置 (用户坐标)
            
        Returns:
            是否设置成功
        """
        if not self.is_valid_position(position):
            return False
        
        if position in self.obstacles:
            return False  # 不能放在障碍物位置
        
        # 清除旧位置
        if self.uav_position is not None:
            old_internal = self._user_to_internal(self.uav_position)
            self.cells[old_internal].set_type(CellType.EMPTY)
        
        # 设置新位置
        internal_pos = self._user_to_internal(position)
        self.cells[internal_pos].set_type(CellType.UAV)
        self.uav_position = position  # 用户坐标存储
        return True
    
    def is_path_clear(self, path: List[Tuple[int, int, int]]) -> Tuple[bool, Optional[Tuple[int, int, int]]]:
        """
        检查路径是否畅通（无障碍物）
        
        Args:
            path: 航点列表
            
        Returns:
            (是否畅通, 第一个碰撞点或None)
        """
        for waypoint in path:
            if not self.is_valid_position(waypoint):
                return False, waypoint
            
            if waypoint in self.obstacles:
                return False, waypoint
        
        return True, None
    
    def get_layer_data(self, z: int) -> Dict[str, any]:
        """
        获取某一层的数据
        
        Args:
            z: 层高度
            
        Returns:
            该层的栅格数据字典
        """
        if z < 0 or z >= self.grid_size[2]:
            return None
        
        layer_data = {
            "z_level": z,
            "size": (self.grid_size[0], self.grid_size[1]),
            "cells": [],
            "obstacles": [],
            "uav": None
        }
        
        for x in range(self.grid_size[0]):
            for y in range(self.grid_size[1]):
                pos = (x, y, z)
                cell = self.cells[pos]
                
                cell_info = {
                    "position": pos,
                    "type": cell.cell_type.value,
                    "color": cell.color
                }
                layer_data["cells"].append(cell_info)
                
                if cell.cell_type == CellType.OBSTACLE:
                    layer_data["obstacles"].append(pos)
                elif cell.cell_type == CellType.UAV:
                    layer_data["uav"] = pos
        
        return layer_data
    
    def get_all_layers_data(self) -> List[Dict]:
        """获取所有层的数据"""
        return [self.get_layer_data(z) for z in range(self.grid_size[2])]
    
    def get_obstacles_info(self) -> Dict:
        """获取障碍物统计信息"""
        # 按层分组
        obstacles_by_layer = {}
        for obs in self.obstacles:
            z = obs[2]
            if z not in obstacles_by_layer:
                obstacles_by_layer[z] = []
            obstacles_by_layer[z].append(obs)
        
        return {
            "total_count": len(self.obstacles),
            "by_layer": obstacles_by_layer,
            "positions": list(self.obstacles)
        }
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "grid_size": self.grid_size,
            "uav_position": self.uav_position,
            "obstacles": list(self.obstacles),
            "total_cells": len(self.cells)
        }
    
    def __repr__(self):
        return f"GridSpace({self.grid_size}, UAV:{self.uav_position}, Obstacles:{len(self.obstacles)})"


# 测试代码
if __name__ == "__main__":
    # 创建20x20x20的栅格空间
    grid = GridSpace((20, 20, 20))
    
    # 设置无人机初始位置 (1,1,1)
    grid.set_uav_position((1, 1, 1))
    print(f"无人机位置: {grid.uav_position}")
    
    # 添加一些障碍物
    obstacles = [
        (5, 5, 1),
        (6, 5, 1),
        (5, 6, 1),
        (10, 10, 2),
        (11, 10, 2)
    ]
    
    success, errors = grid.add_obstacles(obstacles)
    print(f"\n添加障碍物: 成功{success}个")
    if errors:
        print("错误:", errors)
    
    # 获取障碍物信息
    obs_info = grid.get_obstacles_info()
    print(f"\n障碍物统计: {obs_info['total_count']}个")
    print(f"按层分布: {obs_info['by_layer']}")
    
    # 测试路径检查
    test_path = [(1, 1, 1), (2, 2, 1), (3, 3, 1), (4, 4, 1)]
    is_clear, collision = grid.is_path_clear(test_path)
    print(f"\n路径检查: {'畅通' if is_clear else f'碰撞于{collision}'}")
    
    # 测试有障碍物的路径
    test_path2 = [(1, 1, 1), (5, 5, 1), (7, 7, 1)]
    is_clear2, collision2 = grid.is_path_clear(test_path2)
    print(f"路径检查2: {'畅通' if is_clear2 else f'碰撞于{collision2}'}")
    
    # 获取第1层数据
    layer1 = grid.get_layer_data(1)
    print(f"\n第1层数据: 障碍物{len(layer1['obstacles'])}个, UAV位置{layer1['uav']}")
