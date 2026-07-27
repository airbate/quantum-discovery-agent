# Q-Discovery Agent 实现 Spec

> 对应产品文档：[PRD.md](./PRD.md)
> 文档版本：v0.1
> 实现目标：先完成可复现的离线科研实验批次选择闭环，再接入量子模拟器/赛事量子平台。
> 适用范围：MVP、赛事演示、首个化学反应条件优化案例
> 更新时间：2026-07-27

## 1. 实现目标与非目标

### 1.1 必须实现

系统必须能够完成以下端到端流程：

```text
CSV/JSON 历史实验数据
    + 候选实验池
    + 自然语言科研目标
    + 批次大小与约束
        ↓
ExperimentDesignSpec
        ↓
数据审计与代理模型
        ↓
多目标采集函数
        ↓
QUBO / Ising 编译
        ↓
经典 Warm Start
        ↓
XY-Mixer QAOA 或经典回退求解
        ↓
独立可行性与质量验证
        ↓
推荐批次、Pareto 备选、基线比较、运行产物
        ↓
导入下一轮结果并更新模型
```

实现必须满足：

- 推荐批次恰好包含 (K) 个候选，或在不可行时明确报告不可行原因；
- 所有硬约束都经过独立验证；
- 量子结果与经典基线在相同候选、数据和资源预算下比较；
- 固定数据、配置、种子和依赖版本能够重现主要指标；
- 标准演示端到端运行时间不超过 10 分钟，完整评测不超过 30 分钟；
- 每个 Agent/Skill 调用生成结构化输入、输出和日志。

### 1.2 暂不实现

- 不控制真实实验设备；
- 不自动执行危险化学实验；
- 不训练新的大语言模型或化学基础模型；
- 不生成无限化学空间中的全新分子；
- 不承诺量子优势或量子加速；
- 不允许 Agent 执行任意 Python、Shell 或用户上传代码。

## 2. 固定技术决策

### 2.1 运行时

| 层 | MVP 选择 | 选择理由 |
|---|---|---|
| 语言 | Python 3.11 | 科学计算、Qiskit、数据处理生态完整 |
| API | FastAPI + Pydantic v2 | 类型化契约、自动 OpenAPI、便于测试 |
| 前端 | Streamlit | 以最少前端代码完成实验表格、图表和 Agent 演示 |
| 数值 | NumPy、SciPy、pandas | 矩阵、优化、表格和特征处理 |
| 代理模型 | scikit-learn 为默认，GP/Ensemble 可插拔 | 小数据、混合变量和本地部署友好 |
| 量子电路 | Qiskit + Aer Adapter | 兼容状态向量、采样模拟器和可替换硬件后端 |
| QUBO | 自有轻量编译器 | 保留变量映射、约束来源和验证元数据 |
| 优化参数 | scikit-optimize 或自实现 BO Adapter | 控制 QAOA 角度调用预算 |
| 持久化 | SQLite + 本地 artifact 目录 | MVP 无需部署独立数据库，易于打包复现 |
| 日志 | Python logging + JSON Lines | 便于界面展示、审计和离线分析 |
| 打包 | `pyproject.toml` + lock 文件 | 固定依赖，支持赛事环境部署 |

量子电路层必须使用 Adapter，不在业务模块中直接依赖特定 SDK。若赛事环境更适合 PennyLane 或 UnitaryLab，只实现同一 Adapter 接口即可替换。

### 2.2 项目目录

