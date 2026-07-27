# Q-Discovery Agent Skill

## 能力边界

将科研人员关于“有限实验预算下选择下一批实验”的自然语言目标转换为结构化任务，运行代理模型、QUBO 编译、经典基线、量子/量子模拟器求解和独立验证。

本 Skill 不控制真实实验设备，不执行用户代码，不提供化学安全审批，也不承诺量子优势。

## 典型输入

```text
在总成本不超过 5 的条件下，从已有 Suzuki 反应候选中选择 3 个条件，尽量提高产率，同时保留探索性和条件多样性。
```

结构化输入至少包含：候选数据、历史观测、目标指标、批次大小、硬约束、偏好权重、量子资源预算和随机种子。

## 工具调用顺序

```text
parse_experiment_goal
  → validate_design_spec
  → audit_dataset
  → fit_surrogate
  → build_acquisition
  → compile_qubo
  → estimate_resources
  → solve_batch
  → verify_solution
  → compare_baselines
  → export_run_report
```

Agent 不得跳过数据审计或独立验证。求解失败时只能返回错误码和可恢复建议，不能伪造推荐结果。

## 工具接口

| 工具 | 输入 | 输出 |
|---|---|---|
| `parse_experiment_goal` | 自然语言目标、默认批次大小 | 批次大小、预算、目标方向、解析警告 |
| `validate_design_spec` | `ExperimentDesignSpec` | 字段和约束校验结果 |
| `audit_dataset` | 候选、观测、任务规格 | 数据量、缺失、重复、可用候选和警告 |
| `fit_surrogate` | 特征表、历史观测 | 模型 ID、预测均值和不确定性 |
| `build_acquisition` | 预测、偏好权重 | 线性/二次采集系数 |
| `compile_qubo` | 候选、采集系数、硬约束 | 变量映射、QUBO、约束处理说明 |
| `estimate_resources` | QUBO、量子配置 | 宽度、深度、Shot 和时间估计 |
| `solve_batch` | QUBO、求解配置、Warm Start | 候选批次、采样、资源和警告 |
| `verify_solution` | 解、原始候选、规格、QUBO | 独立可行性、目标一致性和状态 |
| `compare_baselines` | 各求解器结果 | 统一指标和预算比较 |
| `export_run_report` | 所有 artifact | JSON/Markdown 运行报告 |

## 输出约束

正式推荐必须：

- 恰好选择 (K) 个候选；
- 通过独立硬约束验证；
- 提供基线结果、随机种子和资源记录；
- 标注是否使用真实 Qiskit、量子模拟器或经典回退；
- 区分模型预测、算法测量结果和 Agent 解释。

## 有效交互示例

1. 创建一个 3 个候选的固定基数任务并运行穷举正确性检查。
2. 输入“预算 5，选择 3 个实验”，解析出 `batch_size=3` 和 `total_budget=5`。
3. 对缺少目标列的数据请求补充或降级说明。
4. 对禁止组合产生可行性警告并阻断正式推荐。
5. 量子宽度超限时生成邻域分解或经典回退建议。
6. 求解结果违反固定基数时由验证器拒绝发布。
