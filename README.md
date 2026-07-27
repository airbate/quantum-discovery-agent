# Q-Discovery Agent

> 面向下一代 AI for Science 的量子原生科研决策引擎：让智能体帮助科学家更快地提出假设、搜索实验空间、组织验证证据。

Q-Discovery Agent 不只是一个“会调用量子线路的聊天机器人”，而是一个连接**自然语言科研目标、科学数据、代理模型、量子组合优化与实验验证**的科研智能体原型。它把实验室中高成本、强约束、需要持续迭代的“下一步做什么”转化为可计算、可解释、可审计的决策流程。

面向 2026 书生国智科探挑战赛暨飞翔杯 AI Agent/Skills 开发大赛·量子计算赛道，系统将科研人员的自然语言目标转换为多目标组合优化问题：先审计数据、估计候选条件的收益与不确定性，再编译 QUBO，使用 Warm Start XY-QAOA 和经典基线生成下一批实验，最后由独立验证器决定结果能否进入科研工作流。

**参赛定位：量子应用与跨界探索** · **产品概念：Quantum Scientific Discovery Copilot** · **当前落点：有限预算下的科研实验批次设计** · **量子核心：可行子空间 QAOA + QUBO**

## 一句话路演

**Q-Discovery Agent 正在构建一个“科研实验导航系统”：它不替科学家做结论，而是把有限预算下的假设空间搜索、实验批次选择和证据链组织变成可复现的量子—经典协同流程。**

## 先看结果

在可复现的 16 候选合成演示数据上，系统完成了从自然语言目标到验证报告的闭环：

| 指标 | 结果 |
| --- | --- |
| 任务约束 | 选择 3 个候选，成本不超过 5 |
| 量子后端 | Qiskit Aer（本地量子线路模拟器） |
| QAOA 配置 | 16 变量、`p=1`、128 shots、8 次目标评估 |
| 壁仞核心计算 | `torch_br` / SUPA 批量 QUBO 能量评估 |
| 主推荐 | `c08, c10, c13` |
| 验证状态 | `verified`，硬约束通过 |
| 目标值独立重算误差 | `0` |
| 五种子最终推荐可行率 | `100%` |
| 演示/完整评测墙钟时间 | 约 `1.05s` / `4.29s` |

表中基础时间来自 macOS 本地运行；同一推荐和验证状态已在 Linux Docker 与壁仞 Biren106M 单卡环境复现。壁仞运行中，Qiskit Aer 在 CPU 上完成线路模拟，SUPA GPU 参与 QAOA 的批量 QUBO 能量评分。演示数据是合成数据；这些结果证明的是软件链路和原型的可复现性，不是化学性能、量子硬件结果或量子优势证据。

## 从一个实验批次，走向科研发现基础设施

当前原型以反应条件筛选为示范入口，但底层抽象并不绑定某一种化学反应：只要问题能够表达为“候选集合 + 观测历史 + 资源约束 + 多目标偏好”，就可以复用同一套 Agent、代理模型、QUBO 和验证器。

| 未来应用空间 | 可被优化的科研问题 | Q-Discovery Agent 的角色 |
| --- | --- | --- |
| 药物与生命科学 | 候选分子、组合实验、活性/毒性权衡 | 在预算约束下安排下一轮验证实验 |
| 材料与能源 | 配方、工艺窗口、电池材料组合 | 探索性能—成本—风险的 Pareto 前沿 |
| 化学合成 | 反应条件、催化剂、溶剂和温度 | 生成多样化且可执行的实验批次 |
| 工程与科学计算 | 传感器布置、参数扫描、仿真工况 | 选择信息增益最大的下一组计算/实验 |
| 量子算法研发 | 线路参数、Ansatz、噪声与资源配置 | 将量子实验本身纳入闭环优化 |

这些是面向后续数据适配和领域验证的扩展方向；当前提交版本首先把“量子优化驱动科研实验设计”的核心闭环跑通。

**长期愿景**：成为实验室科研操作系统中负责“假设空间导航”的决策内核——让科学家把更多时间用在提出好问题和解释新现象上，把候选搜索、资源分配、实验排程和证据整理交给可验证的智能体流程。

## 作品概念与评审价值

### 1. 从“优化一次实验”到“导航整个假设空间”

科研探索的瓶颈往往不是提出一个候选，而是在有限时间、预算和样本量下，决定下一步验证哪一个假设。Q-Discovery Agent 将一次性优化升级为可持续迭代的实验设计循环：每轮吸收新观测，更新不确定性，再重新寻找最值得验证的候选组合。

### 2. 量子计算参与核心决策

候选实验条件被编码为二进制变量，利用收益、不确定性、条件多样性、成本和风险共同构成 QUBO。Warm Start XY-QAOA 直接对“下一批实验怎么选”求解，而不是把量子线路放在展示页上作为装饰。

### 3. 从自然语言到实验执行计划

用户只需表达“在预算 5 内选择 3 个实验，尽量提高产率并保持多样性”，Agent 就会解析批次、预算和目标方向，并组织后续数据审计、建模、优化和报告导出。

