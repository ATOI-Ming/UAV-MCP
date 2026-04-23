"""
分层俯视图生成器
将3D栅格空间的每一层转换为2D俯视图图像
用于AI识别障碍物和无人机位置
"""

import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端，用于图像生成
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle, FancyBboxPatch
import numpy as np
from typing import Tuple, List, Dict, Optional
import os

from core.grid_space import GridSpace, CellType


class LayerVisualizer:
    """分层俯视图可视化器
    
    特性：
    - 栅格尺寸：0.8×0.8 (留出0.2间隙)
    - 坐标范围：[0, 10] × [0, 10]
    - 栅格中心：对齐到整数坐标点
    - 圆角设计：使用FancyBboxPatch
    """
    
    def __init__(self, grid_space: GridSpace):
        self.grid_space = grid_space
        self.cell_visual_size = 0.8  # 栅格可视化尺寸
        self.cell_gap = 0.1  # 栅格之间的间隙
    
    def generate_layer_image(self, z: int, save_path: Optional[str] = None, 
                            show_grid: bool = True,
                            show_coordinates: bool = True,
                            show_axes_labels: bool = True) -> Optional[str]:
        """
        生成某一层的俯视图（优化版 - 圆角栅格）
        
        特性：
        - 0.8×0.8栅格尺寸，留出间隙
        - [0,10]坐标范围
        - 栅格中心对齐到整数坐标
        - 圆角设计，更加美观
        
        Args:
            z: 层高度 (用户坐标, 0到10)
            save_path: 保存路径（可选）
            show_grid: 是否显示网格线
            show_coordinates: 是否显示坐标标注
            show_axes_labels: 是否显示坐标轴标签
            
        Returns:
            保存的文件路径（如果保存）
        """
        # 检查层高度是否有效
        if z < 0 or z > 10:
            print(f"[WARNING] 层高度 {z} 超出范围 [0, 10]")
            return None
        
        # 创建图形，更大的尺寸以便显示细节
        fig, ax = plt.subplots(figsize=(14, 14))
        
        # 设置背景色为浅蓝色
        fig.patch.set_facecolor('#E8F4F8')  # 浅蓝色背景
        ax.set_facecolor('#E8F4F8')  # 坐标轴背景也是浅蓝色
        
        # 设置坐标轴范围 [-0.5, 10.5] 留出边距
        ax.set_xlim(-0.5, 10.5)
        ax.set_ylim(-0.5, 10.5)
        ax.set_aspect('equal')
        
        # === 绘制背景网格 ===
        if show_grid:
            # 较淡的网格线
            for i in range(0, 11):
                ax.axhline(y=i, color='lightgray', linewidth=0.5, alpha=0.3, zorder=1)
                ax.axvline(x=i, color='lightgray', linewidth=0.5, alpha=0.3, zorder=1)
        
        # === 绘制栅格方块（圆角设计） ===
        # 遍历 [0, 10] 范围的所有栅格
        for x in range(0, 11):
            for y in range(0, 11):
                user_pos = (x, y, z)
                
                # 转换为内部坐标查询
                internal_pos = self.grid_space._user_to_internal(user_pos)
                
                # 获取单元格信息
                if internal_pos in self.grid_space.cells:
                    cell = self.grid_space.cells[internal_pos]
                    cell_type = cell.cell_type.value
                else:
                    cell_type = 'empty'
                
                # 计算栅格的绘制位置（中心对齐）
                # 栅格中心在 (x, y)，尺寸为 0.8x0.8
                rect_x = x - self.cell_visual_size / 2
                rect_y = y - self.cell_visual_size / 2
                
                # 根据类型绘制不同样式的栅格（圆角设计）
                if cell_type == "empty":
                    # 空白栅格 - 浅白色/浅灰色方块（清晰可见，圆角）
                    rect = FancyBboxPatch((rect_x, rect_y), 
                                         self.cell_visual_size, self.cell_visual_size,
                                         boxstyle="round,pad=0.05",  # 圆角效果（增大弧度）
                                         linewidth=0.8, 
                                         edgecolor='#D0D0D0',  # 浅灰色边框
                                         facecolor='#F5F5F5',  # 浅白色填充
                                         alpha=0.9, 
                                         zorder=3)
                    
                elif cell_type == "uav":
                    # 无人机 - 蓝色填充，深蓝色边框（圆角）
                    rect = FancyBboxPatch((rect_x, rect_y), 
                                         self.cell_visual_size, self.cell_visual_size,
                                         boxstyle="round,pad=0.05",  # 圆角效果（增大弧度）
                                         linewidth=2.5, 
                                         edgecolor='#0066CC', 
                                         facecolor='#3399FF', 
                                         alpha=0.8, 
                                         zorder=5)
                    
                elif cell_type == "obstacle":
                    # 障碍物 - 红色填充，深红色边框（圆角）
                    rect = FancyBboxPatch((rect_x, rect_y), 
                                         self.cell_visual_size, self.cell_visual_size,
                                         boxstyle="round,pad=0.05",  # 圆角效果（增大弧度）
                                         linewidth=2.5, 
                                         edgecolor='#CC0000', 
                                         facecolor='#FF3333', 
                                         alpha=0.8, 
                                         zorder=5)
                
                ax.add_patch(rect)
                
                # === 添加坐标标注 (仅对无人机和障碍物) ===
                if show_coordinates and cell_type in ["uav", "obstacle"]:
                    # 保持原格式，最大化字号和内边距
                    label_text = f"({x},{y},{z})"
                    
                    if cell_type == "uav":
                        text_color = 'black'  # 黑色字体
                        bbox_color = '#B3D9FF'  # 浅蓝色背景
                        bbox_edgecolor = '#0066CC'  # 深蓝色边框
                    else:  # obstacle
                        text_color = 'black'  # 黑色字体
                        bbox_color = '#FFB3B3'  # 浅红色背景
                        bbox_edgecolor = '#CC0000'  # 深红色边框
                    
                    ax.text(x, y, label_text,
                           ha='center', va='center',
                           fontsize=14,  # 增大字号到14pt（最大化）
                           fontweight='bold',
                           color=text_color,
                           bbox=dict(boxstyle='round,pad=0.6',  # 增大内边距到0.6（最大化）
                                   facecolor=bbox_color,
                                   edgecolor=bbox_edgecolor,
                                   linewidth=2.5,  # 加粗边框到2.5
                                   alpha=0.95),
                           zorder=6,
                           fontproperties='SimHei')
        
        # === 设置坐标轴 ===
        if show_axes_labels:
            ax.set_xlabel('X 轴 (右向)', fontsize=13, fontweight='bold', 
                         fontproperties='SimHei', labelpad=10)
            ax.set_ylabel('Y 轴 (前向)', fontsize=13, fontweight='bold', 
                         fontproperties='SimHei', labelpad=10)
        
        # 设置刻度（每1个单位一个刻度，更清晰）
        ax.set_xticks(range(0, 11, 1))
        ax.set_yticks(range(0, 11, 1))
        ax.tick_params(labelsize=11)
        
        # === 生成标题 ===
        if z == 0:
            title_text = '飞行层：第 0 层栅格地图'
        else:
            title_text = f'飞行层：第 {z} 层栅格地图'
        
        ax.set_title(title_text, 
                    fontsize=18,        # 增大字号（16→18
                    fontweight='bold', 
                    fontproperties='SimHei', 
                    pad=20,             # 增大pad给图例留空间
                    loc='center')       # 中央对齐
        
        # === 添加图例（放在栅格地图左上角） ===
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#3399FF', edgecolor='#0066CC', 
                  label='蓝色栅格 无人机', alpha=0.8, linewidth=2),
            Patch(facecolor='#FF3333', edgecolor='#CC0000', 
                  label='红色栅格 障碍物', alpha=0.8, linewidth=2),
            Patch(facecolor='#F5F5F5', edgecolor='#D0D0D0', 
                  label='白色栅格 空白', alpha=0.9, linewidth=0.8)
        ]
        # 将图例放在栅格地图外面左上方（标题左下方）
        ax.legend(handles=legend_elements, 
                 loc='upper left',          # 左上角定位
                 bbox_to_anchor=(0, 1.15),  # 放在地图外部上方（标题下方）
                 ncol=3,                    # 3列横向排列
                 prop={'family': 'SimHei', 'size': 12},  # 增大字号到12pt
                 framealpha=0.95, 
                 edgecolor='gray', 
                 fancybox=True,
                 columnspacing=1.5,         # 增大列间距
                 handlelength=1.5,          # 图例标记长度
                 handletextpad=0.5)         # 标记与文字间距
        
        # === 添加说明文字 ===
        info_text = f'栅格尺寸: {self.cell_visual_size}×{self.cell_visual_size}m | 坐标范围: [0,10]×[0,10]'
        ax.text(0.5, -0.04, info_text,
               transform=ax.transAxes,
               ha='center', va='top',
               fontsize=9, color='gray',
               fontproperties='SimHei')
        
        plt.tight_layout()
        
        # === 保存图像 ===
        if save_path:
            os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
            plt.savefig(save_path, dpi=150, bbox_inches='tight', 
                       facecolor='#E8F4F8')  # 保存时使用浅蓝色背景
            plt.close()
            return save_path
        else:
            plt.close()
            return None
    
    def generate_all_layers(self, output_dir: str = "grid_layers", 
                           filename_pattern: str = "layer_{z}.png") -> List[str]:
        """
        生成所有层的俯视图
        
        Args:
            output_dir: 输出目录
            filename_pattern: 文件名模式（{z}会被替换为层号）
            
        Returns:
            生成的所有文件路径列表
        """
        os.makedirs(output_dir, exist_ok=True)
        
        saved_files = []
        
        # 遍历 -10 到 10
        for z in range(-10, 11):
            filename = filename_pattern.format(z=z)
            filepath = os.path.join(output_dir, filename)
            
            result = self.generate_layer_image(z, filepath)
            if result:
                saved_files.append(result)
        
        return saved_files
    
    def generate_composite_view(self, save_path: str, 
                                layers_to_show: Optional[List[int]] = None,
                                max_cols: int = 4) -> str:
        """
        生成多层组合视图
        
        Args:
            save_path: 保存路径
            layers_to_show: 要显示的层列表（None表示所有层）
            max_cols: 每行最多显示的层数
            
        Returns:
            保存的文件路径
        """
        if layers_to_show is None:
            layers_to_show = list(range(self.grid_space.grid_size[2]))
        
        num_layers = len(layers_to_show)
        num_cols = min(max_cols, num_layers)
        num_rows = (num_layers + num_cols - 1) // num_cols
        
        fig, axes = plt.subplots(num_rows, num_cols, 
                                figsize=(5 * num_cols, 5 * num_rows))
        
        # 确保axes是2D数组
        if num_rows == 1 and num_cols == 1:
            axes = np.array([[axes]])
        elif num_rows == 1:
            axes = axes.reshape(1, -1)
        elif num_cols == 1:
            axes = axes.reshape(-1, 1)
        
        for idx, z in enumerate(layers_to_show):
            row = idx // num_cols
            col = idx % num_cols
            ax = axes[row, col]
            
            layer_data = self.grid_space.get_layer_data(z)
            x_size, y_size = layer_data["size"]
            
            ax.set_xlim(0, x_size)
            ax.set_ylim(0, y_size)
            ax.set_aspect('equal')
            
            # 绘制栅格
            for cell_info in layer_data["cells"]:
                x, y, _ = cell_info["position"]
                cell_type = cell_info["type"]
                
                if cell_type == "empty":
                    rect = Rectangle((x, y), 1, 1,
                                    linewidth=0.3, edgecolor='lightgray',
                                    facecolor='white', alpha=0.2)
                elif cell_type == "uav":
                    rect = Rectangle((x, y), 1, 1,
                                    linewidth=1.5, edgecolor='darkblue',
                                    facecolor='blue', alpha=0.7)
                elif cell_type == "obstacle":
                    rect = Rectangle((x, y), 1, 1,
                                    linewidth=1.5, edgecolor='darkred',
                                    facecolor='red', alpha=0.7)
                
                ax.add_patch(rect)
            
            ax.grid(True, alpha=0.2)
            ax.set_title(f'层 {z}', fontsize=10, fontproperties='SimHei')
            ax.set_xlabel('X', fontsize=8)
            ax.set_ylabel('Y', fontsize=8)
        
        # 隐藏多余的子图
        for idx in range(num_layers, num_rows * num_cols):
            row = idx // num_cols
            col = idx % num_cols
            axes[row, col].axis('off')
        
        plt.suptitle('栅格空间多层俯视图', fontsize=16, 
                    fontweight='bold', fontproperties='SimHei')
        plt.tight_layout()
        
        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return save_path


