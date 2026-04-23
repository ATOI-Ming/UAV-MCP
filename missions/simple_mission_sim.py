"""
无人机任务执行代码
生成时间: 2025-12-10 21:25:22
自动生成 - 请勿手动修改
"""

import time
from typing import Tuple, List
import matplotlib
matplotlib.use("TkAgg")  # 设置GUI后端
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# 配置参数
GRID_UNIT = 1.0  # 网格单位长度 (米)
MOVEMENT_SPEED = 0.5  # 移动速度 (米/秒)
HOVER_TIME = 2.0  # 悬停时间 (秒)

class RealtimeVisualizer:
    """实时可视化器(带丰富文字标注)"""
    
    def __init__(self, grid_size: Tuple[int, int, int] = (10, 10, 10)):
        self.grid_size = grid_size
        self.trajectory = []  # 存储飞行轨迹
        self.waypoint_count = 0  # 航点计数器
        self.text_objects = []  # 存储文字对象
        self.start_marker = None  # 起点标记
        
        # 创建3D图形
        plt.ion()  # 开启交互模式
        self.fig = plt.figure(figsize=(12, 9))
        self.ax = self.fig.add_subplot(111, projection="3d")
        
        # 设置坐标轴
        self.ax.set_xlim(0, grid_size[0])
        self.ax.set_ylim(0, grid_size[1])
        self.ax.set_zlim(0, grid_size[2])
        self.ax.set_xlabel("X (米) - 前后", fontsize=10, fontproperties="SimHei")
        self.ax.set_ylabel("Y (米) - 左右", fontsize=10, fontproperties="SimHei")
        self.ax.set_zlabel("Z (米) - 上下", fontsize=10, fontproperties="SimHei")
        self.ax.set_title("无人机实时飞行轨迹 | 航点: 0 | 距离: 0.0m", 
                         fontsize=12, fontproperties="SimHei", pad=15)
        
        # 绘制网格
        self.ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
        
        # 初始化轨迹线和当前位置点
        self.trajectory_line, = self.ax.plot([], [], [], "b-", linewidth=2.5, 
                                              label="飞行轨迹", alpha=0.7)
        self.current_point = self.ax.scatter([], [], [], c="red", marker="o", 
                                            s=120, label="当前位置", 
                                            edgecolors="darkred", linewidths=2)
        
        # 添加图例
        self.ax.legend(loc="upper right", prop={"family": "SimHei", "size": 9})
        self.ax.view_init(elev=25, azim=45)
        
        plt.show(block=False)
        plt.pause(0.1)
    
    def update(self, position: List[float]):
        """更新可视化(添加新位置+文字标注)"""
        self.trajectory.append(position.copy())
        self.waypoint_count += 1
        
        if len(self.trajectory) > 0:
            # 更新轨迹线
            xs = [p[0] for p in self.trajectory]
            ys = [p[1] for p in self.trajectory]
            zs = [p[2] for p in self.trajectory]
            
            self.trajectory_line.set_data(xs, ys)
            self.trajectory_line.set_3d_properties(zs)
            
            # 更新当前位置点
            self.current_point._offsets3d = ([xs[-1]], [ys[-1]], [zs[-1]])
            
            # 添加文字标注
            if len(self.trajectory) == 1:
                # 起点标注(绿色框)
                self.start_marker = self.ax.scatter([xs[0]], [ys[0]], [zs[0]], 
                                                   c="green", marker="D", s=150, 
                                                   edgecolors="darkgreen", linewidths=2,
                                                   label="起点", zorder=10)
                start_text = self.ax.text(xs[0], ys[0], zs[0] + 0.5, 
                                         f"起点\n({xs[0]:.1f},{ys[0]:.1f},{zs[0]:.1f})", 
                                         fontsize=9, ha="center", color="darkgreen",
                                         fontproperties="SimHei",
                                         bbox=dict(boxstyle="round,pad=0.3", 
                                                  facecolor="lightgreen", alpha=0.6),
                                         zorder=10)
                self.text_objects.append(start_text)
            
            # 每3个点添加一次航点标注(黄色框)
            if self.waypoint_count > 1 and self.waypoint_count % 3 == 0:
                waypoint_text = self.ax.text(xs[-1], ys[-1], zs[-1] + 0.3, 
                                            f"P{self.waypoint_count}\n({xs[-1]:.1f},{ys[-1]:.1f},{zs[-1]:.1f})", 
                                            fontsize=7, ha="center", color="orange",
                                            bbox=dict(boxstyle="round,pad=0.2", 
                                                     facecolor="yellow", alpha=0.4),
                                            zorder=9)
                self.text_objects.append(waypoint_text)
            
            # 计算飞行总距离
            total_distance = 0.0
            for i in range(1, len(self.trajectory)):
                dx = self.trajectory[i][0] - self.trajectory[i-1][0]
                dy = self.trajectory[i][1] - self.trajectory[i-1][1]
                dz = self.trajectory[i][2] - self.trajectory[i-1][2]
                total_distance += (dx**2 + dy**2 + dz**2)**0.5
            
            # 更新动态标题
            self.ax.set_title(f"无人机实时飞行轨迹 | 航点: {self.waypoint_count} | 距离: {total_distance:.1f}m", 
                            fontsize=12, fontproperties="SimHei", pad=15)
            
            # 刷新图形
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
            plt.pause(0.05)  # 短暂停顿,让窗口响应
    
    def close(self):
        """关闭可视化窗口(添加终点标注)"""
        if len(self.trajectory) > 0:
            # 添加终点标注(红色框)
            xs = [p[0] for p in self.trajectory]
            ys = [p[1] for p in self.trajectory]
            zs = [p[2] for p in self.trajectory]
            
            end_marker = self.ax.scatter([xs[-1]], [ys[-1]], [zs[-1]], 
                                        c="red", marker="s", s=150, 
                                        edgecolors="darkred", linewidths=2,
                                        label="终点", zorder=10)
            end_text = self.ax.text(xs[-1], ys[-1], zs[-1] + 0.5, 
                                   f"终点\n({xs[-1]:.1f},{ys[-1]:.1f},{zs[-1]:.1f})", 
                                   fontsize=9, ha="center", color="darkred",
                                   fontproperties="SimHei",
                                   bbox=dict(boxstyle="round,pad=0.3", 
                                            facecolor="lightcoral", alpha=0.6),
                                   zorder=10)
            self.text_objects.append(end_text)
            
            # 更新图例
            self.ax.legend(loc="upper right", prop={"family": "SimHei", "size": 9})
            
            # 最后一次刷新
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
        
        plt.ioff()
        plt.show(block=True)  # 最后保持窗口显示