### 4. Agent 作为科研流程编排器

Agent 的价值不在于生成一段漂亮的解释，而在于把跨模块科研流程真正串起来：数据是否可信、模型是否有足够观测、QUBO 是否满足约束、量子后端是否可用、结果是否能够复核，都被纳入同一条可追踪链路。

### 5. 结果先验证，再推荐

每个候选解都会经过独立的固定基数、预算、可用性和目标值重算。验证失败的解会被阻断；量子后端不可用时会明确标记 `fallback=true`，不会把经典回退冒充成 QAOA 或量子优势。

### 6. 把每一次推荐沉淀成科研资产

系统保存输入规格、数据审计、特征表、模型预测、采集函数、QUBO、求解器结果、验证报告和 Agent 事件。评审可以从最终推荐追溯到每一个关键步骤。

### 7. 有基线，也保留失败样例

每轮同时运行精确枚举、贪心、经典批量采集、模拟退火和惩罚式 QAOA。即使 `penalty_qaoa` 产生不可行样本，也会被保留为负向对照并由验证器拒绝，避免只展示“成功截图”。

## 核心叙事：Quantum Scientific Discovery Loop

```text
提出问题 → 形成假设 → 组织候选实验 → 量子搜索组合空间
    ↑                                      ↓
吸收新观测 ← 独立验证与基线比较 ← 输出可执行实验批次
```

这条闭环让量子计算从“单次算法演示”进入科研生产流程：它既可以作为实验条件筛选器，也可以成为材料配方、药物候选、能源工艺和量子算法调参等问题的统一决策内核。当前版本用可复现的小规模实例证明闭环可运行，后续通过数据适配、GPU 加速和更大规模量子线路扩展应用边界。

## Agent 闭环

```text
自然语言科研目标
  → parse_experiment_goal
  → validate_design_spec
  → audit_dataset
  → fit_surrogate
  → build_acquisition
  → compile_qubo
  → solve_batch
  → verify_solution
  → compare_baselines
  → export_run_report
```

每个节点都有明确输入、输出和下一步许可；Agent 不控制真实实验设备、不执行用户代码，也不替代领域专家进行化学安全审批。

## 量子方法概览

设 `x_i∈{0,1}` 表示是否选择候选 `i`，系统优化：

```text
maximize  Σ_i(a_i · x_i) + Σ_i<j(a_ij · x_i · x_j)
subject to  Σ_i x_i = K
            Σ_i cost_i · x_i ≤ B
```

- `a_i`：代理模型预测收益、不确定性、成本和风险的加权得分；
- `a_ij`：候选条件之间的多样性奖励；
- `K`：固定批次大小；`B`：成本预算；
- XY mixer：保持固定基数可行子空间；
- Warm Start：用可行贪心解初始化量子线路；
- Qiskit Aer：在本地经典机器上模拟量子线路和测量采样。

## 一键复现

```bash
python3 -m venv .venv
source .venv/bin/activate

# 开发、测试和 Qiskit Aer 依赖
python -m pip install -e ".[dev,quantum]"

# 正确性：枚举 15 个小规模可行组合，并运行完整服务链
python scripts/run_correctness.py

# 单样例演示：生成验证结果和 artifacts
python scripts/run_demo.py --output artifacts/submission-demo.json

# 五种子稳定性评测
python scripts/run_benchmark.py --seeds 1,2,3,4,5 \
  --output artifacts/submission-benchmark.json
```

预期结果：`correctness passed`、演示状态 `verified`、五种子可行率 `1.0`。如果不安装 Qiskit，系统会运行带警告的 quantum-inspired fallback；该模式适合验证软件链路，不适合描述为量子模拟结果。

## Linux 可复现环境

项目提供基于 Debian Linux + Python 3.11 的 Docker 环境，镜像内包含测试、Qiskit Aer 和完整演示依赖：

```bash
# 构建 Linux 镜像（Docker 会按当前主机架构选择 arm64 或 amd64）
docker build -t q-discovery-agent:linux .

# 运行默认 Qiskit Aer 演示
docker run --rm q-discovery-agent:linux

# 启动 API
docker run --rm -p 8000:8000 q-discovery-agent:linux \
  uvicorn app.main:app --host 0.0.0.0 --port 8000

# 一次执行正确性、demo 和五种子评测
./scripts/run_linux.sh
```

服务器也可使用 Conda：

```bash
conda env create -f environment.yml
conda activate q-discovery-agent
python scripts/run_demo.py --output artifacts/linux-demo.json
```

### 壁仞 SUPA 单卡运行

项目已适配竞赛容器的 Python 3.10、`torch_br`、UnitaryLab 与 SUPA 1.11。Qiskit Aer 负责生成量子线路测量样本，`SupaQUBOEvaluator` 使用 `device="supa"` 在壁仞 GPU 上批量计算 QUBO 能量，用于角度期望值计算和加速评分；最终候选按 CPU 双精度值排序和发布，保持 `1e-8` 发布门槛。