```text
quantum-discovery-agent/
├── pyproject.toml
├── README.md
├── skill.md
├── IMPLEMENTATION-SPEC.md
├── PRD.md
├── app/
│   ├── api.py
│   ├── settings.py
│   ├── dependencies.py
│   ├── domain/
│   │   ├── enums.py
│   │   ├── models.py
│   │   └── errors.py
│   ├── data/
│   │   ├── ingest.py
│   │   ├── audit.py
│   │   ├── features.py
│   │   └── repository.py
│   ├── modeling/
│   │   ├── surrogate.py
│   │   ├── acquisition.py
│   │   └── active_learning.py
│   ├── optimization/
│   │   ├── qubo.py
│   │   ├── constraints.py
│   │   ├── warm_start.py
│   │   ├── qaoa.py
│   │   ├── neighborhoods.py
│   │   └── baselines.py
│   ├── agents/
│   │   ├── orchestrator.py
│   │   ├── schemas.py
│   │   ├── tools.py
│   │   └── guardrails.py
│   ├── verification/
│   │   ├── feasibility.py
│   │   ├── objective.py
│   │   ├── exact.py
│   │   ├── metrics.py
│   │   └── report.py
│   └── runtime/
│       ├── jobs.py
│       ├── artifacts.py
│       └── manifests.py
├── ui/
│   ├── streamlit_app.py
│   ├── pages/
│   └── components/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── fixtures/
├── data/
│   ├── raw/
│   ├── processed/
│   └── examples/
├── artifacts/
└── scripts/
    ├── run_demo.py
    ├── run_correctness.py
    ├── run_benchmark.py
    └── export_report.py
```

目录结构表达职责，不要求最终文件名完全固定；模块边界和数据契约必须保持。

## 3. 领域模型与数据契约

所有跨模块对象使用 Pydantic 模型。数据库和 artifact 文件中保存模型的 JSON 序列化结果；不通过解析自然语言日志重建状态。

### 3.1 枚举

```python
class RunStatus(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    MODELED = "modeled"
    COMPILED = "compiled"
    SOLVED = "solved"
    VERIFIED = "verified"
    PRESENTED = "presented"
    UPDATED = "updated"
    FAILED = "failed"

class SolverKind(str, Enum):
    ENUMERATION = "enumeration"
    GREEDY = "greedy"
    SIMULATED_ANNEALING = "simulated_annealing"
    CLASSICAL_BO = "classical_bo"
    PENALTY_QAOA = "penalty_qaoa"
    WARM_START_XY_QAOA = "warm_start_xy_qaoa"

class ConstraintMode(str, Enum):
    PRE_FILTER = "pre_filter"
    EXACT_SUBSPACE = "exact_subspace"
    PENALTY = "penalty"
    SLACK_QUBO = "slack_qubo"
```

### 3.2 ExperimentDesignSpec

```json
{
  "run_id": "run_20260727_0001",
  "name": "suzuki_batch_round_01",
  "domain": "reaction_condition_optimization",
  "objective": {
    "metric": "isolated_yield",
    "direction": "maximize",
    "unit": "fraction"
  },
  "candidate_source": {
    "dataset_id": "dataset_suzuki_v1",
    "candidate_id_column": "candidate_id",
    "feature_columns": ["ligand", "solvent", "base", "temperature", "time"],
    "observed_target_column": "yield"
  },
  "batch": {
    "size": 5,
    "total_budget": 100.0,
    "max_runtime_minutes": 480
  },
  "preferences": {
    "exploitation": 0.40,
    "exploration": 0.25,
    "diversity": 0.20,
    "cost": 0.10,
    "risk": 0.05
  },
  "hard_constraints": [
    {"type": "exact_cardinality", "value": 5},
    {"type": "forbidden_pair", "left": "candidate_004", "right": "candidate_019"}
  ],
  "solver": {
    "kind": "warm_start_xy_qaoa",
    "max_quantum_width": 16,
    "p": 2,
    "shots": 512,
    "angle_optimizer": "bayesian",
    "max_objective_calls": 24,
    "seed": 20260727
  }
}
```

### 3.3 核心对象

#### Candidate

```text
candidate_id: string                 # 全局唯一且稳定
raw_features: object                 # 原始变量和值
encoded_features: array[float]       # 模型特征
cost: float
risk: float
runtime_minutes: float | null
availability: bool
metadata: object
```