class UAVController:
    """无人机控制器 - 模拟版本(带实时可视化)"""
    
    def __init__(self, visualize: bool = True):
        self.position = [5.0, 5.0, 0.0]  # 当前位置 (x, y, z) - 与配置文件INITIAL_POSITION一致
        self.is_flying = False
        self.visualize = visualize
        
        # 创建可视化器
        if self.visualize:
            self.visualizer = RealtimeVisualizer()
            self.visualizer.update(self.position)  # 添加起始点
    
    def takeoff(self):
        """起飞"""
        print("[UAV] 起飞...")
        self.is_flying = True
        time.sleep(1.0)
        print("[UAV] 起飞完成")
    
    def land(self):
        """降落"""
        print("[UAV] 降落...")
        time.sleep(1.0)
        self.is_flying = False
        print("[UAV] 降落完成")
        
        # 关闭可视化
        if self.visualize and hasattr(self, "visualizer"):
            print("[VIS] 关闭可视化窗口,按Ctrl+C退出...")
            self.visualizer.close()
    
    def move(self, direction: str, distance: float):
        """
        移动指定距离
        
        Args:
            direction: 方向 (forward/backward/left/right/up/down/forward_right/forward_left/backward_right/backward_left)
            distance: 距离 (米)
        """
        if not self.is_flying and direction not in ["up"]:
            print("[UAV] 错误: 无人机未起飞")
            return
        
        duration = distance / MOVEMENT_SPEED
        print(f"[UAV] {direction} {distance}米 (耗时 {duration:.1f}秒)")
        
        # 更新位置
        if direction == "forward":
            self.position[0] += distance
        elif direction == "backward":
            self.position[0] -= distance
        elif direction == "left":
            self.position[1] -= distance
        elif direction == "right":
            self.position[1] += distance
        elif direction == "up":
            self.position[2] += distance
            if not self.is_flying:  # 第一次上升时自动起飞
                self.is_flying = True
        elif direction == "down":
            self.position[2] -= distance
        # 斜向移动（平面斜向，45度角）
        elif direction == "forward_right":
            self.position[0] += distance
            self.position[1] += distance
        elif direction == "forward_left":
            self.position[0] -= distance
            self.position[1] += distance
        elif direction == "backward_right":
            self.position[0] += distance
            self.position[1] -= distance
        elif direction == "backward_left":
            self.position[0] -= distance
            self.position[1] -= distance
        
        time.sleep(duration)
        print(f"[UAV] 当前位置: ({self.position[0]:.1f}, {self.position[1]:.1f}, {self.position[2]:.1f})")
        
        # 更新可视化
        if self.visualize and hasattr(self, "visualizer"):
            self.visualizer.update(self.position)
    
    def hover(self, duration: float = HOVER_TIME):
        """悬停"""
        print(f"[UAV] 悬停 {duration}秒")
        time.sleep(duration)
        print("[UAV] 悬停结束")

