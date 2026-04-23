"""
无人机配置文件
定义仿真空间参数和无人机基本参数
"""

# 仿真空间配置
GRID_SIZE = (11, 11, 11)  # 空间大小 (X右, Y前, Z上) - 支持[0,10]范围
GRID_UNIT = 1.0  # 每个网格单位长度 (米)
GRID_CELL_SIZE = 0.8  # 栅格可视化尺寸 (0.8留出0.2间隙)
GRID_OFFSET = 0  # 坐标偏移量，[0,10]直接映射到[0,10]

# 无人机运动参数
MOVEMENT_SPEED = 0.5  # 移动速度 (米/秒)
HOVER_TIME = 2.0  # 悬停时间 (秒)

# 坐标系统说明
# X轴: 向右为正，向左为负
# Y轴: 向前为正，向后为负  
# Z轴: 向上为正，向下为负
# 四象限分层结构

# 基本动作定义
ACTIONS = {
    "forward": (0, 1, 0),    # 前进 (Y+)
    "backward": (0, -1, 0),  # 后退 (Y-)
    "left": (-1, 0, 0),      # 左移 (X-)
    "right": (1, 0, 0),      # 右移 (X+)
    "up": (0, 0, 1),         # 上升 (Z+)
    "down": (0, 0, -1),      # 下降 (Z-)
    "hover": (0, 0, 0),      # 悬停
    # 斜向移动动作（平面斜向，45度角）
    "forward_right": (1, 1, 0),   # 右上 (X+, Y+)
    "forward_left": (-1, 1, 0),   # 左上 (X-, Y+)
    "backward_right": (1, -1, 0), # 右下 (X+, Y-)
    "backward_left": (-1, -1, 0), # 左下 (X-, Y-)
}

# 动作中文映射
ACTION_NAMES_CN = {
    "前进": "forward",
    "后退": "backward",
    "左移": "left",
    "右移": "right",
    "上升": "up",
    "下降": "down",
    "悬停": "hover",
    # 斜向移动（平面斜向）
    "右上": "forward_right",
    "左上": "forward_left",
    "右下": "backward_right",
    "左下": "backward_left",
}

# 无人机初始位置
INITIAL_POSITION = (5, 5, 0)  # 起始位置 (5,5,0) - 地图中心
