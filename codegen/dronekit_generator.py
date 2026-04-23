"""
DroneKit无人机代码生成器
生成适用于真实无人机的控制代码（基于DroneKit-Python）
"""

from typing import List, Dict, Tuple
from datetime import datetime
from config import MOVEMENT_SPEED, HOVER_TIME, GRID_UNIT


class DroneKitCodeGenerator:
    """DroneKit无人机控制代码生成器
    
    生成两种模式的代码：
    1. 仿真模式 (uav_mission_sim.py) - 保持原有仿真逻辑
    2. 真实模式 (uav_mission_dronekit.py) - DroneKit真实无人机控制
    """
    
    def __init__(self):
        self.speed = MOVEMENT_SPEED
        self.hover_time = HOVER_TIME
        self.grid_unit = GRID_UNIT
    
    def generate_both_versions(self, waypoints: List[Tuple[int, int, int]], 
                               base_filename: str = "uav_mission"):
        """
        生成仿真版和DroneKit版两个代码文件
        
        Args:
            waypoints: 航点列表
            base_filename: 基础文件名（不含扩展名）
        """
        # 生成仿真版本（保持原有逻辑）
        sim_file = f"{base_filename}_sim.py"
        self._generate_simulation_version(waypoints, sim_file)
        
        # 生成DroneKit版本
        dronekit_file = f"{base_filename}_dronekit.py"
        self._generate_dronekit_version(waypoints, dronekit_file)
        
        return sim_file, dronekit_file
    
    def _generate_simulation_version(self, waypoints: List[Tuple[int, int, int]], 
                                    output_file: str):
        """生成仿真版本（使用原有code_generator逻辑）"""
        from code_generator import UAVCodeGenerator
        
        generator = UAVCodeGenerator()
        generator.generate_from_waypoints(waypoints, output_file)
        
        print(f"[生成] 仿真版本代码: {output_file}")
    
    def _generate_dronekit_version(self, waypoints: List[Tuple[int, int, int]], 
                                   output_file: str):
        """生成DroneKit真实无人机版本"""
        actions = self._waypoints_to_actions(waypoints)
        
        code_lines = []
        
        # 文件头
        code_lines.extend(self._generate_header())
        
        # 导入部分
        code_lines.extend(self._generate_imports())
        
        # 配置参数
        code_lines.extend(self._generate_config())
        
        # DroneKit控制类
        code_lines.extend(self._generate_dronekit_controller())
        
        # 任务函数
        code_lines.extend(self._generate_mission_function(actions, waypoints))
        
        # 主函数
        code_lines.extend(self._generate_main())
        
        # 生成完整代码
        code = "\n".join(code_lines)
        
        # 保存到文件
        import os
        workspace_dir = r"i:\UAV-MCP"
        if not os.path.isabs(output_file):
            output_file = os.path.join(workspace_dir, output_file)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        print(f"[生成] DroneKit版本代码: {output_file}")
        print(f"  - 航点数: {len(waypoints)}")
        print(f"  - 动作数: {len(actions)}")
        
        return code
    
    def _waypoints_to_actions(self, waypoints: List[Tuple[int, int, int]]) -> List[Dict]:
        """将航点转换为动作序列（支持斜向移动）"""
        actions = []
        
        for i in range(len(waypoints) - 1):
            current = waypoints[i]
            next_point = waypoints[i + 1]
            
            dx = next_point[0] - current[0]
            dy = next_point[1] - current[1]
            dz = next_point[2] - current[2]
            
            # 转换为方向动作（支持斜向移动）
            # 注意：栅格坐标系 X=右, Y=前, Z=上
            if dz == 0 and dx != 0 and dy != 0:
                # 斜向移动（4个方向）- 修正坐标系映射
                if dx > 0 and dy > 0:
                    action_type, action_cn = "right_forward", "右前"
                elif dx < 0 and dy > 0:
                    action_type, action_cn = "left_forward", "左前"
                elif dx > 0 and dy < 0:
                    action_type, action_cn = "right_backward", "右后"
                elif dx < 0 and dy < 0:
                    action_type, action_cn = "left_backward", "左后"
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
                "dx": dx,
                "dy": dy,
                "dz": dz,
            })
        
        return actions
    
    def _generate_header(self) -> List[str]:
        """生成文件头"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return [
            '"""',
            '无人机任务执行代码 - DroneKit真实硬件版本',
            f'生成时间: {timestamp}',
            '',
            '【重要说明】',
            '1. 本代码适用于真实无人机（Pixhawk + APM/ArduPilot固件）',
            '2. 支持光流定位（GUIDED_NOGPS模式）',
            '3. 需要安装dronekit-python: pip install dronekit',
            '4. 需要配置MAVProxy或连接字符串',
            '',
            '【连接方式】',
            '- SITL仿真: "udp:127.0.0.1:14550"',
            '- USB串口: "/dev/ttyUSB0" 或 "/dev/ttyACM0" (Linux)',
            '           "COM3" (Windows)',
            '- 无线数传: "udp:192.168.1.100:14550"',
            '',
            '【飞行前检查】',
            '✓ 确认光流传感器已校准',
            '✓ 确认电池电量充足 (>30%)',
            '✓ 确认飞行空间安全、无障碍物',
            '✓ 确认急停开关可用',
            '✓ 测试手动模式可正常控制',
            '',
            '⚠️  警告: 真实飞行存在风险，首次使用请在安全环境下测试！',
            '"""',
            '',
        ]
    
    def _generate_imports(self) -> List[str]:
        """生成导入语句"""
        return [
            'import time',
            'import sys',
            'from typing import Tuple, List',
            '',
            '# DroneKit导入',
            'try:',
            '    from dronekit import connect, VehicleMode, LocationLocal',
            '    from pymavlink import mavutil',
            '    DRONEKIT_AVAILABLE = True',
            'except ImportError:',
            '    print("错误: 未安装dronekit库")',
            '    print("请运行: pip install dronekit pymavlink")',
            '    DRONEKIT_AVAILABLE = False',
            '    sys.exit(1)',
            '',
        ]
    
    def _generate_config(self) -> List[str]:
        """生成配置参数"""
        return [
            '# ==================== 配置参数 ====================',
            '',
            '# 连接配置',
            'CONNECTION_STRING = "127.0.0.1:14551"  # 默认连接端口（真实硬件）',
            '# CONNECTION_STRING = "127.0.0.1:14550"  # SITL仿真端口',
            '# CONNECTION_STRING = "/dev/ttyUSB0"  # Linux串口',
            '# CONNECTION_STRING = "COM3"  # Windows串口',
            '',
            '# 飞行参数 (参考example5.py)',
            f'DEFAULT_ALTITUDE = 3.0  # 默认起飞高度（米）',
            f'DEFAULT_SPEED = 0.2  # 默认速度（米/秒）⚠️ 1格1米需要5秒 (0.2m/s × 5s = 1m)',
            f'HOVER_TIME = {self.hover_time}  # 悬停时间（秒）',
            f'GRID_UNIT = {self.grid_unit}  # 网格单位（米）',
            '',
            '# 距离计算说明',
            '# 1格(1米) = 0.2m/s × 5秒',
            '# 2格(2米) = 0.2m/s × 10秒',
            '# 3格(3米) = 0.2m/s × 15秒',
            '',
            '# 安全参数',
            'MIN_BATTERY = 30.0  # 最低电量（%）',
            'MAX_ALTITUDE = 10.0  # 最大高度（米）',
            'POSITION_TOLERANCE = 0.3  # 位置到达容差（米）',
            '',
        ]
    
    def _generate_dronekit_controller(self) -> List[str]:
        """生成DroneKit控制器类（移除，改为生成动作函数）"""
        # 直接生成模块化动作函数，符合example4.py的函数式设计
        return self._generate_action_functions()

    def _generate_action_functions(self) -> List[str]:
        """生成动作函数（模块化设计，对应栅格空间的每个动作）"""
        return [
            '# ============================================================================',
            '# 航向锁定辅助函数（方案3：显式锁定航向）',
            '# ============================================================================',
            'def condition_yaw(heading, relative=False):',
            '    """',
            '    设置无人机航向（Yaw角度）',
            '    ',
            '    参数:',
            '        heading: 目标航向角度（0-360度）',
            '        relative: 是否相对于当前航向（True=相对，False=绝对）',
            '    """',
            '    if relative:',
            '        is_relative = 1  # yaw relative to direction of travel',
            '    else:',
            '        is_relative = 0  # yaw is an absolute angle',
            '    ',
            '    # create the CONDITION_YAW command using command_long_encode()',
            '    msg = vehicle.message_factory.command_long_encode(',
            '        0, 0,    # target system, target component',
            '        mavutil.mavlink.MAV_CMD_CONDITION_YAW,  # command',
            '        0,       # confirmation',
            '        heading, # param 1, yaw in degrees',
            '        0,       # param 2, yaw speed deg/s (0=max)',
            '        1,       # param 3, direction -1 ccw, 1 cw',
            '        is_relative,  # param 4, relative offset 1, absolute angle 0',
            '        0, 0, 0) # param 5-7 not used',
            '    ',
            '    # send command to vehicle',
            '    vehicle.send_mavlink(msg)',
            '    time.sleep(0.1)  # 短暂延迟确保命令发送',
            '',
            '',
            '# ============================================================================',
            '# 模块化动作函数（对应UAV-MCP栅格空间动作）',
            '# ============================================================================',
            'def send_body_ned_velocity(velocity_x, velocity_y, velocity_z, duration=0):',
            '    """',
            '    发送机体坐标系下的NED速度命令',
            '    ',
            '    参数:',
            '        velocity_x: 前后方向速度 (m/s, 正值向前)',
            '        velocity_y: 左右方向速度 (m/s, 正值向右)',
            '        velocity_z: 垂直方向速度 (m/s, 正值向下)',
            '        duration: 持续时间（秒）',
            '    ',
            '    坐标系说明:',
            '        MAV_FRAME_BODY_NED - 机体坐标系（航空航天标准）',
            '        - X轴: 机头方向为正（前进）',
            '        - Y轴: 机身右侧为正（右移）',
            '        - Z轴: 垂直向下为正（下降）⚠️ 航空标准约定',
            '    """',
            '    msg = vehicle.message_factory.set_position_target_local_ned_encode(',
            '        0,       # time_boot_ms (not used)',
            '        0, 0,    # target system, target component',
            '        mavutil.mavlink.MAV_FRAME_BODY_NED,  # frame Needs to be MAV_FRAME_BODY_NED for forward/back left/right control.',
            '        0b0000111111000111,  # type_mask (参考example5.py成功配置)',
            '        0, 0, 0,  # x, y, z positions (not used)',
            '        velocity_x, velocity_y, velocity_z,  # m/s',
            '        0, 0, 0,  # x, y, z acceleration',
            '        0, 0)     # yaw, yaw_rate',
            '    ',
            '    for x in range(0, duration):',
            '        vehicle.send_mavlink(msg)',
            '        time.sleep(1)',
            '',
            '',
            '# ============================================================================',
            '# UAV-MCP栅格动作函数（1格=1米）',
            '# ============================================================================',
            'def action_forward(grids=1):',
            '    """前进指定格数（沿机头方向，x轴正向）"""',
            '    speed = DEFAULT_SPEED',
            '    duration = int(grids * (GRID_UNIT / speed))',
            '    print(f"[动作] 前进 {grids}格 ({grids*GRID_UNIT}米) - 速度{speed}m/s, 时长{duration}秒")',
            '    # x表示前后方向，y表示左右方向，z表示垂直高度方向',
            '    send_body_ned_velocity(speed, 0, 0, duration)',
            '    time.sleep(2)  # 延迟2秒，这样拐角更方正（参考example5.py）',
            '',
            '',
            'def action_backward(grids=1):',
            '    """后退指定格数（沿机尾方向，x轴负向）"""',
            '    speed = DEFAULT_SPEED',
            '    duration = int(grids * (GRID_UNIT / speed))',
            '    print(f"[动作] 后退 {grids}格 ({grids*GRID_UNIT}米) - 速度{speed}m/s, 时长{duration}秒")',
            '    send_body_ned_velocity(-speed, 0, 0, duration)',
            '    time.sleep(2)  # 延迟2秒',
            '',
            '',
            'def action_right(grids=1):',
            '    """右移指定格数（向机身右侧，y轴正向）"""',
            '    speed = DEFAULT_SPEED',
            '    duration = int(grids * (GRID_UNIT / speed))',
            '    print(f"[动作] 右移 {grids}格 ({grids*GRID_UNIT}米) - 速度{speed}m/s, 时长{duration}秒")',
            '    send_body_ned_velocity(0, speed, 0, duration)',
            '    time.sleep(2)  # 延迟2秒',
            '',
            '',
            'def action_left(grids=1):',
            '    """左移指定格数（向机身左侧，y轴负向）"""',
            '    speed = DEFAULT_SPEED',
            '    duration = int(grids * (GRID_UNIT / speed))',
            '    print(f"[动作] 左移 {grids}格 ({grids*GRID_UNIT}米) - 速度{speed}m/s, 时长{duration}秒")',
            '    send_body_ned_velocity(0, -speed, 0, duration)',
            '    time.sleep(2)  # 延迟2秒',
            '',
            '',
            'def action_up(grids=1):',
            '    """上升指定格数（垂直向上，z轴负向）⚠️ NED坐标系Z轴向下为正"""',
            '    speed = DEFAULT_SPEED',
            '    duration = int(grids * (GRID_UNIT / speed))',
            '    print(f"[动作] 上升 {grids}格 ({grids*GRID_UNIT}米) - 速度{speed}m/s, 时长{duration}秒")',
            '    send_body_ned_velocity(0, 0, -speed, duration)  # 注意：Z轴负值表示上升',
            '    time.sleep(2)  # 延迟2秒',
            '',
            '',
            'def action_down(grids=1):',
            '    """下降指定格数（垂直向下，z轴正向）"""',
            '    speed = DEFAULT_SPEED',
            '    duration = int(grids * (GRID_UNIT / speed))',
            '    print(f"[动作] 下降 {grids}格 ({grids*GRID_UNIT}米) - 速度{speed}m/s, 时长{duration}秒")',
            '    send_body_ned_velocity(0, 0, speed, duration)  # 注意：Z轴正值表示下降',
            '    time.sleep(2)  # 延迟2秒',
            '',
            '',
            'def action_hover(duration=2):',
            '    """悬停指定时间"""',
            '    print(f"[动作] 悬停 {duration}秒")',
            '    send_body_ned_velocity(0, 0, 0, duration)',
            '    time.sleep(1)  # 悬停后短暂延迟',
            '',
            '',
            '# ============================================================================',
            '# 斜向移动动作函数（平面斜向，45度角）',
            '# 注意：斜向移动1格实际距离为√2米（约1.414米）',
            '# ============================================================================',
            'def action_right_forward(grids=1):',
            '    """右前斜移（同时右移+前进）"""',
            '    # 【航向锁定】在斜向移动前锁定当前航向，防止飞控自动旋转机头',
            '    current_heading = vehicle.heading',
            '    condition_yaw(current_heading, relative=False)  # 绝对角度锁定',
            '    ',
            '    speed = DEFAULT_SPEED',
            '    duration = int(grids * (GRID_UNIT / speed))',
            '    send_body_ned_velocity(speed, speed, 0, duration)',
            '    time.sleep(2)  # 延迟2秒',
            '',
            '',
            'def action_left_forward(grids=1):',
            '    """左前斜移（同时左移+前进）"""',
            '    # 【航向锁定】在斜向移动前锁定当前航向，防止飞控自动旋转机头',
            '    current_heading = vehicle.heading',
            '    condition_yaw(current_heading, relative=False)  # 绝对角度锁定',
            '    ',
            '    speed = DEFAULT_SPEED',
            '    duration = int(grids * (GRID_UNIT / speed))',
            '    send_body_ned_velocity(speed, -speed, 0, duration)',
            '    time.sleep(2)  # 延迟2秒',
            '',
            '',
            'def action_right_backward(grids=1):',
            '    """右后斜移（同时右移+后退）"""',
            '    # 【航向锁定】在斜向移动前锁定当前航向，防止飞控自动旋转机头',
            '    current_heading = vehicle.heading',
            '    condition_yaw(current_heading, relative=False)  # 绝对角度锁定',
            '    ',
            '    speed = DEFAULT_SPEED',
            '    duration = int(grids * (GRID_UNIT / speed))',
            '    send_body_ned_velocity(-speed, speed, 0, duration)',
            '    time.sleep(2)  # 延迟2秒',
            '',
            '',
            'def action_left_backward(grids=1):',
            '    """左后斜移（同时左移+后退）"""',
            '    # 【航向锁定】在斜向移动前锁定当前航向，防止飞控自动旋转机头',
            '    current_heading = vehicle.heading',
            '    condition_yaw(current_heading, relative=False)  # 绝对角度锁定',
            '    ',
            '    speed = DEFAULT_SPEED',
            '    duration = int(grids * (GRID_UNIT / speed))',
            '    send_body_ned_velocity(-speed, -speed, 0, duration)',
            '    time.sleep(2)  # 延迟2秒',
            '',
        ]
    
    def _generate_mission_function(self, actions: List[Dict], 
                                   waypoints: List[Tuple[int, int, int]]) -> List[str]:
        """生成任务执行函数（使用模块化动作）"""
        lines = [
            '# ============================================================================',
            '# 解锁并起飞',
            '# ============================================================================',
            'def arm_and_takeoff(aTargetAltitude):',
            '    """',
            '    解锁无人机并起飞到目标高度',
            '    ',
            '    参数:',
            '        aTargetAltitude: 目标高度（米）',
            '    ',
            '    注意: 参考example5.py，注释掉is_armable检查以避免传感器问题导致阻塞',
            '    """',
            '    # print("基本预检查...")',
            '    # 注释掉is_armable检查（参考example5.py实际运行经验）',
            '    # while not vehicle.is_armable:',
            '    #     print(" 等待无人机就绪...")',
            '    #     time.sleep(1)',
            '    # print("无人机已就绪!")',
            '    ',
            '    # 切换到GUIDED模式',
            '    print("切换到GUIDED模式...")',
            '    vehicle.mode = VehicleMode("GUIDED")',
            '    ',
            '    # 等待模式切换完成',
            '    while vehicle.mode.name != "GUIDED":',
            '        print(" 等待模式切换...")',
            '        time.sleep(1)',
            '    ',
            '    print("模式切换完成!")',
            '    ',
            '    # 解锁无人机（电机将开始旋转）',
            '    # print("解锁无人机...")',
            '    vehicle.armed = True',
            '    ',
            '    # 在无人机起飞之前，确认电机已经解锁',
            '    while not vehicle.armed:',
            '        print(" Waiting for arming...")',
            '        time.sleep(1)',
            '    ',
            '    # 发送起飞指令',
            '    print("Taking off!")',
            '    # simple_takeoff将发送指令，使无人机起飞并上升到目标高度',
            '    vehicle.simple_takeoff(aTargetAltitude)',
            '    ',
            '    # 在无人机上升到目标高度之前，阻塞程序',
            '    while True:',
            '        print(" Altitude: ", vehicle.location.global_relative_frame.alt)',
            '        # 当高度上升到目标高度的0.95倍时，即认为达到了目标高度，退出循环',
            '        # vehicle.location.global_relative_frame.alt为相对于home点的高度',
            '        if vehicle.location.global_relative_frame.alt >= aTargetAltitude * 0.95:',
            '            print("Reached target altitude")',
            '            break',
            '        # 等待1s',
            '        time.sleep(1)',
            '',
            '',
            '# ============================================================================',
            '# 执行任务主函数',
            '# ============================================================================',
            'def execute_mission():',
            '    """',
            '    执行无人机任务',
            '    ',
            f'    任务概述:',
            f'        - 总航点数: {len(waypoints)}',
            f'        - 总动作数: {len(actions)}',
            '    """',
            '    print("=" * 70)',
            '    print("       开始执行无人机任务")',
            '    print("=" * 70)',
            '    print()',
            '    ',
            '    # 起飞到默认高度',
            '    arm_and_takeoff(DEFAULT_ALTITUDE)',
            '    ',
            '    # 设置在运动时，默认的空速',
            '    print("Set default/target airspeed to", DEFAULT_SPEED)',
            '    # vehicle.airspeed变量可读可写，且读、写时的含义不同。',
            '    # 读取时，为无人机的当前空速；写入时，设定无人机在执行航点任务时的默认速度',
            '    vehicle.airspeed = DEFAULT_SPEED',
            '    ',
            '    print()',
            '    print("=" * 70)',
            f'    print("       开始执行飞行动作 (共{len(actions)}个动作)")',
            '    print("=" * 70)',
            '    print()',
            '    ',
        ]
        
        # 生成每个动作的调用
        for i, action in enumerate(actions, 1):
            action_type = action["action"]
            action_cn = action.get("action_cn", action_type)
            grids = action.get("grids", 1)
            
            lines.append(f'    # 动作 {i}/{len(actions)}: {action_cn} {grids}格')
            
            # 根据动作类型调用对应的模块化函数
            if action_type == "forward":
                lines.append(f'    action_forward({grids})')
            elif action_type == "backward":
                lines.append(f'    action_backward({grids})')
            elif action_type == "right":
                lines.append(f'    action_right({grids})')
            elif action_type == "left":
                lines.append(f'    action_left({grids})')
            elif action_type == "up":
                lines.append(f'    action_up({grids})')
            elif action_type == "down":
                lines.append(f'    action_down({grids})')
            elif action_type == "hover":
                hover_time = action.get("duration", 2)
                lines.append(f'    action_hover({hover_time})')
            # 斜向移动动作（修正后的命名）
            elif action_type == "right_forward":
                lines.append(f'    action_right_forward({grids})')
            elif action_type == "left_forward":
                lines.append(f'    action_left_forward({grids})')
            elif action_type == "right_backward":
                lines.append(f'    action_right_backward({grids})')
            elif action_type == "left_backward":
                lines.append(f'    action_left_backward({grids})')
            
            lines.append('    ')
        
        lines.extend([
            '    print()',
            '    print("=" * 70)',
            '    print("动作执行完成，开始降落")',
            '    print("=" * 70)',
            '    print()',
            '    ',
            '    # 发送"降落"指令',
            '    print("Land")',
            '    # 降落，只需将无人机的飞行模式切换成"LAND"',
            '    vehicle.mode = VehicleMode("LAND")',
            '    ',
            '    # 等待降落完成（无人机会自动降落）',
            '    # while vehicle.armed:',
            '    #     time.sleep(1)',
            '',
        ])
        
        return lines
    
    def _generate_main(self) -> List[str]:
        """生成主程序(完全参考example4.py的脚本式设计)"""
        return [
            '# ============================================================================',
            '# 连接到飞控',
            '# ============================================================================',
            '# 连接到飞控',
            '# 请根据实际情况修改连接字符串:',
            "# - 串口连接: '/dev/ttyUSB0' (Linux) 或 'COM3' (Windows)",
            "# - 网络连接: 'tcp:127.0.0.1:5760' (SITL仿真)",
            "# - UDP连接: 'udp:127.0.0.1:14550'",
            '',
            'print()',
            'print("=" * 70)',
            'print("       UAV-MCP DroneKit无人机控制程序")',
            'print("=" * 70)',
            'print()',
            'print("⚠️  警告: 这是真实无人机控制代码！")',
            'print("⚠️  请确保:")',
            'print("    1. 飞行环境安全，无障碍物")',
            'print("    2. 电池电量充足 (>30%)")',
            'print("    3. 光流传感器已校准")',
            'print("    4. 急停开关可用")',
            'print()',
            '',
            '# 用户确认',
            'response = input("确认继续执行？(输入 YES 继续): ")',
            '',
            'if response.upper() != "YES":',
            '    print()',
            '    print("[取消] 任务已取消")',
            '    sys.exit(0)',
            '',
            'print()',
            'print("Connecting to vehicle on:", CONNECTION_STRING)',
            '# connect函数将会返回一个Vehicle类型的对象，即此处的vehicle',
            '# 即可认为是无人机的主体，通过vehicle对象，我们可以直接控制无人机',
            'try:',
            '    vehicle = connect(CONNECTION_STRING, wait_ready=True, baud=921600)',
            '    print("连接成功!")',
            'except Exception as e:',
            '    print(f"连接失败: {e}")',
            '    sys.exit(1)',
            '',
            '',
            '# ============================================================================',
            '# 执行任务 (包含起飞、动作序列、自动降落)',
            '# ============================================================================',
            'try:',
            '    execute_mission()',
            '    print()',
            '    print("✓ 任务完成!")',
            '    ',
            'except KeyboardInterrupt:',
            '    print()',
            '    print("[中断] 用户取消任务，紧急降落...")',
            '    try:',
            '        vehicle.mode = VehicleMode("LAND")',
            '        print("等待紧急降落...")',
            '        while vehicle.armed:',
            '            time.sleep(1)',
            '        print("✓ 紧急降落完成")',
            '    except:',
            '        pass',
            '        ',
            'except Exception as e:',
            '    print()',
            '    print(f"[错误] {e}")',
            '    print("程序异常，紧急降落...")',
            '    try:',
            '        vehicle.mode = VehicleMode("LAND")',
            '        print("等待紧急降落...")',
            '        while vehicle.armed:',
            '            time.sleep(1)',
            '        print("✓ 紧急降落完成")',
            '    except:',
            '        pass',
            '',
            '',
            '# ============================================================================',
            '# 清理资源',
            '# ============================================================================',
            '# 退出之前，清除vehicle对象',
            'print("Close vehicle object")',
            'vehicle.close()',
        ]


# ====================测试函数 ====================

def test_generate():
    """测试代码生成"""
    generator = DroneKitCodeGenerator()
    
    # 测试航点
    test_waypoints = [
        (5, 5, 0),   # 起点
        (5, 5, 2),   # 上升2米
        (8, 5, 2),   # 右移3米
        (8, 8, 2),   # 前进3米
        (5, 8, 2),   # 左移3米
        (5, 5, 2),   # 后退3米
        (5, 5, 0),   # 下降2米
    ]
    
    # 生成两个版本
    sim_file, dronekit_file = generator.generate_both_versions(test_waypoints, "test_mission")
    
    print(f"\n✓ 生成完成!")
    print(f"  - 仿真版本: {sim_file}")
    print(f"  - DroneKit版本: {dronekit_file}")


if __name__ == "__main__":
    test_generate()