def execute_mission():
    """执行无人机任务(带实时可视化)"""
    # 检测是否在交互式环境中运行
    import sys
    import os
    
    # 【环境检测优化】支持通过环境变量控制可视化
    # MCP环境下：自动禁用可视化以避免阻塞
    # 手动执行：启用可视化以便实时查看
    if os.environ.get("DISABLE_UAV_VISUALIZATION", "").lower() == "true":
        enable_visualization = False
        print("[信息] 环境变量已禁用可视化（DISABLE_UAV_VISUALIZATION=true）")
    elif hasattr(sys.stdin, "isatty") and sys.stdin.isatty():
        enable_visualization = True  # 交互式终端，启用可视化
    else:
        enable_visualization = False  # 非交互式环境（如MCP），禁用可视化
        print("[信息] 检测到非交互式环境，自动禁用实时可视化")
    
    uav = UAVController(visualize=enable_visualization)  # 根据环境决定是否启用可视化
    
    print("=" * 50)
    print("开始执行无人机任务")
    print("=" * 50)
    
    # 起飞
    uav.takeoff()
    
    # 步骤 1: 上升 1格 (1.0米)
    uav.move("up", 1.0)
    
    # 步骤 2: 上升 1格 (1.0米)
    uav.move("up", 1.0)
    
    # 步骤 3: 上升 1格 (1.0米)
    uav.move("up", 1.0)
    
    # 步骤 4: 上升 1格 (1.0米)
    uav.move("up", 1.0)
    
    # 步骤 5: 下降 1格 (1.0米)
    uav.move("down", 1.0)
    
    # 步骤 6: 下降 1格 (1.0米)
    uav.move("down", 1.0)
    
    # 步骤 7: 后退 1格 (1.0米)
    uav.move("backward", 1.0)
    
    # 步骤 8: 后退 1格 (1.0米)
    uav.move("backward", 1.0)
    
    # 步骤 9: 后退 1格 (1.0米)
    uav.move("backward", 1.0)
    
    # 降落
    uav.land()
    
    print("=" * 50)
    print("任务执行完成")
    print("=" * 50)

if __name__ == "__main__":
    try:
        execute_mission()
    except KeyboardInterrupt:
        print("\n[UAV] 任务中断")
    except Exception as e:
        print(f"[UAV] 错误: {e}")