#### Observation

```text
candidate_id: string
target: float
observed_at: datetime | null
round_id: string
source: historical | simulated_oracle | user_import
quality_flags: list[string]
```

#### ModelPrediction

```text
candidate_id: string
mean: float
std: float
lower_bound: float
upper_bound: float
model_id: string
training_observation_ids: list[string]
```

#### QUBOProblem

```text
problem_id: string
variable_ids: list[string]
linear: map[int, float]
quadratic: map[string, float]       # key 为 "i,j" 且 i < j
constant: float
objective_direction: "minimize" | "maximize"
constraints: list[CompiledConstraint]
normalization: NormalizationSpec
source_acquisition_id: string
```

#### CandidateBatch

```text
batch_id: string
candidate_ids: list[string]
predicted_components: object
predicted_objective: float
solver_kind: SolverKind
sample_probability: float | null
resource_usage: ResourceUsage
```

#### VerificationReport

```text
status: "passed" | "failed" | "warning"
hard_constraint_results: list[ConstraintResult]
objective_recomputed: float
objective_reported: float
objective_abs_error: float
is_feasible: bool
baseline_comparison: list[BaselineResult]
stability: StabilitySummary
warnings: list[string]
artifact_ids: list[string]
```

### 3.4 版本规则

- `dataset_id`、`feature_schema_hash`、`objective_config_hash` 和 `solver_config_hash` 必须进入 RunManifest。
- 修改特征编码、归一化、约束编译或模型超参数时必须创建新的版本号。
- 不能在同一 `run_id` 下覆盖已验证产物；更新轮次创建新的 `round_id`。

## 4. 运行时架构

### 4.1 组件关系

```text
Streamlit UI
    │
    ▼
FastAPI / Job Service
    │
    ├── Agent Orchestrator
    │       ├── Task Parser Skill
    │       ├── Data Audit Skill
    │       ├── Modeling Skill
    │       ├── QUBO Compile Skill
    │       ├── Solve Skill
    │       ├── Verify Skill
    │       └── Report Skill
    │
    ├── SQLite Metadata Repository
    ├── Artifact Store
    └── Domain Services
            ├── Data/Feature Service
            ├── Surrogate Service
            ├── Acquisition Service
            ├── QUBO/Constraint Compiler
            ├── Solver Adapters
            └── Verification Service
```

### 4.2 同步与异步边界

- 目标解析、参数校验和小规模可行性检查使用同步调用。
- 模型训练、QUBO 编译、QAOA、基线比较和报告生成使用 Job Service。
- 每个 job 写入阶段状态和 JSONL 日志；UI 通过轮询 job 状态展示进度。
- MVP 使用进程内 Job Runner；若后续需要并发，再替换为 Celery/RQ，不改变上层接口。
- 同一个 `run_id` 同时只能有一个写入型 job；重复提交返回已有 job_id。

### 4.3 Artifact 设计

每次运行在 `artifacts/<run_id>/<round_id>/` 下生成：

```text
manifest.json
input_spec.json
data_audit.json
feature_schema.json
model_predictions.parquet
acquisition_config.json
qubo_problem.json
warm_start.json
solver_config.json
solver_samples.json
candidate_batches.json
verification_report.json
baseline_results.json
metrics.json
run.log.jsonl
```

Artifact 写入采用临时文件加原子重命名。文件内容生成 SHA-256 摘要，并由 `manifest.json` 引用。

## 5. 数据输入与审计实现

### 5.1 支持格式

- CSV：首行必须为字段名；
- JSON/JSONL：每条记录表示一个候选或观察；
- MVP 不支持 Excel 宏、数据库连接和远程数据源。

### 5.2 字段规范

数据集至少包含：

- 稳定候选标识；
- 一个或多个实验变量；
- 目标值（历史观察行必须有，未来候选行可以为空）；
- 可选成本、风险和预计时长。

