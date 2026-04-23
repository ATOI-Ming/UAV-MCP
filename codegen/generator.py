"""
无人机代码生成器
将航线和动作序列转换为可执行的无人机控制代码
"""

from typing import List, Dict, Tuple
from datetime import datetime
from config import MOVEMENT_SPEED, HOVER_TIME, GRID_UNIT


class UAVCodeGenerator:
    """无人机控制代码生成器"""
    
    def __init__(self):
        self.speed = MOVEMENT_SPEED
        self.hover_time = HOVER_TIME
        self.grid_unit = GRID_UNIT
    
    def generate_from_waypoints_dual(self, waypoints: List[Tuple[int, int, int]], 
                                    base_filename: str = "uav_mission") -> Tuple[str, str]:
        """
        生成仿真版和DroneKit版两个代码文件
        
        Args:
            waypoints: 航点列表
            base_filename: 基础文件名（不含扩展名）
            
        Returns:
            (仿真文件路径, DroneKit文件路径)
        """
        import os
        workspace_dir = r"i:\UAV-MCP"
        
        # 生成仿真版本（原有逻辑）
        sim_file = f"{base_filename}_sim.py"
        if not os.path.isabs(sim_file):
            sim_file = os.path.join(workspace_dir, sim_file)
        self.generate_from_waypoints(waypoints, sim_file)
        
        # 生成DroneKit版本
        try:
            from codegen.dronekit_generator import DroneKitCodeGenerator
            
            dronekit_gen = DroneKitCodeGenerator()
            dronekit_file = f"{base_filename}_dronekit.py"
            if not os.path.isabs(dronekit_file):
                dronekit_file = os.path.join(workspace_dir, dronekit_file)
            
            dronekit_gen._generate_dronekit_version(waypoints, dronekit_file)
            
            return sim_file, dronekit_file
            
        except ImportError as e:
            print(f"[警告] 无法导入DroneKit代码生成器: {e}")
            return sim_file, None
    
    def generate_from_actions(self, actions: List[Dict], 
                             output_file: str = "uav_mission.py") -> str:
        """
        从动作序列生成代码
        
        Args:
            actions: 动作列表,每个动作包含 {action, action_cn, grids, ...}
            output_file: 输出文件名
            
        Returns:
            生成的代码内容
        """
        code_lines = []
        
        # 文件头
        code_lines.extend(self._generate_header())
        
        # 导入部分
        code_lines.extend(self._generate_imports())
        
        # 配置参数
        code_lines.extend(self._generate_config())
        
        # 无人机控制类
        code_lines.extend(self._generate_uav_class())
        
        # 任务函数
        code_lines.extend(self._generate_mission_function(actions))
        
        # 主函数
        code_lines.extend(self._generate_main())
        
        # 生成完整代码
        code = "\n".join(code_lines)
        
        # 保存到文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        return code
    
    def generate_from_waypoints(self, waypoints: List[Tuple[int, int, int]], 
                               output_file: str = "uav_mission.py") -> str:
        """
        从航点序列生成代码
        
        Args:
            waypoints: 航点列表 [(x, y, z), ...]
            output_file: 输出文件名
            
        Returns:
            生成的代码内容
        """
        # 将航点转换为动作
        actions = self._waypoints_to_actions(waypoints)
        return self.generate_from_actions(actions, output_file)
    
    def _waypoints_to_actions(self, waypoints: List[Tuple[int, int, int]]) -> List[Dict]:
        """将航点转换为动作序列（支持斜向移动）"""
        actions = []
        
        for i in range(len(waypoints) - 1):
            current = waypoints[i]
            next_point = waypoints[i + 1]
            
            dx = next_point[0] - current[0]
            dy = next_point[1] - current[1]
            dz = next_point[2] - current[2]
            
            # 支持斜向移动（与 flight_planner.py 逻辑一致）
            if dz == 0 and dx != 0 and dy != 0:
                # 斜向移动（4个方向）
                if dx > 0 and dy > 0:
                    action_type, action_cn = "forward_right", "右上"
                elif dx < 0 and dy > 0:
                    action_type, action_cn = "forward_left", "左上"
                elif dx > 0 and dy < 0:
                    action_type, action_cn = "backward_right", "右下"
                elif dx < 0 and dy < 0:
                    action_type, action_cn = "backward_left", "左下"
            elif dx > 0 and dy == 0 and dz == 0:
                action_type, action_cn = "forward", "前进"
            elif dx < 0 and dy == 0 and dz == 0:
                action_type, action_cn = "backward", "后退"
            elif dy > 0 and dx == 0 and dz == 0:
                action_type, action_cn = "right", "右移"
            elif dy < 0 and dx == 0 and dz == 0:
                action_type, action_cn = "left", "左移"
            elif dz > 0 and dx == 0 and dy == 0:
                action_type, action_cn = "up", "上升"
            elif dz < 0 and dx == 0 and dy == 0:
                action_type, action_cn = "down", "下降"
            else:
                action_type, action_cn = "hover", "悬停"
            
            actions.append({
                "action": action_type,
                "action_cn": action_cn,
                "grids": 1,
                "from": current,
                "to": next_point,
            })
        
        return actions
    
    def _generate_header(self) -> List[str]:
        """生成文件头"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return [
            '"""',
            '无人机任务执行代码',
            f'生成时间: {timestamp}',
            '自动生成 - 请勿手动修改',
            '"""',
            '',
        ]
    
    def _generate_imports(self) -> List[str]:
        """生成导入语句"""
        return [
            'import time',
            'from typing import Tuple, List',
            'import matplotlib',
            'matplotlib.use("TkAgg")  # 设置GUI后端',
            'import matplotlib.pyplot as plt',
            'from mpl_toolkits.mplot3d import Axes3D',
            '',
        ]
    
    def _generate_config(self) -> List[str]:
        """生成配置参数"""
        return [
            '# 配置参数',
            f'GRID_UNIT = {self.grid_unit}  # 网格单位长度 (米)',
            f'MOVEMENT_SPEED = {self.speed}  # 移动速度 (米/秒)',
            f'HOVER_TIME = {self.hover_time}  # 悬停时间 (秒)',
            '',
        ]
    
    def _generate_uav_class(self) -> List[str]:
        """生成无人机控制类(带实时可视化)"""
        return [
            'class RealtimeVisualizer:',
            '    """实时可视化器(带丰富文字标注)"""',
            '    ',
            '    def __init__(self, grid_size: Tuple[int, int, int] = (10, 10, 10)):',
            '        self.grid_size = grid_size',
            '        self.trajectory = []  # 存储飞行轨迹',
            '        self.waypoint_count = 0  # 航点计数器',
            '        self.text_objects = []  # 存储文字对象',
            '        self.start_marker = None  # 起点标记',
            '        ',
            '        # 创建3D图形',
            '        plt.ion()  # 开启交互模式',
            '        self.fig = plt.figure(figsize=(12, 9))',
            '        self.ax = self.fig.add_subplot(111, projection="3d")',
            '        ',
            '        # 设置坐标轴',
            '        self.ax.set_xlim(0, grid_size[0])',
            '        self.ax.set_ylim(0, grid_size[1])',
            '        self.ax.set_zlim(0, grid_size[2])',
            '        self.ax.set_xlabel("X (米) - 前后", fontsize=10, fontproperties="SimHei")',
            '        self.ax.set_ylabel("Y (米) - 左右", fontsize=10, fontproperties="SimHei")',
            '        self.ax.set_zlabel("Z (米) - 上下", fontsize=10, fontproperties="SimHei")',
            '        self.ax.set_title("无人机实时飞行轨迹 | 航点: 0 | 距离: 0.0m", ',
            '                         fontsize=12, fontproperties="SimHei", pad=15)',
            '        ',
            '        # 绘制网格',
            '        self.ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)',
            '        ',
            '        # 初始化轨迹线和当前位置点',
            '        self.trajectory_line, = self.ax.plot([], [], [], "b-", linewidth=2.5, ',
            '                                              label="飞行轨迹", alpha=0.7)',
            '        self.current_point = self.ax.scatter([], [], [], c="red", marker="o", ',
            '                                            s=120, label="当前位置", ',
            '                                            edgecolors="darkred", linewidths=2)',
            '        ',
            '        # 添加图例',
            '        self.ax.legend(loc="upper right", prop={"family": "SimHei", "size": 9})',
            '        self.ax.view_init(elev=25, azim=45)',
            '        ',
            '        plt.show(block=False)',
            '        plt.pause(0.1)',
            '    ',
            '    def update(self, position: List[float]):',
            '        """更新可视化(添加新位置+文字标注)"""',
            '        self.trajectory.append(position.copy())',
            '        self.waypoint_count += 1',
            '        ',
            '        if len(self.trajectory) > 0:',
            '            # 更新轨迹线',
            '            xs = [p[0] for p in self.trajectory]',
            '            ys = [p[1] for p in self.trajectory]',
            '            zs = [p[2] for p in self.trajectory]',
            '            ',
            '            self.trajectory_line.set_data(xs, ys)',
            '            self.trajectory_line.set_3d_properties(zs)',
            '            ',
            '            # 更新当前位置点',
            '            self.current_point._offsets3d = ([xs[-1]], [ys[-1]], [zs[-1]])',
            '            ',
            '            # 添加文字标注',
            '            if len(self.trajectory) == 1:',
            '                # 起点标注(绿色框)',
            '                self.start_marker = self.ax.scatter([xs[0]], [ys[0]], [zs[0]], ',
            '                                                   c="green", marker="D", s=150, ',
            '                                                   edgecolors="darkgreen", linewidths=2,',
            '                                                   label="起点", zorder=10)',
            '                start_text = self.ax.text(xs[0], ys[0], zs[0] + 0.5, ',
            '                                         f"起点\\n({xs[0]:.1f},{ys[0]:.1f},{zs[0]:.1f})", ',
            '                                         fontsize=9, ha="center", color="darkgreen",',
            '                                         fontproperties="SimHei",',
            '                                         bbox=dict(boxstyle="round,pad=0.3", ',
            '                                                  facecolor="lightgreen", alpha=0.6),',
            '                                         zorder=10)',
            '                self.text_objects.append(start_text)',
            '            ',
            '            # 每3个点添加一次航点标注(黄色框)',
            '            if self.waypoint_count > 1 and self.waypoint_count % 3 == 0:',
            '                waypoint_text = self.ax.text(xs[-1], ys[-1], zs[-1] + 0.3, ',
            '                                            f"P{self.waypoint_count}\\n({xs[-1]:.1f},{ys[-1]:.1f},{zs[-1]:.1f})", ',
            '                                            fontsize=7, ha="center", color="orange",',
            '                                            bbox=dict(boxstyle="round,pad=0.2", ',
            '                                                     facecolor="yellow", alpha=0.4),',
            '                                            zorder=9)',
            '                self.text_objects.append(waypoint_text)',
            '            ',
            '            # 计算飞行总距离',
            '            total_distance = 0.0',
            '            for i in range(1, len(self.trajectory)):',
            '                dx = self.trajectory[i][0] - self.trajectory[i-1][0]',
            '                dy = self.trajectory[i][1] - self.trajectory[i-1][1]',
            '                dz = self.trajectory[i][2] - self.trajectory[i-1][2]',
            '                total_distance += (dx**2 + dy**2 + dz**2)**0.5',
            '            ',
            '            # 更新动态标题',
            '            self.ax.set_title(f"无人机实时飞行轨迹 | 航点: {self.waypoint_count} | 距离: {total_distance:.1f}m", ',
            '                            fontsize=12, fontproperties="SimHei", pad=15)',
            '            ',
            '            # 刷新图形',
            '            self.fig.canvas.draw()',
            '            self.fig.canvas.flush_events()',
            '            plt.pause(0.05)  # 短暂停顿,让窗口响应',
            '    ',
            '    def close(self):',
            '        """关闭可视化窗口(添加终点标注)"""',
            '        if len(self.trajectory) > 0:',
            '            # 添加终点标注(红色框)',
            '            xs = [p[0] for p in self.trajectory]',
            '            ys = [p[1] for p in self.trajectory]',
            '            zs = [p[2] for p in self.trajectory]',
            '            ',
            '            end_marker = self.ax.scatter([xs[-1]], [ys[-1]], [zs[-1]], ',
            '                                        c="red", marker="s", s=150, ',
            '                                        edgecolors="darkred", linewidths=2,',
            '                                        label="终点", zorder=10)',
            '            end_text = self.ax.text(xs[-1], ys[-1], zs[-1] + 0.5, ',
            '                                   f"终点\\n({xs[-1]:.1f},{ys[-1]:.1f},{zs[-1]:.1f})", ',
            '                                   fontsize=9, ha="center", color="darkred",',
            '                                   fontproperties="SimHei",',
            '                                   bbox=dict(boxstyle="round,pad=0.3", ',
            '                                            facecolor="lightcoral", alpha=0.6),',
            '                                   zorder=10)',
            '            self.text_objects.append(end_text)',
            '            ',
            '            # 更新图例',
            '            self.ax.legend(loc="upper right", prop={"family": "SimHei", "size": 9})',
            '            ',
            '            # 最后一次刷新',
            '            self.fig.canvas.draw()',
            '            self.fig.canvas.flush_events()',
            '        ',
            '        plt.ioff()',
            '        plt.show(block=True)  # 最后保持窗口显示',
            '',
            'class UAVController:',
            '    """无人机控制器 - 模拟版本(带实时可视化)"""',
            '    ',
            '    def __init__(self, visualize: bool = True):',
            '        self.position = [5.0, 5.0, 0.0]  # 当前位置 (x, y, z) - 与配置文件INITIAL_POSITION一致',
            '        self.is_flying = False',
            '        self.visualize = visualize',
            '        ',
            '        # 创建可视化器',
            '        if self.visualize:',
            '            self.visualizer = RealtimeVisualizer()',
            '            self.visualizer.update(self.position)  # 添加起始点',
            '    ',
            '    def takeoff(self):',
            '        """起飞"""',
            '        print("[UAV] 起飞...")',
            '        self.is_flying = True',
            '        time.sleep(1.0)',
            '        print("[UAV] 起飞完成")',
            '    ',
            '    def land(self):',
            '        """降落"""',
            '        print("[UAV] 降落...")',
            '        time.sleep(1.0)',
            '        self.is_flying = False',
            '        print("[UAV] 降落完成")',
            '        ',
            '        # 关闭可视化',
            '        if self.visualize and hasattr(self, "visualizer"):',
            '            print("[VIS] 关闭可视化窗口,按Ctrl+C退出...")',
            '            self.visualizer.close()',
            '    ',
            '    def move(self, direction: str, distance: float):',
            '        """',
            '        移动指定距离',
            '        ',
            '        Args:',
            '            direction: 方向 (forward/backward/left/right/up/down/forward_right/forward_left/backward_right/backward_left)',
            '            distance: 距离 (米)',
            '        """',
            '        if not self.is_flying and direction not in ["up"]:',
            '            print("[UAV] 错误: 无人机未起飞")',
            '            return',
            '        ',
            '        duration = distance / MOVEMENT_SPEED',
            '        print(f"[UAV] {direction} {distance}米 (耗时 {duration:.1f}秒)")',
            '        ',
            '        # 更新位置',
            '        if direction == "forward":',
            '            self.position[0] += distance',
            '        elif direction == "backward":',
            '            self.position[0] -= distance',
            '        elif direction == "left":',
            '            self.position[1] -= distance',
            '        elif direction == "right":',
            '            self.position[1] += distance',
            '        elif direction == "up":',
            '            self.position[2] += distance',
            '            if not self.is_flying:  # 第一次上升时自动起飞',
            '                self.is_flying = True',
            '        elif direction == "down":',
            '            self.position[2] -= distance',
            '        # 斜向移动（平面斜向，45度角）',
            '        elif direction == "forward_right":',
            '            self.position[0] += distance',
            '            self.position[1] += distance',
            '        elif direction == "forward_left":',
            '            self.position[0] -= distance',
            '            self.position[1] += distance',
            '        elif direction == "backward_right":',
            '            self.position[0] += distance',
            '            self.position[1] -= distance',
            '        elif direction == "backward_left":',
            '            self.position[0] -= distance',
            '            self.position[1] -= distance',
            '        ',
            '        time.sleep(duration)',
            '        print(f"[UAV] 当前位置: ({self.position[0]:.1f}, {self.position[1]:.1f}, {self.position[2]:.1f})")',
            '        ',
            '        # 更新可视化',
            '        if self.visualize and hasattr(self, "visualizer"):',
            '            self.visualizer.update(self.position)',
            '    ',
            '    def hover(self, duration: float = HOVER_TIME):',
            '        """悬停"""',
            '        print(f"[UAV] 悬停 {duration}秒")',
            '        time.sleep(duration)',
            '        print("[UAV] 悬停结束")',
            '',
        ]
    
    def _generate_mission_function(self, actions: List[Dict]) -> List[str]:
        """生成任务执行函数(带实时可视化)"""
        lines = [
            'def execute_mission():',
            '    """执行无人机任务(带实时可视化)"""',
            '    # 检测是否在交互式环境中运行',
            '    import sys',
            '    import os',
            '    ',
            '    # 【环境检测优化】支持通过环境变量控制可视化',
            '    # MCP环境下：自动禁用可视化以避免阻塞',
            '    # 手动执行：启用可视化以便实时查看',
            '    if os.environ.get("DISABLE_UAV_VISUALIZATION", "").lower() == "true":',
            '        enable_visualization = False',
            '        print("[信息] 环境变量已禁用可视化（DISABLE_UAV_VISUALIZATION=true）")',
            '    elif hasattr(sys.stdin, "isatty") and sys.stdin.isatty():',
            '        enable_visualization = True  # 交互式终端，启用可视化',
            '    else:',
            '        enable_visualization = False  # 非交互式环境（如MCP），禁用可视化',
            '        print("[信息] 检测到非交互式环境，自动禁用实时可视化")',
            '    ',
            '    uav = UAVController(visualize=enable_visualization)  # 根据环境决定是否启用可视化',
            '    ',
            '    print("=" * 50)',
            '    print("开始执行无人机任务")',
            '    print("=" * 50)',
            '    ',
            '    # 起飞',
            '    uav.takeoff()',
            '    ',
        ]
        
        # 生成每个动作的代码
        for i, action in enumerate(actions):
            action_type = action["action"]
            action_cn = action.get("action_cn", action_type)
            grids = action.get("grids", 1)
            distance = grids * self.grid_unit
            
            lines.append(f'    # 步骤 {i+1}: {action_cn} {grids}格 ({distance}米)')
            
            if action_type == "hover":
                lines.append(f'    uav.hover()')
            elif action_type in ["forward", "backward", "left", "right", "up", "down", 
                               "forward_right", "forward_left", "backward_right", "backward_left"]:
                lines.append(f'    uav.move("{action_type}", {distance})')
            
            lines.append('    ')
        
        lines.extend([
            '    # 降落',
            '    uav.land()',
            '    ',
            '    print("=" * 50)',
            '    print("任务执行完成")',
            '    print("=" * 50)',
            '',
        ])
        
        return lines
    
    def _generate_main(self) -> List[str]:
        """生成主函数"""
        return [
            'if __name__ == "__main__":',
            '    try:',
            '        execute_mission()',
            '    except KeyboardInterrupt:',
            '        print("\\n[UAV] 任务中断")',
            '    except Exception as e:',
            '        print(f"[UAV] 错误: {e}")',
        ]


# 测试
if __name__ == "__main__":
    generator = UAVCodeGenerator()
    
    # 测试动作序列
    actions = [
        {"action": "up", "action_cn": "上升", "grids": 1},
        {"action": "forward", "action_cn": "前进", "grids": 3},
        {"action": "left", "action_cn": "左移", "grids": 1},
        {"action": "forward", "action_cn": "前进", "grids": 1},
    ]
    
    code = generator.generate_from_actions(actions, "test_mission.py")
    print("代码已生成到 test_mission.py")
    print("\n生成的代码:")
    print(code)
