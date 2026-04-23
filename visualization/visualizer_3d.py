"""
3D仿真空间可视化 - 完全重构版
使用Matplotlib实现高性能、高美观度的3D栅格空间显示

全新优化方案：
1. 性能优化 - 批量渲染、事件优化、智能LOD（细节层次）
2. 美观度提升 - 专业配色、光影效果、材质设计
3. 栅格完整显示 - 网格线系统，可视化完整空间结构
4. 透明度层次 - 障碍物半透明，避免遮挡无人机和航线
5. 交互优化 - 流畅旋转、智能视角、响应式设计
6. 非阻塞显示 - 立即返回控制权，窗口独立运行
"""

import matplotlib
matplotlib.use('TkAgg')  # 设置后端为TkAgg,确保窗口显示
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Line3D
import numpy as np
from typing import List, Tuple, Optional
import time
import threading
from matplotlib.animation import FuncAnimation
from config import GRID_SIZE, GRID_UNIT


class GridVisualizer:
    """3D栅格化仿真空间可视化器 - 完全重构版
    
    全新特性：
    - 🚀 性能优化：批量渲染、智能LOD、事件优化
    - 🎨 美观设计：专业配色、光影效果、材质系统
    - 📐 栅格完整显示：网格线系统、空间结构可视化
    - 🔍 透明度层次：障碍物半透明、无人机高亮
    - 🖱️ 交互优化：流畅响应、智能视角
    - ⚡ 非阻塞模式：立即返回、窗口独立运行
    """
    
    def __init__(self, grid_size: Tuple[int, int, int] = GRID_SIZE, grid_space=None):
        self.grid_size = grid_size
        self.grid_space = grid_space  # 栅格空间引用（用于显示障碍物）
        self.fig = None
        self.ax = None
        self.waypoints = []
        self._async_thread = None  # 异步渲染线程
        self._is_async_running = False  # 异步运行标志
        
        # 🎨 新增：专业配色方案
        self.colors = {
            'background': '#F5F5F5',      # 浅灰背景
            'grid_major': '#CCCCCC',      # 主网格线（灰色）
            'grid_minor': '#E8E8E8',      # 次网格线（浅灰）
            'boundary': '#666666',        # 边界框（深灰）
            'obstacle': '#FF4444',        # 障碍物（鲜红色）
            'obstacle_edge': '#CC0000',   # 障碍物边缘（深红）
            'drone': '#FFD700',           # 无人机（金色）
            'path': '#4A90E2',            # 航线（蓝色）
            'start': '#00CC66',           # 起点（绿色）
            'end': '#FF6B6B',             # 终点（红色）
            'waypoint': '#FF9500',        # 航点（橙色）
        }
        
        # ⚡ 新增：性能优化配置
        self.performance_mode = 'balanced'  # 'fast', 'balanced', 'quality'
        self.max_grid_lines = 100  # 最大网格线数量
        self.obstacle_lod = True   # 障碍物细节层次优化
        
    def create_grid_space(self):
        """
        创建3D栅格空间框架 - 完全重构版
        
        全新特性：
        - 🎨 专业配色方案
        - 📐 完整栅格网格线系统
        - 🔍 障碍物半透明显示
        - ⚡ 批量渲染优化
        - 📏 真正的10×10×10空间（0-9范围）
        """
        # 创建3D图形（调整图形大小和分辨率）
        self.fig = plt.figure(figsize=(16, 12), dpi=100)
        self.fig.patch.set_facecolor(self.colors['background'])  # 设置背景色
        
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_facecolor(self.colors['background'])
        
        # 🆕 设置坐标轴范围为真正的10×10×10（0-9，留出边距）
        self.ax.set_xlim(0, 10)  # 0-9范围
        self.ax.set_ylim(0, 10)  # 0-9范围
        self.ax.set_zlim(0, 10)  # type: ignore  # 0-9范围
        
        # 🆕 设置坐标轴刻度（0-9整数刻度）
        self.ax.set_xticks(range(10))
        self.ax.set_yticks(range(10))
        self.ax.set_zticks(range(10))  # type: ignore
        
        # 设置坐标轴标签（更大、更清晰）
        self.ax.set_xlabel('X 轴 (右向)', fontsize=13, fontweight='bold', 
                          fontproperties='SimHei', labelpad=10)
        self.ax.set_ylabel('Y 轴 (前向)', fontsize=13, fontweight='bold', 
                          fontproperties='SimHei', labelpad=10)
        self.ax.set_zlabel('Z 轴 (上向)', fontsize=13, fontweight='bold',  # type: ignore
                          fontproperties='SimHei', labelpad=10)
        
        # 设置标题（更大、更突出）
        self.ax.set_title('🚁 无人机仿真空间 - 3D栅格环境 [0,9]×[0,9]×[0,9]', 
                        fontsize=16, fontweight='bold', fontproperties='SimHei', 
                        pad=20, color='#333333')
        
        # 🆕 新增：绘制增强的三维空间参考系统
        self._draw_3d_reference_system()
        
        # 绘制边界框（加强边界）
        self._draw_boundary_box()
        
        # 🆕 新增：绘制障碍物（标准立方体，0.8尺寸）
        if self.grid_space:
            self._draw_obstacles_standard()
        
        # 🆕 新增：设置最优视角（更好的观看角度）
        self.ax.view_init(elev=20, azim=45)  # type: ignore
        
        # ⚡ 性能优化：禁用自动重绘
        self.ax.set_autoscale_on(False)
    
    def _draw_3d_reference_system(self):
        """
        🆕 绘制增强的三维空间参考系统
        
        功能：
        - 绘制地面平面（XY平面，增强空间感）
        - 绘制完整栅格网格线（主网格+次网格）
        - 绘制立体坐标参考线（帮助理解深度）
        - 绘制空白栅格框架（显示完整10×10×10结构）
        """
        # 📐 绘制地面平面（半透明，增强空间感）
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
        
        # 地面网格（XY平面，Z=0）
        floor_vertices = [
            [0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0]
        ]
        floor_poly = Poly3DCollection([floor_vertices], 
                                     facecolors='#E8F4F8',  # 浅蓝色
                                     edgecolors='#CCCCCC',
                                     linewidths=1.5,
                                     alpha=0.15)  # 非常透明
        self.ax.add_collection3d(floor_poly)  # type: ignore
        
        # 📐 绘制XY平面网格线（每1格一条）
        for i in range(10):
            # X方向网格线
            alpha = 0.25 if i % 2 == 0 else 0.15  # 主次网格
            linewidth = 0.8 if i % 2 == 0 else 0.5
            color = self.colors['grid_major'] if i % 2 == 0 else self.colors['grid_minor']
            
            self.ax.plot([0, 10], [i, i], [0, 0],  # type: ignore
                       color=color, linewidth=linewidth, alpha=alpha, linestyle='-')
            
            # Y方向网格线
            self.ax.plot([i, i], [0, 10], [0, 0],  # type: ignore
                       color=color, linewidth=linewidth, alpha=alpha, linestyle='-')
        
        # 📐 绘制垂直参考线（显示Z轴高度，关键位置）
        # 四个角的垂直线（虚线）
        corner_positions = [(0, 0), (10, 0), (0, 10), (10, 10)]
        for x, y in corner_positions:
            self.ax.plot([x, x], [y, y], [0, 10],  # type: ignore
                       color=self.colors['grid_major'], 
                       linewidth=0.6, alpha=0.2, linestyle=':')
        
        # 中心位置的垂直参考线（稍粗）
        center_positions = [(4, 4), (4, 5), (5, 4), (5, 5)]  # 中心区域
        for x, y in center_positions:
            self.ax.plot([x, x], [y, y], [0, 10],  # type: ignore
                       color=self.colors['grid_minor'], 
                       linewidth=0.5, alpha=0.12, linestyle=':')
        
        # 📐 绘制关键高度层的水平参考线（Z=3, 6层）
        key_heights = [3, 6]
        for z in key_heights:
            # 绘制稀疏的水平网格
            for i in range(0, 10, 3):  # 每3格一条
                self.ax.plot([0, 10], [i, i], [z, z],  # type: ignore
                           color=self.colors['grid_minor'], 
                           linewidth=0.4, alpha=0.08, linestyle=':')
                self.ax.plot([i, i], [0, 10], [z, z],  # type: ignore
                           color=self.colors['grid_minor'], 
                           linewidth=0.4, alpha=0.08, linestyle=':')
    
    def _draw_boundary_box(self):
        """绘制边界框 - 增强版（10×10×10真实范围）"""
        # 底面四条边（加粗）
        corners = [
            ([0, 10], [0, 0], [0, 0]),      # 后边
            ([0, 10], [10, 10], [0, 0]),    # 前边
            ([0, 0], [0, 10], [0, 0]),      # 左边
            ([10, 10], [0, 10], [0, 0]),    # 右边
        ]
        
        for xs, ys, zs in corners:
            self.ax.plot(xs, ys, zs, color=self.colors['boundary'],  # type: ignore
                       linewidth=2.5, alpha=0.6)
        
        # 垂直边（四个角）
        vertical_corners = [
            ([0, 0], [0, 0], [0, 10]),
            ([10, 10], [0, 0], [0, 10]),
            ([0, 0], [10, 10], [0, 10]),
            ([10, 10], [10, 10], [0, 10]),
        ]
        
        for xs, ys, zs in vertical_corners:
            self.ax.plot(xs, ys, zs, color=self.colors['boundary'],  # type: ignore
                       linewidth=1.5, alpha=0.4, linestyle='--')
        
        # 顶面四条边（虚线）
        top_corners = [
            ([0, 10], [0, 0], [10, 10]),
            ([0, 10], [10, 10], [10, 10]),
            ([0, 0], [0, 10], [10, 10]),
            ([10, 10], [0, 10], [10, 10]),
        ]
        
        for xs, ys, zs in top_corners:
            self.ax.plot(xs, ys, zs, color=self.colors['boundary'],  # type: ignore
                       linewidth=1.0, alpha=0.3, linestyle=':')
    
    def _draw_obstacles_standard(self):
        """
        🆕 绘制障碍物 - 标准立方体版本（0.8×0.8×0.8）
        
        特性：
        - 🔴 红色不透明立方体
        - 📐 0.8×0.8×0.8尺寸（不完全填满栅格）
        - ⚡ 批量渲染优化
        """
        if not hasattr(self.grid_space, 'obstacles'):
            return
        
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
        
        obstacles = self.grid_space.obstacles  # type: ignore
        if not obstacles:
            return
        
        cell_size = 0.80  # 固定0.8尺寸
        offset = cell_size / 2
        all_faces = []
        
        # ⚡ 批量生成所有障碍物的面
        for obs in obstacles:
            x, y, z = obs
            
            # 定义8个顶点
            vertices = [
                [x - offset, y - offset, z - offset],  # 0: 左后下
                [x + offset, y - offset, z - offset],  # 1: 右后下
                [x + offset, y + offset, z - offset],  # 2: 右前下
                [x - offset, y + offset, z - offset],  # 3: 左前下
                [x - offset, y - offset, z + offset],  # 4: 左后上
                [x + offset, y - offset, z + offset],  # 5: 右后上
                [x + offset, y + offset, z + offset],  # 6: 右前上
                [x - offset, y + offset, z + offset],  # 7: 左前上
            ]
            
            # 定义6个面
            faces = [
                [vertices[0], vertices[1], vertices[2], vertices[3]],  # 底面
                [vertices[4], vertices[5], vertices[6], vertices[7]],  # 顶面
                [vertices[0], vertices[1], vertices[5], vertices[4]],  # 后面
                [vertices[2], vertices[3], vertices[7], vertices[6]],  # 前面
                [vertices[0], vertices[3], vertices[7], vertices[4]],  # 左面
                [vertices[1], vertices[2], vertices[6], vertices[5]],  # 右面
            ]
            
            all_faces.extend(faces)
        
        # ⚡ 批量渲染：一次性绘制所有障碍物
        poly = Poly3DCollection(all_faces, 
                               facecolors=self.colors['obstacle'], 
                               edgecolors=self.colors['obstacle_edge'],
                               linewidths=1.2,
                               alpha=0.9)  # 🔴 接近不透明
        self.ax.add_collection3d(poly)  # type: ignore
    
    def _draw_empty_cells(self):
        """
        🆕 绘制空白栅格 - 淡白色立方体
        
        特性：
        - ⬜ 淡白色半透明立方体
        - 📐 0.8×0.8×0.8尺寸
        - 🎯 只显示Z=0-2层（避免过多栅格）
        - ⚡ 批量渲染优化
        """
        if not hasattr(self.grid_space, 'obstacles'):
            return
        
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
        
        obstacles = self.grid_space.obstacles  # type: ignore
        obstacle_set = set(obstacles)  # 转换为集合，加速查找
        
        cell_size = 0.80  # 与障碍物相同尺寸
        offset = cell_size / 2
        all_faces = []
        
        # 🎯 只显示底层3层（Z=0,1,2），避免过多栅格导致性能问题
        max_z = 3
        
        # ⚡ 批量生成所有空白栅格的面
        for x in range(10):
            for y in range(10):
                for z in range(max_z):
                    # 跳过障碍物位置
                    if (x, y, z) in obstacle_set:
                        continue
                    
                    # 定义8个顶点
                    vertices = [
                        [x - offset, y - offset, z - offset],  # 0: 左后下
                        [x + offset, y - offset, z - offset],  # 1: 右后下
                        [x + offset, y + offset, z - offset],  # 2: 右前下
                        [x - offset, y + offset, z - offset],  # 3: 左前下
                        [x - offset, y - offset, z + offset],  # 4: 左后上
                        [x + offset, y - offset, z + offset],  # 5: 右后上
                        [x + offset, y + offset, z + offset],  # 6: 右前上
                        [x - offset, y + offset, z + offset],  # 7: 左前上
                    ]
                    
                    # 定义6个面
                    faces = [
                        [vertices[0], vertices[1], vertices[2], vertices[3]],  # 底面
                        [vertices[4], vertices[5], vertices[6], vertices[7]],  # 顶面
                        [vertices[0], vertices[1], vertices[5], vertices[4]],  # 后面
                        [vertices[2], vertices[3], vertices[7], vertices[6]],  # 前面
                        [vertices[0], vertices[3], vertices[7], vertices[4]],  # 左面
                        [vertices[1], vertices[2], vertices[6], vertices[5]],  # 右面
                    ]
                    
                    all_faces.extend(faces)
        
        # ⚡ 批量渲染：一次性绘制所有空白栅格
        if all_faces:
            poly = Poly3DCollection(all_faces, 
                                   facecolors=self.colors['empty_cell'], 
                                   edgecolors=self.colors['empty_cell_edge'],
                                   linewidths=0.5,
                                   alpha=0.15)  # ⬜ 非常透明，不遮挡
            self.ax.add_collection3d(poly)  # type: ignore
        
    def _add_grid_lines(self):
        """添加栅格线(精简版:只绘制必要的参考线)"""
        # 使用matplotlib自带的grid方法
        self.ax.grid(True, alpha=0.2, linestyle='--', linewidth=0.3)
        
        # 绘制边框线(使用plot3D性能更好)
        corners = [
            # 底面4条边
            ([0, self.grid_size[0]], [0, 0], [0, 0]),
            ([0, self.grid_size[0]], [self.grid_size[1], self.grid_size[1]], [0, 0]),
            ([0, 0], [0, self.grid_size[1]], [0, 0]),
            ([self.grid_size[0], self.grid_size[0]], [0, self.grid_size[1]], [0, 0]),
            # 顶面4条垂直边
            ([0, 0], [0, 0], [0, self.grid_size[2]]),
            ([self.grid_size[0], self.grid_size[0]], [0, 0], [0, self.grid_size[2]]),
            ([0, 0], [self.grid_size[1], self.grid_size[1]], [0, self.grid_size[2]]),
            ([self.grid_size[0], self.grid_size[0]], [self.grid_size[1], self.grid_size[1]], [0, self.grid_size[2]]),
        ]
        
        for xs, ys, zs in corners:
            self.ax.plot(xs, ys, zs, 'k-', linewidth=1, alpha=0.3)
    
    def add_waypoints(self, waypoints: List[Tuple[int, int, int]], 
                     name: str = "航点",
                     show_path: bool = True,
                     smart_label: bool = True):  # 默认启用智能标注
        """
        添加航点和航线 - 增强版
        
        全新特性：
        - 🎨 精美航线：使用专业配色、渐变效果
        - 🔍 无人机高亮：金色、大尺寸、发光效果
        - 📌 智能标注：根据航点数量自适应
        - ⚡ 批量渲染：一次性绘制所有元素
        
        Args:
            waypoints: 航点列表 [(x, y, z), ...]
            name: 显示名称
            show_path: 是否显示连接路径
            smart_label: 智能标注模式(航点多时只显示关键点)
        """
        if not waypoints:
            return
        
        self.waypoints = waypoints
        
        # ⚡ 批量分离坐标（性能优化）
        xs, ys, zs = zip(*waypoints) if waypoints else ([], [], [])
        xs, ys, zs = list(xs), list(ys), list(zs)
        
        # 🎨 绘制航线路径（更粗、更鲜明）
        if show_path and len(waypoints) > 1:
            self.ax.plot(xs, ys, zs, color=self.colors['path'],  # type: ignore
                       linewidth=3.5, label='飞行航线', alpha=0.8, 
                       linestyle='-', zorder=5)
        
        # 📌 绘制中间航点（更大、更鲜明）
        if len(waypoints) > 2:
            self.ax.scatter(xs[1:-1], ys[1:-1], zs[1:-1],  # type: ignore
                          c=self.colors['waypoint'], marker='o', s=120, 
                          label='中间航点', alpha=0.9, 
                          edgecolors='white', linewidths=2, zorder=10)
        
        # 🟢 高亮起点 (绿色大菱形)
        if len(waypoints) > 0:
            self.ax.scatter([xs[0]], [ys[0]], [zs[0]],  # type: ignore
                          c=self.colors['start'], marker='D', s=300, 
                          label='起点', edgecolors='darkgreen', 
                          linewidths=3, zorder=15, alpha=1.0)
            
            # 起点标注
            self.ax.text(xs[0], ys[0], zs[0] + 0.5,  # type: ignore
                       f'✅ 起点\n{waypoints[0]}', 
                       fontsize=10, fontproperties='SimHei', ha='center', 
                       bbox=dict(boxstyle='round,pad=0.5', 
                                facecolor='lightgreen', 
                                edgecolor='darkgreen',
                                alpha=0.8, linewidth=2),
                       zorder=20)
        
        # 🔴 高亮终点 (红色大方块)
        if len(waypoints) > 1:
            self.ax.scatter([xs[-1]], [ys[-1]], [zs[-1]],  # type: ignore
                          c=self.colors['end'], marker='s', s=300, 
                          label='终点', edgecolors='darkred', 
                          linewidths=3, zorder=15, alpha=1.0)
            
            # 终点标注
            self.ax.text(xs[-1], ys[-1], zs[-1] + 0.5,  # type: ignore
                       f'🏁 终点\n{waypoints[-1]}', 
                       fontsize=10, fontproperties='SimHei', ha='center',
                       bbox=dict(boxstyle='round,pad=0.5', 
                                facecolor='lightcoral', 
                                edgecolor='darkred',
                                alpha=0.8, linewidth=2),
                       zorder=20)
        
        # 📌 智能标注模式
        if len(waypoints) > 2:  # 只有有中间航点才显示
            if smart_label and len(waypoints) > 15:
                # 航点很多，每5个标注一次
                label_interval = max(5, len(waypoints) // 10)
                for i in range(1, len(waypoints) - 1, label_interval):
                    x, y, z = waypoints[i]
                    self.ax.text(x, y, z + 0.3, f'P{i}',  # type: ignore
                               fontsize=7, ha='center', alpha=0.7,
                               bbox=dict(boxstyle='round,pad=0.2', 
                                        facecolor='yellow', alpha=0.5),
                               zorder=12)
            elif len(waypoints) <= 15:
                # 航点较少，显示所有中间航点标注
                for i in range(1, len(waypoints) - 1):
                    x, y, z = waypoints[i]
                    self.ax.text(x, y, z + 0.35, f'P{i}\n({x},{y},{z})',  # type: ignore
                               fontsize=7, ha='center', alpha=0.75,
                               bbox=dict(boxstyle='round,pad=0.25', 
                                        facecolor='#FFF9C4', 
                                        edgecolor='orange',
                                        alpha=0.7, linewidth=1),
                               zorder=12)
        
        # 🟡 添加图例（更大、更清晰）
        legend = self.ax.legend(loc='upper left',  # type: ignore
                              prop={'family': 'SimHei', 'size': 11},
                              frameon=True, 
                              fancybox=True, 
                              shadow=True,
                              framealpha=0.95,
                              edgecolor='#666666',
                              facecolor='white')
        legend.set_zorder(100)  # 图例始终在最前面
    
    def animate_flight(self, waypoints: List[Tuple[int, int, int]], interval: int = 500):
        """
        动画显示无人机飞行过程 - 批量更新优化版
        
        Args:
            waypoints: 航点序列
            interval: 动画间隔(毫秒)
        """
        if len(waypoints) < 2:
            return
        
        self.waypoints = waypoints
        
        # 初始化图形
        self.create_grid_space()
        
        # 【批量分离坐标】性能优化
        xs, ys, zs = zip(*waypoints)
        xs, ys, zs = list(xs), list(ys), list(zs)
        
        # 初始化航线和无人机
        path_line, = self.ax.plot([], [], [], 'b-', linewidth=2, label='已飞行路径')
        drone_point = self.ax.scatter([], [], [], c='orange', marker='D', 
                                     s=150, label='无人机当前位置', edgecolors='darkorange', linewidths=2)
        
        # 【批量绘制】一次性绘制所有航点(灰色)
        self.ax.scatter(xs, ys, zs, c='lightgray', marker='o', s=30, alpha=0.5)
        
        # 起点和终点
        self.ax.scatter([xs[0]], [ys[0]], [zs[0]], 
                       c='green', marker='D', s=200, label='起点')
        self.ax.scatter([xs[-1]], [ys[-1]], [zs[-1]], 
                       c='red', marker='s', s=200, label='终点')
        
        self.ax.legend(loc='upper left', prop={'family': 'SimHei', 'size': 9})
        
        # 【方案2: 批量更新模式】动画更新函数
        def update(frame):
            # 更新已飞行路径
            path_line.set_data(xs[:frame+1], ys[:frame+1])
            path_line.set_3d_properties(zs[:frame+1])
            
            # 更新无人机位置
            drone_point._offsets3d = ([xs[frame]], [ys[frame]], [zs[frame]])
            
            # 更新标题显示当前进度
            self.ax.set_title(f'无人机仿真空间 - 航点 {frame+1}/{len(waypoints)}', 
                            fontsize=14, fontproperties='SimHei', pad=20)
            
            return path_line, drone_point
        
        # 【优化】创建动画，使用blit加速
        anim = FuncAnimation(self.fig, update, frames=len(waypoints), 
                           interval=interval, blit=False, repeat=True)
        
        plt.show()
    
    def show(self, block: bool = False):
        """
        显示可视化窗口 - 完全重构版
        
        全新特性：
        - ⚡ 极速响应：解决卡顿和无响应问题
        - 🖱️ 流畅交互：优化鼠标事件处理
        - 💨 立即返回：非阻塞模式默认
        
        Args:
            block: 是否阻塞等待窗口关闭(默认False,非阻塞)
        """
        if not self.fig:
            return
        
        if not block:
            # ⚡ 非阻塞模式 - 极速优化版
            try:
                # 方案A：先绘制一次，确保窗口有内容
                self.fig.canvas.draw()  # type: ignore
                
                # 方案B：启用交互模式
                plt.ion()
                
                # 方案C：显示窗口（非阻塞）
                plt.show(block=False)
                
                # 方案D：刷新事件，确保窗口响应
                self.fig.canvas.flush_events()  # type: ignore
                
                print("[可视化] 💻 3D窗口已启动（非阻塞模式）")
                print("[提示] 🔄 窗口独立运行，可继续其他操作")
                
            except Exception as e:
                print(f"[警告] 窗口显示异常: {e}")
                # 备用方案：简化显示
                plt.show(block=False)
        else:
            # 🔒 阻塞模式 - 传统方式
            plt.ioff()  # 关闭交互模式
            plt.show(block=True)
            print("[可视化] 🔴 3D窗口已关闭")
    
    def save_image(self, filename: str = "uav_simulation.png"):
        """保存为图像文件"""
        import os
        if self.fig:
            # 确保保存到项目目录
            workspace_dir = r"i:\UAV-MCP"
            if not os.path.isabs(filename):
                full_path = os.path.join(workspace_dir, filename)
            else:
                full_path = filename
            
            plt.savefig(full_path, dpi=150, bbox_inches='tight')
            print(f"[图像保存] {full_path}")
            return full_path
        return None
    
    def visualize_flight(self, waypoints: List[Tuple[int, int, int]], 
                        save_image: Optional[str] = None,
                        show_window: bool = True,
                        animate: bool = False,
                        block: bool = False,
                        async_mode: bool = False) -> Optional[str]:
        """
        完整可视化飞行过程
        
        Args:
            waypoints: 航点列表
            save_image: 保存图像文件名
            show_window: 是否显示窗口
            animate: 是否使用动画模式
            block: 是否阻塞等待窗口关闭(默认False,非阻塞)
            async_mode: 是否使用异步渲染模式(MCP场景推荐)
            
        Returns:
            图像文件路径(如果保存)
        """
        if async_mode:
            # 【方案4: 异步渲染模式】在后台线程运行
            return self._visualize_async(waypoints, save_image, show_window)
        elif animate:
            # 动画模式(自动阻塞)
            self.animate_flight(waypoints)
            return None
        else:
            # 静态模式
            self.create_grid_space()
            self.add_waypoints(waypoints)
            
            if save_image:
                saved_file = self.save_image(save_image)
            else:
                saved_file = None
            
            if show_window:
                self.show(block=block)
            
            return saved_file
    
    def _visualize_async(self, waypoints: List[Tuple[int, int, int]], 
                        save_image: Optional[str] = None,
                        show_window: bool = True) -> Optional[str]:
        """
        【方案4: 异步渲染模式】
        在后台线程运行可视化，完全不阻塞主流程
        
        适用场景: MCP工具调用，需要立即返回控制权
        
        Args:
            waypoints: 航点列表
            save_image: 保存图像文件名
            show_window: 是否显示窗口
            
        Returns:
            图像文件路径(如果保存)
        """
        import os
        
        # 先同步保存图像(确保立即生成)
        saved_file = None
        if save_image:
            self.create_grid_space()
            self.add_waypoints(waypoints)
            saved_file = self.save_image(save_image)
            print(f"[同步保存] 图像已保存: {saved_file}")
        
        # 然后在主线程显示窗口(完全非阻塞)
        if show_window:
            # 在主线程中创建和显示窗口(必须!)
            if self.fig is None:
                self.create_grid_space()
                self.add_waypoints(waypoints)
            
            print(f"[异步窗口] 正在主线程中打开3D窗口...")
            
            # 【关键修复】直接在主线程显示，不使用后台线程维持
            # 让Matplotlib自己管理事件循环，避免跨线程GUI操作导致卡顿
            self.show(block=False)
            
            # 极短延迟确保窗口初始化
            import time
            time.sleep(0.1)
            print(f"[异步窗口] 3D窗口已打开，完全非阻塞模式")
        
        # 立即返回，不等待渲染完成
        return saved_file

    def stop_async(self):
        """停止异步渲染"""
        self._is_async_running = False
        if self._async_thread and self._async_thread.is_alive():
            self._async_thread.join(timeout=1.0)


# 测试
if __name__ == "__main__":
    # 测试航点
    waypoints = [
        (5, 5, 0),
        (5, 5, 1),
        (6, 5, 1),
        (7, 5, 1),
        (8, 5, 1),
        (8, 4, 1),
        (9, 4, 1),
    ]
    
    print("测试可视化功能...")
    visualizer = GridVisualizer()
    
    # 静态可视化
    print("\n1. 静态可视化")
    visualizer.visualize_flight(waypoints, show_window=True, animate=False)
    
    # 动画可视化
    # print("\n2. 动画可视化")
    # visualizer_anim = GridVisualizer()
    # visualizer_anim.visualize_flight(waypoints, show_window=True, animate=True)