字段审计输出：

- 记录数、候选数、观察数；
- 重复候选和重复观察；
- 缺失比例及处理策略；
- 类别数、数值范围和异常值；
- 目标值分布；
- 可能的数据泄漏字段；
- 可用于建模的候选数量；
- 可执行硬约束检查。

### 5.3 数据处理规则

- 候选标识缺失或重复时任务进入 `FAILED`，不自动猜测。
- 目标值缺失只允许出现在未观察候选中。
- 数值异常默认标记并在界面要求确认，不静默删除。
- 类别变量使用训练数据拟合编码器；未知类别采用明确的 unknown token。
- 训练、验证和隐藏 Oracle 数据按 round 隔离，禁止使用未来观测。

## 6. 代理模型与采集函数

### 6.1 Surrogate Adapter

```python
class SurrogateAdapter(Protocol):
    def fit(self, observations: list[Observation], features: FeatureTable) -> ModelFitReport: ...
    def predict(self, features: FeatureTable) -> list[ModelPrediction]: ...
    def evaluate(self, validation: ValidationSplit) -> ModelEvaluation: ...
```

默认实现：

1. 数据少且特征维度低：Gaussian Process；
2. 类别和非线性较强：随机森林/ExtraTrees 集成；
3. 不确定性：GP 后验标准差或集成预测标准差；
4. 不确定性不足时，禁止开启探索项或明确降级为基线模式。

### 6.2 特征层

- 数值变量按训练集统计量标准化；
- 类别变量使用 one-hot 或稳定 ordinal encoding；
- 分子/结构字段在 MVP 中仅支持已预计算的数值描述符，不在运行时调用外部化学软件；
- 所有特征映射保存 `feature_schema.json`。

### 6.3 采集函数

对候选 (i) 的单点效用使用：


```text
single_i =
  exploitation * normalize(mean_i)
  + exploration * normalize(std_i)
  - cost_weight * normalize(cost_i)
  - risk_weight * normalize(risk_i)
```

批次多样性使用：

```text
pairwise_ij = diversity_weight * distance(feature_i, feature_j)
```

编译器将单点项放入线性系数，将 pairwise 项放入二次系数。默认距离为归一化特征的余弦距离或 Gower 距离；距离实现必须在任务配置中记录。

### 6.4 多目标输出

MVP 生成三种固定偏好配置：

- `high_yield`：利用权重高；
- `high_information`：不确定性与多样性权重高；
- `low_cost_risk`：成本与风险惩罚高。

后续允许用户输入连续权重网格。每种配置独立编译和验证，最后执行非支配过滤和重复批次去除。

## 7. QUBO 与约束编译

### 7.1 目标方向

领域服务统一使用“最大化效用”表达；底层量子与部分经典库若要求最小化，则在编译时转换为：


```text
energy(x) = -utility(x) + penalties(x)
```

转换前后必须保留 `objective_direction`、常数项和归一化信息。

### 7.2 固定基数约束

量子 XY 模式：

- 使用 (K) 个 1 的初始计算基态或等价可行初态；
- 使用交换相邻激发的 XY Mixer；
- 采样解码时再次检查 (sum_i x_i = K)；
- 不为固定基数重复添加高惩罚项，避免数值条件恶化。

经典/惩罚回退模式：


```text
penalty_cardinality = lambda_k * (sum_i x_i - K)^2
```

`lambda_k` 由目标系数绝对值上界推导，配置中保存推导结果。

### 7.3 成本与资源约束

编译策略按优先级选择：

1. 候选预筛选：删除明显不可执行的候选；
2. 邻域级可行性过滤：只生成满足预算的局部候选；
3. 小规模问题加入二进制 slack 变量形成 QUBO；
4. 若引入 slack 后超过量子宽度，降级到经典可行性过滤并报告原因。

不能把不可表示的约束静默忽略。每个约束必须带 `mode`、`source`、`penalty` 或 `filter_reason`。

