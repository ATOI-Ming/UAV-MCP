# UAV-MCP 无人机路径规划与智能重规划系统 - 完整流程图

## 系统架构总览

```mermaid
graph TB
    subgraph 用户交互层
        A[用户输入]
        A1[自然语言描述]
        A2[航线规划图片]
        A3[真实环境照片]
    end
    
    subgraph MCP服务器层
        B[MCP Server]
        B1[16个工具函数]
        B2[3个资源接口]
    end
    
    subgraph AI智能层
        C1[AI轨迹转换器]
        C2[AI智能重规划器]
        C3[AI视觉识别器]
        C4[AI图像航线规划器]
    end
    
    subgraph 核心处理层
        D1[命令解析器]
        D2[航线规划器]
        D3[栅格空间管理]
        D4[代码生成器]
    end
    
    subgraph 可视化层
        E1[3D航线可视化]
        E2[栅格环境可视化]
        E3[图层地图生成]
    end
    
    subgraph 硬件控制层
        F1[DroneKit代码生成]
        F2[仿真代码生成]
    end
    
    A --> B
    B --> C1 & C2 & C3 & C4
    C1 & C2 & C3 & C4 --> D1
    D1 --> D2
    D2 --> D3
    D3 --> E1 & E2 & E3
    D2 --> D4
    D4 --> F1 & F2
```

## 完整工作流程图

```mermaid
graph TD
    Start([用户开始]) --> InputChoice{输入类型选择}
    
    InputChoice -->|文字描述| A1[ai_translate_flight]
    InputChoice -->|航线图片| A2[ai_flight_image_planner]
    InputChoice -->|环境照片| A3[upload_map_image]
    InputChoice -->|直接命令| A4[parse_command]
    
    A1 --> |AI转换| Action[标准动作序列]
    A2 --> |详细分析| ImageAnalysis[两阶段图片分析]
    ImageAnalysis --> |航点识别| Action
    A3 --> |AI识别| EnvMap[环境障碍物地图]
    A4 --> Action
    
    Action --> Parse[parse_command解析命令]
    Parse --> WaypointGen[生成航点列表]
    
    WaypointGen --> CollisionCheck{碰撞检测}
    CollisionCheck -->|无碰撞| PathOK[航线验证通过]
    CollisionCheck -->|有碰撞| Replan[ai_replan_with_obstacles]
    
    Replan --> |AI重规划| NewPath[新航线方案]
    NewPath --> Parse
    
    PathOK --> VisChoice{可视化选择}
    VisChoice -->|查看航线| V1[visualize_flight]
    VisChoice -->|查看环境| V2[visualize_grid_environment]
    VisChoice -->|生成地图| V3[generate_layer_maps]
    
    V1 --> V1Result[3D航线动画/静态图]
    V2 --> V2Result[3D栅格环境]
    V3 --> V3Result[2D图层地图PNG]
    
    V1Result & V2Result & V3Result --> CodeChoice{代码生成选择}
    
    CodeChoice -->|需要代码| CodeGen[generate_uav_code]
    CodeChoice -->|不需要| InfoQuery{信息查询}
    
    CodeGen --> CodeType{代码类型}
    CodeType -->|仿真版| SimCode[仿真Python代码]
    CodeType -->|硬件版| DroneKitCode[DroneKit硬件代码]
    
    InfoQuery -->|查询状态| GetInfo[get_flight_info]
    InfoQuery -->|查询障碍物| GetObs[get_obstacles]
    InfoQuery -->|重置位置| Reset[reset_position]
    InfoQuery -->|清除障碍| Clear[clear_obstacles]
    
    SimCode & DroneKitCode --> Execute[执行飞行任务]
    GetInfo & GetObs & Reset & Clear --> End([任务完成])
    Execute --> End
```

## 核心模块交互流程

```mermaid
graph LR
    subgraph 输入处理模块
        I1[ai_translate_flight<br/>文字→动作]
        I2[ai_flight_image_planner<br/>图片→动作]
        I3[upload_map_image<br/>照片→障碍物]
    end
    
    subgraph 命令处理模块
        P1[parse_command<br/>命令解析]
        P2[CommandParser<br/>动作分解]
    end
    
    subgraph 航线规划模块
        F1[FlightPlanner<br/>航点生成]
        F2[plan_flight<br/>路径规划]
        F3[ai_replan_with_obstacles<br/>智能重规划]
    end
    
    subgraph 空间管理模块
        G1[GridSpace<br/>栅格空间]
        G2[add_obstacles<br/>添加障碍]
        G3[clear_obstacles<br/>清除障碍]
    end
    
    subgraph 可视化模块
        V1[visualize_flight<br/>航线可视化]
        V2[visualize_grid_environment<br/>环境可视化]
        V3[generate_layer_maps<br/>地图生成]
    end
    
    subgraph 代码生成模块
        C1[generate_uav_code<br/>代码生成]
        C2[UAVCodeGenerator<br/>仿真代码]
        C3[DroneKitCodeGenerator<br/>硬件代码]
    end
    
    I1 & I2 --> P1
    I3 --> G2
    P1 --> P2
    P2 --> F1
    F1 --> F2
    F2 --> G1
    G1 --> F3
    F3 --> F1
    F1 --> V1 & V2
    G1 --> V3
    F1 --> C1
    C1 --> C2 & C3
```