```bash
source /usr/local/birensupa/sdk/1.11.0.0.rc2/scripts/brsw_set_env.sh >/dev/null
python3 -m pip install -e ".[dev,quantum]"

python3 scripts/run_supa_correctness.py --device supa \
  --output artifacts/supa-correctness.json
python3 scripts/run_demo.py --qubo-device supa \
  --output artifacts/biren-demo.json
python3 scripts/run_benchmark.py --seeds 1,2,3,4,5 --qubo-device supa \
  --output artifacts/biren-benchmark.json
```

Biren106M 单卡实测：65,536 个 16 位比特串、16 个线性项和 112 个二次项的批量评分中，CPU/SUPA 最大误差为 `6.171e-5`（阈值 `1e-4`），评分耗时由 `1.733s` 降至 `1.075s`，约 `1.612×`；完整 Agent demo 为 `verified`，后端记录为 `qiskit_aer+torch_supa`，目标值重算误差为 `0`。原始证据见 [`submission/results/biren_single_card/`](./submission/results/biren_single_card/)。

本镜像已完成真实构建和容器内验证：Linux ARM64，以及面向 Intel/AMD CPU 的 Linux AMD64（x86_64）均已通过验证。两种架构均使用 Python 3.11.15、Qiskit 2.5.1、Qiskit Aer 0.17.2；8 个测试通过，demo 状态为 `verified`。完整记录见 [`submission/results/linux_environment_report.md`](./submission/results/linux_environment_report.md)。

Intel 和 AMD 的主流 CPU 都属于 x86_64（Docker 术语为 `linux/amd64`），因此不需要分别维护 Intel 版和 AMD 版。可在 Intel PC/服务器、AMD Ryzen/EPYC 服务器，或 Windows Docker Desktop/WSL2 的 Linux 容器中运行：

```bash
docker build --platform linux/amd64 -t q-discovery-agent:linux-amd64 .
docker run --rm --platform linux/amd64 q-discovery-agent:linux-amd64
```

这里的 Intel/AMD 兼容性指 CPU 运行和 Qiskit Aer 的 CPU 模拟；AMD GPU 的 ROCm 和 Intel GPU 加速仍需单独适配。壁仞 GPU 已用于 QUBO 批量能量评分，但 Qiskit Aer 线路模拟本身仍在 CPU 上执行。

## 运行 API 与 UI

```bash
# FastAPI
uvicorn app.main:app --reload

# Streamlit
python -m pip install -e ".[ui]"
streamlit run ui/streamlit_app.py
```

API 默认对 ASGI 线程池使用安全回退。确认部署环境稳定后，再设置 `Q_DISCOVERY_API_ALLOW_QISKIT=1` 并选择 `backend=auto` 或 `backend=qiskit`。

## 项目结构

```text
app/
├── agents/          # 任务解析与 Agent 编排
├── data/            # 数据加载、特征编码和审计
├── modeling/        # 代理模型与多目标采集函数
├── optimization/    # QUBO、Warm Start、QAOA 和经典基线
├── verification/    # 独立可行性与目标值验证
└── runtime/         # artifact、manifest 和任务运行时
scripts/             # demo、正确性、benchmark、报告导出
tests/               # unit / integration / e2e
ui/                  # Streamlit 演示界面
submission/          # 竞赛提交材料、日志和 PDF
Dockerfile            # Python 3.11 Linux 可复现镜像
environment.yml       # Conda Linux/服务器环境
```

## 工程质量

- 11 个自动化测试通过，覆盖领域模型、QUBO、SUPA 评估器、求解器、API 和端到端流程；
- Ruff 静态检查通过；
- 正确性脚本独立重算目标值，阈值为 `1e-8`；
- 所有求解结果记录随机种子、后端、宽度、深度、shots、调用数、耗时和回退状态；
- `skill.md` 明确能力边界、工具链、输入输出和失败策略。

## 竞赛材料

提交包已经整理在 [`submission/`](./submission/)：

- [提交材料索引](./submission/README.md)
- [提交清单](./submission/MANIFEST.md)
- [场景说明 PDF](./submission/docs/scene_description.pdf)
- [方法说明 PDF](./submission/docs/method_description.pdf)
- [结果分析 PDF](./submission/docs/results_analysis.pdf)
- [Agent/Skill 交互日志](./submission/agent_logs/)
- [正确性与性能报告](./submission/results/)

## 诚实边界与下一步

当前 demo 数据为合成数据，正式科研展示应替换为公开或已授权数据，并记录来源、许可证、快照哈希和字段映射。项目已在 macOS 和 Docker Linux + Qiskit Aer 上复现，但提交到比赛前仍应在壁仞 GPU 平台补录单卡环境、资源和运行日志。项目不宣称量子优势，所有结论都应与经典基线和领域专家复核一起解释。

## 文档导航

- [产品需求文档](./PRD.md)
- [实现 Spec](./IMPLEMENTATION-SPEC.md)
- [Agent/Skill 说明](./skill.md)
- [数据说明](./data/examples/README.md)