### 7.4 稀疏化

当 pairwise 多样性矩阵过密时：

- 默认保留每个候选的 top-p 差异边；
- p 为配置项，默认 8；
- 稀疏化前后比较总效用和 Top-k 候选变化；
- 结果报告必须注明稀疏化比例。

## 8. Warm Start、QAOA 与量子 Adapter

### 8.1 Warm Start 生成

```python
class WarmStartProvider(Protocol):
    def generate(
        self,
        problem: QUBOProblem,
        batch_size: int,
        seed: int,
    ) -> WarmStartArtifact: ...
```

MVP 默认流程：

1. 按单点效用排序；
2. 逐项加入不违反硬约束的候选；
3. 使用 pairwise diversity 进行一次局部交换改良；
4. 若存在成本约束，继续交换直到满足预算；
5. 输出固定基数可行 bitstring 和初始目标值。

Stretch 实现可以加入连续松弛解到量子初态振幅的映射，但不得影响 MVP 的可复现性。

### 8.2 QAOA Adapter

```python
class QuantumOptimizerAdapter(Protocol):
    def solve(
        self,
        problem: QUBOProblem,
        config: SolverConfig,
        warm_start: WarmStartArtifact | None,
    ) -> SolverArtifact: ...

    def estimate_resources(
        self,
        problem: QUBOProblem,
        config: SolverConfig,
    ) -> ResourceEstimate: ...
```

MVP 参数默认值：

```text
p = 1 或 2
shots = 512
max_objective_calls = 24
angle_optimizer = bayesian
backend = aer_qasm
noise_model = none（演示）或 configurable（评测）
seed = required
```

量子求解流程：

1. 校验变量数、固定基数和配置预算；
2. 构造成本 Hamiltonian；
3. 构造与初态子空间一致的 XY Mixer；
4. 将 Warm Start 编译成可行初态；
5. 用贝叶斯优化搜索 (gamma,eta)；
6. 采样并按 energy/utility 排序；
7. 由 `SolutionDecoder` 转换成候选批次；
8. 交给独立验证器，不直接宣布成功。

### 8.3 参数迁移

- `round_n` 优先使用 `round_{n-1}` 的最优角度作为初始候选；
- 如果问题变量或深度改变，按层复制可迁移参数，其余参数用固定种子初始化；
- 同时运行少量“无迁移”对照，记录迁移带来的调用次数和质量变化。

### 8.4 邻域分解

```python
class NeighborhoodBuilder(Protocol):
    def build(
        self,
        candidates: list[Candidate],
        predictions: list[ModelPrediction],
        warm_start: WarmStartArtifact,
        max_width: int,
        seed: int,
    ) -> list[QuantumNeighborhood]: ...
```

默认策略：

