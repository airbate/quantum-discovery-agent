# Q-Discovery Agent

> 把“下一轮做哪些实验”变成可解释、可复现、可验证的量子—经典决策闭环。

面向 2026 书生国智科探挑战赛暨飞翔杯 AI Agent/Skills 开发大赛·量子计算赛道，Q-Discovery Agent 将科研人员的自然语言目标转换为多目标组合优化问题：先审计数据、估计候选条件的收益与不确定性，再编译 QUBO，使用 Warm Start XY-QAOA 和经典基线生成下一批实验，最后由独立验证器决定结果能否发布。

**参赛定位：量子应用与跨界探索** · **应用场景：有限预算下的科研实验批次设计** · **量子核心：可行子空间 QAOA + QUBO**

## 先看结果

在可复现的 16 候选合成演示数据上，系统完成了从自然语言目标到验证报告的闭环：

| 指标 | 结果 |
| --- | --- |
| 任务约束 | 选择 3 个候选，成本不超过 5 |
| 量子后端 | Qiskit Aer（本地量子线路模拟器） |
| QAOA 配置 | 16 变量、`p=1`、128 shots、8 次目标评估 |
| 主推荐 | `c08, c10, c13` |
| 验证状态 | `verified`，硬约束通过 |
| 目标值独立重算误差 | `0` |
| 五种子最终推荐可行率 | `100%` |
| 演示/完整评测墙钟时间 | 约 `1.05s` / `4.29s` |

这些数字来自 macOS 本地运行，演示数据是合成数据；它们证明的是软件链路和原型的可复现性，不是化学性能、量子硬件结果或量子优势证据。

## 为什么这个作品值得评审

### 1. 量子计算参与核心决策

候选实验条件被编码为二进制变量，利用收益、不确定性、条件多样性、成本和风险共同构成 QUBO。Warm Start XY-QAOA 直接对“下一批实验怎么选”求解，而不是把量子线路放在展示页上作为装饰。

### 2. 从自然语言到实验执行计划

用户只需表达“在预算 5 内选择 3 个实验，尽量提高产率并保持多样性”，Agent 就会解析批次、预算和目标方向，并组织后续数据审计、建模、优化和报告导出。

### 3. 结果先验证，再推荐

每个候选解都会经过独立的固定基数、预算、可用性和目标值重算。验证失败的解会被阻断；量子后端不可用时会明确标记 `fallback=true`，不会把经典回退冒充成 QAOA 或量子优势。

### 4. 证据链完整

系统保存输入规格、数据审计、特征表、模型预测、采集函数、QUBO、求解器结果、验证报告和 Agent 事件。评审可以从最终推荐追溯到每一个关键步骤。

### 5. 有基线，也保留失败样例

每轮同时运行精确枚举、贪心、经典批量采集、模拟退火和惩罚式 QAOA。即使 `penalty_qaoa` 产生不可行样本，也会被保留为负向对照并由验证器拒绝，避免只展示“成功截图”。

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
```

## 工程质量

- 8 个自动化测试通过，覆盖领域模型、QUBO、求解器、API 和端到端流程；
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

当前 demo 数据为合成数据，正式科研展示应替换为公开或已授权数据，并记录来源、许可证、快照哈希和字段映射。当前性能数据来自 macOS + Qiskit Aer，提交到比赛前应在壁仞 GPU 平台补录单卡环境、资源和运行日志。项目不宣称量子优势，所有结论都应与经典基线和领域专家复核一起解释。

## 文档导航

- [产品需求文档](./PRD.md)
- [实现 Spec](./IMPLEMENTATION-SPEC.md)
- [Agent/Skill 说明](./skill.md)
- [数据说明](./data/examples/README.md)