## AI图像航线规划详细流程

```mermaid
graph TD
    Start([用户上传航线图片]) --> Tool[ai_flight_image_planner]
    
    Tool --> Guide[生成AI识别指南]
    Guide --> Stage1[第一阶段：详细图片分析]
    
    Stage1 --> S1[1️⃣ 航点识别分析]
    S1 --> S1Detail[总数/位置/类型/编号<br/>起点终点特征]
    
    S1Detail --> S2[2️⃣ 航线形状分析]
    S2 --> S2Detail[轨迹形状/关键特征<br/>尺寸/对称性/转折点]
    
    S2Detail --> S3[3️⃣ 航线顺序分析]
    S3 --> S3Detail[完整路径顺序<br/>方向距离/转折角度]
    
    S3Detail --> S4[4️⃣ 高度层级分析]
    S4 --> S4Detail[工作高度/升降点<br/>高度变化情况]
    
    S4Detail --> S5[5️⃣ 坐标计算过程]
    S5 --> S5Detail[栅格坐标映射<br/>图片→空间转换]
    
    S5Detail --> S6[6️⃣ 动作序列推导]
    S6 --> S6Detail[位移向量计算<br/>动作分解方法]
    
    S6Detail --> Stage2[第二阶段：标准输出]
    Stage2 --> Output[动作序列字符串]
    
    Output --> Parse[parse_command解析]
    Parse --> Waypoints[生成航点列表]
    Waypoints --> Verify{边界验证}
    
    Verify -->|通过| Visual[visualize_flight可视化]
    Verify -->|失败| Error[错误提示：超出边界]
    
    Visual --> Code[generate_uav_code生成代码]
    Code --> End([完成])
```

## AI智能重规划流程

```mermaid
graph TD
    Start([检测到碰撞]) --> Input[ai_replan_with_obstacles]
    
    Input --> GetEnv[获取环境信息]
    GetEnv --> E1[当前航点列表]
    GetEnv --> E2[障碍物坐标]
    GetEnv --> E3[起点终点]
    
    E1 & E2 & E3 --> GenGuide[生成重规划指南]
    
    GenGuide --> AIAnalysis[AI分析任务]
    AIAnalysis --> A1[分析碰撞位置]
    AIAnalysis --> A2[评估绕行方案]
    AIAnalysis --> A3[优化路径长度]
    
    A1 & A2 & A3 --> Strategy[生成避障策略]
    
    Strategy --> NewActions[新动作序列]
    NewActions --> Parse[parse_command解析]
    
    Parse --> NewWaypoints[新航点列表]
    NewWaypoints --> Check{碰撞检测}
    
    Check -->|仍有碰撞| Retry{重试次数}
    Retry -->|<3次| AIAnalysis
    Retry -->|≥3次| Fail[重规划失败]
    
    Check -->|无碰撞| Success[重规划成功]
    Success --> Visual[visualize_flight可视化]
    Visual --> End([完成])
```

## 环境感知与建模流程

```mermaid
graph TD
    Start([真实环境照片]) --> Upload[upload_map_image]
    
    Upload --> ImgCheck{图片验证}
    ImgCheck -->|不存在| Error1[错误：文件不存在]
    ImgCheck -->|存在| Vision[AI视觉识别]
    
    Vision --> Guide[生成识别指南]
    Guide --> AITask[AI识别任务]
    
    AITask --> R1[识别障碍物位置]
    AITask --> R2[估算尺寸大小]
    AITask --> R3[提取栅格坐标]
    
    R1 & R2 & R3 --> ObsList[障碍物坐标列表]
    
    ObsList --> AddObs[add_obstacles添加]
    AddObs --> GridSpace[更新栅格空间]
    
    GridSpace --> VisEnv[visualize_grid_environment]
    VisEnv --> EnvView[3D环境可视化]
    
    EnvView --> LayerMap[generate_layer_maps]
    LayerMap --> MapFiles[生成PNG地图文件]
    
    MapFiles --> Analysis[analyze_grid_space_vision]
    Analysis --> AIAnalysis[AI分析空间特征]
    AIAnalysis --> Suggestions[提供飞行建议]
    
    Suggestions --> End([环境建模完成])
```