1. 取 Warm Start 中的候选作为 active core；
2. 加入高不确定性候选；
3. 加入与当前批次距离较大的候选；
4. 加入当前解的一步交换邻居；
5. 按信息量和宽度截断到 `max_quantum_width`；
6. 对每个邻域固定外部变量，重新计算局部 (K')；
7. 运行量子求解后合并全局可行批次并去重。

必须输出每个邻域的成员、固定变量和局部预算，保证结果可审计。

## 9. 经典基线实现

所有基线实现同一 `BatchSolver` 接口：

```python
class BatchSolver(Protocol):
    def solve(
        self,
        problem: QUBOProblem,
        budget: SolverBudget,
        seed: int,
    ) -> SolverArtifact: ...
```

必须包含：

- `EnumerationSolver`：只用于小规模正确性；
- `GreedySolver`：按单点效用加局部交换；
- `SimulatedAnnealingSolver`：固定迭代/时间预算；
- `ClassicalBatchBOSolver`：在原始候选空间直接运行批量采集策略；
- `PenaltyQAOASolver`：X Mixer + 惩罚项；
- `WarmStartXYQAOASolver`：MVP 主方法。

基线不能访问量子方法产生的中间结果，也不能使用隐藏 Oracle 标签。

## 10. Agent 与 Skill 实现

### 10.1 工具白名单

Agent 只能调用以下工具：

```text
parse_experiment_goal
validate_design_spec
audit_dataset
fit_surrogate
build_acquisition
compile_qubo
estimate_resources
solve_batch
verify_solution
compare_baselines
import_observations
update_active_learning_round
export_run_report
```

工具参数全部使用 Pydantic Schema。工具不得接受任意代码字符串、Shell 命令或未经验证的路径。

### 10.2 Agent 工具返回格式

```json
{
  "tool_name": "compile_qubo",
  "status": "success",
  "run_id": "run_20260727_0001",
  "artifact_id": "artifact_qubo_001",
  "summary": "compiled 16-variable objective",
  "warnings": [],
  "next_allowed_tools": ["estimate_resources", "solve_batch"]
}
```

失败返回：

```json
{
  "tool_name": "solve_batch",
  "status": "failed",
  "error_code": "QUANTUM_WIDTH_EXCEEDED",
  "message": "compiled problem has 28 active variables, limit is 16",
  "recoverable": true,
  "suggested_actions": ["build_neighborhood", "run_classical_baseline"]
}
```

### 10.3 编排规则

- Agent 不能跳过 `validate_design_spec`、`audit_dataset` 或 `verify_solution`。
- 未通过验证的任务不得进入正式求解。
- 求解失败时只能建议降级、缩小邻域或修改配置，不能伪造结果。
- 关键数值必须引用 artifact，不从 LLM 自由生成。
- 用户修改硬约束后，之前的 QUBO 和求解结果标记为过期。

### 10.4 赛事 Skill 文档

`skill.md` 必须说明：

- Skill 的科研任务边界；
- 输入字段和自然语言示例；
- 每个工具的调用顺序；
- 工具输入/输出 JSON Schema；
- 量子与经典后端选择规则；
- 验证失败和资源超限的处理；
- 不支持真实实验控制和量子优势承诺；
- 至少五组有效调用日志。

## 11. API 设计

FastAPI 提供以下接口；UI 可以直接调用，也可以在本地进程中调用同一 Service 层。

### 11.1 创建任务

```http
POST /api/v1/runs
Content-Type: application/json
```

请求体为 `ExperimentDesignSpec` 草案。返回 `201` 和：

```json
{
  "run_id": "run_20260727_0001",
  "status": "draft",
  "next_action": "validate_design_spec"
}
```

### 11.2 启动阶段 Job

```http
POST /api/v1/runs/{run_id}/jobs
Content-Type: application/json
```

```json
{
  "job_type": "full_pipeline",
  "round_id": "round_01"
}
```

返回：

```json
{
  "job_id": "job_001",
  "run_id": "run_20260727_0001",
  "status": "queued"
}
```

### 11.3 查询运行状态

```http
GET /api/v1/runs/{run_id}
GET /api/v1/jobs/{job_id}
```

返回当前状态、阶段进度、错误摘要和 artifact 引用。

### 11.4 导入实验结果

```http
POST /api/v1/runs/{run_id}/rounds/{round_id}/observations
```

服务器校验 candidate_id、目标值、round_id 和数据版本；导入成功后只能创建新的更新 Job。

### 11.5 读取结果

```http
GET /api/v1/runs/{run_id}/rounds/{round_id}/recommendations
GET /api/v1/runs/{run_id}/rounds/{round_id}/verification
GET /api/v1/runs/{run_id}/artifacts/{artifact_id}
```

## 12. UI 实现

Streamlit 页面按以下顺序构建：

### 12.1 数据页

- 上传 CSV/JSON；
- 选择候选 ID、特征列和目标列；
- 展示审计结果；
- 确认异常和缺失处理。

### 12.2 任务页

- 文本框输入科研目标；
- 表单确认变量、批次大小、成本和风险；
- 展示 Agent 解析后的 `ExperimentDesignSpec`；
- 允许用户编辑后再次校验。

### 12.3 求解页

- 显示候选数量、活跃量子宽度和估算资源；
- 选择量子/经典求解器；
- 配置 QAOA 深度、Shot、角度调用数和种子；
- 显示运行阶段和 JSONL 日志摘要。

### 12.4 结果页

- 推荐实验表格；
- 高收益、高探索、低成本/风险三组 Pareto 批次；
- 每项预测、标准差、成本、风险和选择原因；
- 约束通过/失败标记；
- 与基线的条形图或表格比较；
- QAOA 资源和采样统计；
- 下载 CSV、JSON、报告和日志。

### 12.5 多轮页

- 导入实验结果；
- 查看 Best Found Value、Simple Regret、Hypervolume 和 Batch Diversity 曲线；
- 比较参数迁移与重新初始化；
- 启动下一轮。

## 13. 错误模型

错误必须使用稳定错误码，不以自然语言作为程序判断依据。

| 错误码 | 触发条件 | 默认处理 |
|---|---|---|
| `INVALID_SCHEMA` | 输入字段不完整或类型错误 | 阻断并显示字段级错误 |
| `DUPLICATE_CANDIDATE` | 候选 ID 重复 | 阻断数据审计 |
| `NO_FEASIBLE_BATCH` | 不存在满足硬约束的 (K) 个候选 | 返回不可行证明摘要 |
| `MODEL_INSUFFICIENT_DATA` | 观察数据少于模型最低要求 | 降级为基线或要求补充数据 |
| `UNCERTAINTY_UNAVAILABLE` | 模型无法产生可信不确定性 | 禁止探索模式 |
| `QUBO_NUMERIC_RANGE` | 系数范围导致模拟器不稳定 | 重新归一化或阻断 |
| `QUANTUM_WIDTH_EXCEEDED` | 超过配置量子宽度 | 进入邻域分解或经典回退 |
| `SOLVER_TIMEOUT` | 超过阶段时间预算 | 保存中间结果并可恢复 |
| `VERIFICATION_FAILED` | 解不满足硬约束或目标不一致 | 不发布推荐 |
| `ARTIFACT_WRITE_FAILED` | 产物无法持久化 | 标记运行失败 |

## 14. 测试实现

### 14.1 单元测试

测试 `domain`、特征编码、采集函数、QUBO 编译、约束、采样解码、指标和错误码。

重点断言：

- 输入输出对象通过 Schema；
- 目标函数与手工计算一致；
- 固定基数始终为 (K)；
- QUBO 对称/上三角约定一致；
- 缺失和重复数据不被静默接受；
- 归一化处理可逆或误差在容差内。

### 14.2 集成测试

- 数据导入 → 审计 → 特征 → 代理模型；
- 代理模型 → 采集函数 → QUBO；
- QUBO → Warm Start → QAOA Adapter；
- 求解器输出 → 独立验证器；
- 结果导入 → 新一轮代理模型。

### 14.3 端到端测试

固定 fixture 完成两轮反应条件优化。端到端测试不检查具体某个随机样本，而检查：

- 状态按规定顺序推进；
- 推荐批次可行；
- 产物齐全；
- 基线和验证报告可读取；
- 固定种子下核心指标在容差内复现。

### 14.4 研究评测脚本

提供三个独立命令：

```bash
python scripts/run_correctness.py
python scripts/run_benchmark.py --seeds 1,2,3,4,5
python scripts/run_demo.py --config data/examples/demo_config.json
```

脚本不能依赖 Streamlit 页面运行，确保评委可以在命令行重新生成结果。

## 15. 性能与资源预算

### 15.1 演示默认配置

```text
candidate_count: 64–128
active_quantum_width: 12–16
qaoa_depth: 1–2
shots: 256–512
angle_objective_calls: ≤24
neighborhood_count: ≤4
random_seeds: 3（演示）；5（完整评测）
```

### 15.2 完整评测默认配置

```text
candidate_count: 128–512
active_quantum_width: ≤20
qaoa_depth: ≤3
shots: 512–1024
angle_objective_calls: ≤40
neighborhood_count: ≤8
```

若预计超过 30 分钟，系统必须在启动前显示资源估算，并提供缩小邻域、降低 Shot、减少种子或切换经典基线的选项。

### 15.3 资源记录

每次运行记录：

- CPU 型号、核心数和内存；
- GPU/量子后端名称（若有）；
- 量子电路宽度、深度和 Shot；
- QAOA 目标函数调用数；
- 墙钟时间和各阶段耗时；
- 峰值内存；
- 是否发生回退。

## 16. 交付顺序

### Milestone 1：可验证数学原型

交付：数据 fixture、候选编码、采集函数、QUBO 编译器、穷举和贪心基线、正确性脚本。

退出条件：小规模实例的 QUBO 目标与直接目标一致，固定基数和预算约束测试通过。

### Milestone 2：量子核心

交付：Penalty QAOA、Warm-start XY-QAOA、QAOA 角度 BO、采样解码和资源估算。

退出条件：同一问题可以在两个量子模式和至少两个经典基线间公平比较。

### Milestone 3：规模化主动学习

交付：邻域分解、模型更新、隐藏 Oracle 回放、多轮指标和消融脚本。

退出条件：至少三个任务、五个种子完成完整回放，结果可生成 JSON 和报告。

### Milestone 4：Agent 与界面

交付：结构化需求解析、工具白名单、Streamlit 页面、运行日志和 artifact 下载。

退出条件：自然语言输入可以完成至少五组有效工具调用，验证失败不能发布推荐。

### Milestone 5：赛事打包

交付：`skill.md`、安装/运行说明、正确性脚本、性能报告、演示配置、截图和视频脚本。

退出条件：新环境可按 README 启动，演示在 10 分钟内完成，完整评测不超过 30 分钟。

## 17. 关键技术取舍

### 17.1 为什么先用离线回放

真实湿实验不可控、耗时高且不适合在赛事环境稳定复现。离线回放仍然可以测量主动学习决策质量、批次多样性、预算效率和量子求解可行性。系统保留 `simulated_oracle` 与 `user_import` 数据源，为后续真实实验接入留下接口。

### 17.2 为什么优先 XY Mixer

本项目的核心决策不是“选任意数量的候选”，而是“在固定实验预算下选恰好 (K) 个”。XY Mixer 将这个结构直接放入量子搜索空间，减少无效样本，并形成明确的量子算法创新点。

### 17.3 为什么保留经典回退

量子后端可能不可用、超时或超过宽度。回退保证产品可用，但所有回退都必须在结果页显示；回退结果不能伪装成量子结果。

### 17.4 为什么使用独立验证器

科研软件的可信度来自可复核证据，不来自 Agent 的语言流畅度。验证器不读取求解器的“成功”状态，而是重新计算约束和目标，并对小问题执行穷举。

## 18. 实现完成定义

只有同时满足以下条件，MVP 才算完成：

- PRD 中的首个场景可以从输入数据运行到两轮推荐；
- Warm-start XY-QAOA 和至少四个基线能在统一接口下运行；
- 小问题拥有穷举正确性证据；
- 大问题拥有邻域分解和资源报告；
- 推荐批次经过独立验证并满足硬约束；
- Agent 不能跳过关键验证阶段；
- 所有核心结果有 artifact、日志、配置和随机种子；
- 赛事要求的 `skill.md`、运行说明、正确性脚本和性能脚本齐全；
- 结果报告同时呈现正向、无差异和失败案例；
- 文档没有把尚未证实的结果表述为量子优势。
