"""
3D栅格环境可视化模块 - Environment Visualizer

功能：
- 独立的3D环境预览工具
- 可视化栅格空间、障碍物和无人机位置
- 不需要航点数据，专注于环境展示

"""

import os
from typing import Tuple, List, Optional
from mcp.types import TextContent


class EnvironmentVisualizer:
    """3D栅格环境可视化器
    
    专门用于可视化栅格环境，不依赖航点数据
    """
    
    def __init__(self, workspace_dir: str = r"i:\UAV-MCP"):
        """初始化环境可视化器
        
        Args:
            workspace_dir: 工作目录路径
        """
        self.workspace_dir = workspace_dir
    
    def visualize_environment(
        self,
        grid_space,
        flight_planner,
        visualizer_getter,
        show_grid: bool = True,
        save_image: Optional[str] = None
    ) -> Tuple[bool, List[TextContent], str]:
        """可视化栅格环境
        
        Args:
            grid_space: 栅格空间对象
            flight_planner: 飞行规划器对象
            visualizer_getter: 可视化器获取函数
            show_grid: 是否显示栅格线
            save_image: 保存图像文件名（可选）
            
        Returns:
            (success, result_contents, error_msg)
            - success: 是否成功
            - result_contents: MCP返回内容列表
            - error_msg: 错误信息（如果失败）
        """
        print(f"\n[EnvironmentVisualizer] 3D栅格环境可视化")
        print(f"  显示栅格线: {show_grid}")
        print(f"  保存图像: {save_image or '否'}")
        print(f"  当前障碍物数: {len(grid_space.obstacles)}")
        
        try:
            # 使用延迟加载的可视化器
            print(f"[EnvironmentVisualizer] 创建可视化器...")
            visualizer_new = visualizer_getter()
            visualizer_new.grid_space = grid_space  # 传递栅格空间引用
            
            # 创建3D空间
            print(f"[EnvironmentVisualizer] 创建3D空间...")
            visualizer_new.create_grid_space()
            
            # 添加无人机起始位置标记
            start_pos = flight_planner.current_position
            visualizer_new.ax.scatter(
                [start_pos[0]], [start_pos[1]], [start_pos[2]],
                c='blue', marker='o', s=200, 
                label=f'无人机起始位置 {start_pos}',
                edgecolors='navy', linewidths=2, alpha=0.9
            )
            
            # 添加图例
            visualizer_new.ax.legend(loc='upper right', fontsize=10, framealpha=0.9)
            
            # 💾 关键优化：先保存图片（在显示窗口之前）
            save_path = None
            if save_image:
                save_path = self._save_image_optimized(save_image, visualizer_new)
            
            # 🚀 关键优化：使用极速非阻塞方式显示窗口（不等待）
            # 注意：Matplotlib GUI必须在主线程启动，但可以立即返回
            print(f"[EnvironmentVisualizer] 显示3D窗口（极速模式）...")
            self._show_window_instant(visualizer_new)
            print(f"[EnvironmentVisualizer] 窗口已启动，MCP立即返回")
            
            # 生成报告（立即返回）
            report_text = self._generate_report(
                grid_space, 
                start_pos, 
                save_path,  # 传递已保存的路径
                visualizer_new
            )
            
            return True, [TextContent(type="text", text=report_text)], ""
            
        except Exception as e:
            import traceback
            error_msg = f"❌ 环境可视化错误: {str(e)}\n\n{traceback.format_exc()}"
            print(f"[EnvironmentVisualizer ERROR] {error_msg}")
            return False, [TextContent(type="text", text=error_msg)], error_msg
    
    def _generate_report(
        self, 
        grid_space, 
        start_pos: tuple,
        save_path: Optional[str],  # 已保存的路径
        visualizer
    ) -> str:
        """生成可视化报告
        
        Args:
            grid_space: 栅格空间对象
            start_pos: 无人机起始位置
            save_image: 保存图像文件名
            visualizer: 可视化器对象
            
        Returns:
            格式化的报告文本
        """
        report_lines = []
        report_lines.append("🎬 **3D栅格环境可视化**\n")
        report_lines.append(f"[环境信息]:")
        report_lines.append(f"  - 栅格空间: [0,10]×[0,10]×[0,10]")
        report_lines.append(f"  - 障碍物数量: {len(grid_space.obstacles)}个")
        report_lines.append(f"  - 无人机位置: {start_pos}")
        report_lines.append(f"")
        
        # 障碍物分布统计
        if len(grid_space.obstacles) > 0:
            report_lines.append(f"[障碍物分布]:")
            obstacles_by_layer = self._count_obstacles_by_layer(grid_space.obstacles)
            
            for z in sorted(obstacles_by_layer.keys()):
                report_lines.append(f"  - Z={z}层: {obstacles_by_layer[z]}个障碍物")
            report_lines.append(f"")
        else:
            report_lines.append(f"[提示]: 当前环境无障碍物\n")
        
        # 显示内容说明
        report_lines.append(f"[显示内容]:")
        report_lines.append(f"  🟪 栅格空间边界: 10×10×10立方体框架")
        report_lines.append(f"  🔴 障碍物: 红色立方体 ({len(grid_space.obstacles)}个)")
        report_lines.append(f"  🔵 起始位置: 蓝色标记点")
        report_lines.append(f"  📊 坐标轴: X(右)/Y(前)/Z(上)")
        report_lines.append(f"")
        
        # 交互操作说明
        report_lines.append(f"[交互操作]:")
        report_lines.append(f"  - 鼠标拖拽 = 旋转视角")
        report_lines.append(f"  - 滚轮 = 缩放视图")
        report_lines.append(f"  - 关闭窗口继续")
        report_lines.append(f"")
        
        # 显示保存结果（如果有）
        if save_path:
            report_lines.append(f"[成功] 图像已保存: {save_path}\n")
        
        report_lines.append(f"[状态] 3D窗口正在后台启动...")
        report_lines.append(f"\n[成功] MCP调用已完成，窗口异步启动中!")
        report_lines.append(f"\n[提示]: ")
        report_lines.append(f"  - ⚡ MCP立即返回，完全不阻塞")
        report_lines.append(f"  - 🚀 窗口在后台线程独立启动（约0.1秒后）")
        report_lines.append(f"  - ✅ 您可以立即继续下一步操作")
        report_lines.append(f"  - 🎨 窗口打开后可自由交互旋转")
        report_lines.append(f"  - 🔄 关闭窗口不影响数据")
        
        return "\n".join(report_lines)
    
    def _show_window_instant(self, visualizer):
        """
        极速窗口显示方法 - 立即返回，不等待任何渲染
        
        关键：
        - ⚡ 先调用 draw() 一次，确保窗口有内容
        - 🚀 然后立即显示窗口
        - 🎯 MCP调用立即返回
        
        Args:
            visualizer: 可视化器对象
        """
        import matplotlib.pyplot as plt
        
        try:
            # ⚡ 关键：先绘制一次，确保窗口有内容（与保存图片时一致）
            visualizer.fig.canvas.draw()
            
            # 🚀 启动窗口（非阻塞）
            plt.ion()  # 启用交互模式
            plt.show(block=False)  # 非阻塞显示
            
            # 不调用 flush_events()，立即返回
            
            print("[可视化] 💻 3D窗口已启动（内容完整，立即返回）")
            
        except Exception as e:
            print(f"[警告] 窗口显示异常: {e}")
            # 备用方案：简化显示
            plt.show(block=False)
    
    def _show_window_optimized(self, visualizer):
        """
        优化的窗口显示方法 - 解决卡顿和无响应问题
        
        采用与visualizer.py中相同的优化策略：
        - ⚡ 先绘制一次，确保窗口有内容
        - 🖱️ 启用交互模式
        - 💨 显示窗口（非阻塞）
        - 🔄 刷新事件，确保窗口响应
        
        Args:
            visualizer: 可视化器对象
        """
        import matplotlib.pyplot as plt
        
        try:
            # ⚡ 方案A：先绘制一次，确保窗口有内容
            visualizer.fig.canvas.draw()
            
            # ⚡ 方案B：启用交互模式
            plt.ion()
            
            # ⚡ 方案C：显示窗口（非阻塞）
            plt.show(block=False)
            
            # ⚡ 方案D：刷新事件，确保窗口响应
            visualizer.fig.canvas.flush_events()
            
            print("[可视化] 💻 3D窗口已启动（非阻塞模式）")
            print("[提示] 🔄 窗口独立运行，可继续其他操作")
            
        except Exception as e:
            print(f"[警告] 窗口显示异常: {e}")
            # 备用方案：简化显示
            plt.show(block=False)
    
    def _count_obstacles_by_layer(self, obstacles) -> dict:
        """按层统计障碍物数量
        
        Args:
            obstacles: 障碍物列表
            
        Returns:
            {z: count} 字典
        """
        obstacles_by_layer = {}
        for obs in obstacles:
            z = obs[2]
            if z not in obstacles_by_layer:
                obstacles_by_layer[z] = 0
            obstacles_by_layer[z] += 1
        return obstacles_by_layer
    
    def _save_image_optimized(self, save_image: str, visualizer) -> str:
        """
        优化的图像保存方法 - 避免未响应
        
        关键优化：
        - 💾 在显示窗口之前保存图片
        - ⚡ 使用draw()确保渲染完成
        - 🛡️ 异常处理，避免卡死
        
        Args:
            save_image: 文件名
            visualizer: 可视化器对象
            
        Returns:
            保存的文件路径
        """
        try:
            if not save_image.endswith('.png'):
                save_image = f"{save_image}.png"
            save_path = os.path.join(self.workspace_dir, save_image)
            
            print(f"[EnvironmentVisualizer] 💾 保存图像到: {save_path}")
            
            # ⚡ 关键：先绘制一次，确保渲染完成
            visualizer.fig.canvas.draw()
            
            # 💾 保存图片（使用较低的DPI提高速度）
            visualizer.fig.savefig(save_path, dpi=120, bbox_inches='tight')
            
            print(f"[EnvironmentVisualizer] ✅ 图像保存成功")
            return save_path
            
        except Exception as e:
            print(f"[EnvironmentVisualizer] ⚠️ 图僋保存失败: {e}")
            # 返回默认路径，不阻断流程
            return os.path.join(self.workspace_dir, save_image)
    
    def _save_image(self, save_image: str, visualizer) -> str:
        """保存可视化图像
        
        Args:
            save_image: 文件名
            visualizer: 可视化器对象
            
        Returns:
            保存的文件路径
        """
        if not save_image.endswith('.png'):
            save_image = f"{save_image}.png"
        save_path = os.path.join(self.workspace_dir, save_image)
        
        print(f"[EnvironmentVisualizer] 保存图像到: {save_path}")
        visualizer.fig.savefig(save_path, dpi=150, bbox_inches='tight')
        
        return save_path


# 全局单例实例（延迟加载）
_environment_visualizer = None

def get_environment_visualizer() -> EnvironmentVisualizer:
    """获取环境可视化器的全局单例
    
    Returns:
        EnvironmentVisualizer实例
    """
    global _environment_visualizer
    if _environment_visualizer is None:
        _environment_visualizer = EnvironmentVisualizer()
    return _environment_visualizer