## 可视化与代码生成流程

```mermaid
graph TD
    Start([航点列表ready]) --> VisChoice{可视化类型}
    
    VisChoice -->|航线| VF[visualize_flight]
    VisChoice -->|环境| VE[visualize_grid_environment]
    VisChoice -->|地图| GM[generate_layer_maps]
    
    VF --> VFOpt{动画选项}
    VFOpt -->|animate=true| Anim[3D动画播放]
    VFOpt -->|animate=false| Static[3D静态图]
    
    Anim & Static --> SaveImg{保存图片}
    SaveImg -->|save_image指定| SavePNG[保存PNG文件]
    SaveImg -->|未指定| NoSave[仅显示窗口]
    
    VE --> VEResult[3D栅格环境显示]
    VEResult --> ShowObs[显示障碍物位置]
    ShowObs --> ShowPath[显示航线路径]
    
    GM --> GenLayers[生成多层地图]
    GenLayers --> L1[障碍物层]
    GenLayers --> L2[航线层]
    GenLayers --> L3[综合层]
    
    L1 & L2 & L3 --> MapPNG[保存PNG地图]
    
    SavePNG & NoSave & ShowPath & MapPNG --> CodeGen{需要代码?}
    
    CodeGen -->|是| GUC[generate_uav_code]
    CodeGen -->|否| End1([完成])
    
    GUC --> CheckWP{有航点?}
    CheckWP -->|无| Error[错误：无航点]
    CheckWP -->|有| GenOpt{生成选项}
    
    GenOpt --> Sim[仿真版_sim.py]
    GenOpt -->|dronekit=true| DroneKit[硬件版_dronekit.py]
    
    Sim --> SimCode[UAVController类<br/>3D可视化<br/>仿真飞行]
    DroneKit --> DKCode[DroneKit连接<br/>MAVLink命令<br/>光流定位]
    
    SimCode & DKCode --> End2([代码生成完成])
```

## 完整数据流图

```mermaid
graph LR
    subgraph 输入数据
        D1[自然语言<br/>轨迹描述]
        D2[航线规划<br/>图片]
        D3[环境照片<br/>真实场景]
        D4[动作命令<br/>字符串]
    end
    
    subgraph 中间数据
        M1[动作序列<br/>如: 上升1米,右移2米]
        M2[航点列表<br/>x,y,z坐标数组]
        M3[障碍物列表<br/>坐标+尺寸]
        M4[栅格占用<br/>3D布尔数组]
    end
    
    subgraph 输出数据
        O1[3D可视化<br/>PNG图片]
        O2[2D地图<br/>PNG图片]
        O3[Python代码<br/>_sim.py]
        O4[DroneKit代码<br/>_dronekit.py]
        O5[航线信息<br/>JSON数据]
    end
    
    D1 --> |AI转换| M1
    D2 --> |AI识别| M1
    D3 --> |AI识别| M3
    D4 --> M1
    
    M1 --> |解析| M2
    M3 --> M4
    M2 --> |碰撞检测| M4
    M4 --> |验证| M2
    
    M2 --> O1 & O3 & O4 & O5
    M4 --> O1 & O2
    M2 & M4 --> O2
```

## 16个工具函数关系图

```mermaid
graph TD
    subgraph 输入工具
        T1[ai_translate_flight<br/>文字转动作]
        T2[ai_flight_image_planner<br/>图片转动作]
        T3[upload_map_image<br/>照片转障碍物]
    end
    
    subgraph 核心工具
        T4[parse_command<br/>命令解析]
        T5[plan_flight<br/>路径规划]
        T6[ai_replan_with_obstacles<br/>智能重规划]
    end
    
    subgraph 空间管理
        T7[add_obstacles<br/>添加障碍物]
        T8[clear_obstacles<br/>清除障碍物]
        T9[get_obstacles<br/>查询障碍物]
    end
    
    subgraph 可视化工具
        T10[visualize_flight<br/>航线可视化]
        T11[visualize_grid_environment<br/>环境可视化]
        T12[generate_layer_maps<br/>地图生成]
        T13[analyze_grid_space_vision<br/>AI空间分析]
    end
    
    subgraph 辅助工具
        T14[generate_uav_code<br/>代码生成]
        T15[reset_position<br/>重置位置]
        T16[get_flight_info<br/>查询信息]
    end
    
    T1 & T2 --> T4
    T3 --> T7
    T4 --> T5
    T5 --> T6
    T7 --> T11
    T8 --> T11
    T5 --> T10 & T11
    T11 --> T12
    T12 --> T13
    T5 --> T14
    
    style T1 fill:#e1f5ff
    style T2 fill:#e1f5ff
    style T3 fill:#e1f5ff
    style T4 fill:#fff4e1
    style T5 fill:#fff4e1
    style T6 fill:#ffe1e1
    style T10 fill:#e8f5e9
    style T11 fill:#e8f5e9
    style T12 fill:#e8f5e9
```