# 测试代码
if __name__ == "__main__":
    from grid_space import GridSpace
    
    # 创建栅格空间
    grid = GridSpace((20, 20, 20))
    
    # 设置无人机位置
    grid.set_uav_position((1, 1, 1))
    
    # 添加障碍物（第1层）
    obstacles_layer1 = [
        (5, 5, 1), (6, 5, 1), (7, 5, 1),
        (5, 6, 1), (7, 6, 1),
        (5, 7, 1), (6, 7, 1), (7, 7, 1)
    ]
    grid.add_obstacles(obstacles_layer1)
    
    # 添加障碍物（第2层）
    obstacles_layer2 = [
        (10, 10, 2), (11, 10, 2), (12, 10, 2),
        (10, 11, 2), (12, 11, 2),
        (10, 12, 2), (11, 12, 2), (12, 12, 2)
    ]
    grid.add_obstacles(obstacles_layer2)
    
    # 创建可视化器
    visualizer = LayerVisualizer(grid)
    
    # 生成单层图像
    print("生成第1层俯视图...")
    visualizer.generate_layer_image(1, "test_layer_1.png")
    print("✅ 已保存: test_layer_1.png")
    
    print("\n生成第2层俯视图...")
    visualizer.generate_layer_image(2, "test_layer_2.png")
    print("✅ 已保存: test_layer_2.png")
    
    # 生成所有层
    print("\n生成所有层俯视图...")
    saved_files = visualizer.generate_all_layers("grid_layers")
    print(f"✅ 已生成 {len(saved_files)} 个图像文件")
    
    # 生成组合视图
    print("\n生成多层组合视图...")
    visualizer.generate_composite_view("grid_layers/composite_view.png", 
                                      layers_to_show=[0, 1, 2, 3])
    print("✅ 已保存: grid_layers/composite_view.png")