## 核心类关系图

```mermaid
classDiagram
    class MCPServer {
        +app: Server
        +list_tools()
        +call_tool()
        +list_resources()
        +read_resource()
    }
    
    class AITranslatorMCP {
        +translate_to_actions()
        +create_conversion_guide()
    }
    
    class AIReplannerMCP {
        +replan_with_obstacles()
        +create_replanning_guide()
    }
    
    class AIImageFlightPlanner {
        +process_flight_image()
        +_generate_flight_recognition_guide()
    }
    
    class AIVisionRecognizer {
        +recognize_grid_map()
        +_generate_recognition_guide()
    }
    
    class CommandParser {
        +parse()
        +_parse_action()
    }
    
    class FlightPlanner {
        +add_waypoint()
        +check_collision()
        +get_waypoints()
        +set_start_position()
    }
    
    class GridSpace {
        +add_obstacle()
        +remove_obstacle()
        +is_occupied()
        +get_obstacle_positions()
    }
    
    class UAVCodeGenerator {
        +generate_simulation_code()
        +generate_dronekit_code()
    }
    
    class GridVisualizer {
        +visualize()
        +animate()
        +save_image()
    }
    
    MCPServer --> AITranslatorMCP
    MCPServer --> AIReplannerMCP
    MCPServer --> AIImageFlightPlanner
    MCPServer --> AIVisionRecognizer
    MCPServer --> CommandParser
    MCPServer --> FlightPlanner
    MCPServer --> GridSpace
    MCPServer --> UAVCodeGenerator
    MCPServer --> GridVisualizer
    
    CommandParser --> FlightPlanner
    FlightPlanner --> GridSpace
    UAVCodeGenerator --> FlightPlanner
    GridVisualizer --> FlightPlanner
    GridVisualizer --> GridSpace
```

## 完整使用场景流程

```mermaid
graph TD
    Start([用户开始使用]) --> Scenario{使用场景}
    
    Scenario -->|场景1| S1[文字描述飞行]
    Scenario -->|场景2| S2[图片导入航线]
    Scenario -->|场景3| S3[环境建模]
    Scenario -->|场景4| S4[避障重规划]
    
    S1 --> S1_1[输入: 飞一个正方形]
    S1_1 --> S1_2[ai_translate_flight]
    S1_2 --> S1_3[parse_command]
    S1_3 --> S1_4[visualize_flight]
    S1_4 --> S1_5[generate_uav_code]
    S1_5 --> End1([完成])
    
    S2 --> S2_1[上传: plan.png]
    S2_1 --> S2_2[ai_flight_image_planner]
    S2_2 --> S2_3[详细分析6维度]
    S2_3 --> S2_4[输出动作序列]
    S2_4 --> S2_5[parse_command]
    S2_5 --> S2_6[visualize_flight]
    S2_6 --> End2([完成])
    
    S3 --> S3_1[上传: 真实环境照片]
    S3_1 --> S3_2[upload_map_image]
    S3_2 --> S3_3[AI识别障碍物]
    S3_3 --> S3_4[add_obstacles]
    S3_4 --> S3_5[visualize_grid_environment]
    S3_5 --> S3_6[generate_layer_maps]
    S3_6 --> End3([完成])
    
    S4 --> S4_1[检测到碰撞]
    S4_1 --> S4_2[ai_replan_with_obstacles]
    S4_2 --> S4_3[AI重规划路径]
    S4_3 --> S4_4[parse_command新路径]
    S4_4 --> S4_5[visualize_flight对比]
    S4_5 --> S4_6[generate_uav_code]
    S4_6 --> End4([完成])
```

---

## 流程图说明

### 系统特点
1. **模块化设计**: 16个工具函数各司其职，相互协作
2. **AI驱动**: 4个AI模块提供智能转换、识别、重规划能力
3. **两阶段分析**: 图像航线规划采用详细分析+标准输出模式
4. **完整闭环**: 从输入到可视化到代码生成，形成完整工作流
5. **安全保障**: 碰撞检测、边界验证、智能重规划确保安全

### 核心流程
1. **输入阶段**: 支持文字、图片、照片三种输入方式
2. **处理阶段**: AI转换→命令解析→航点生成→碰撞检测
3. **优化阶段**: 智能重规划→路径优化→安全验证
4. **输出阶段**: 3D可视化→地图生成→代码生成→硬件执行

### 数据流向
输入数据 → AI处理 → 中间数据 → 核心处理 → 输出数据 → 硬件执行
