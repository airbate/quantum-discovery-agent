# 方法说明：Q-Discovery Agent

## 1. 系统架构

系统由五层组成：

1. **数据层**：读取候选实验条件与历史观测，完成字段、缺失、重复和可用性审计。
2. **建模层**：用轻量的距离加权近邻集成模型给出预测均值与不确定性，适合小样本冷启动。
3. **决策层**：把利用、探索、多样性、成本和风险组成统一采集函数。
4. **量子优化层**：将候选选择编译成 QUBO，使用可行子空间 Warm Start XY-QAOA；同时运行经典基线。
5. **验证层**：独立重算约束和目标值，拒绝不满足约束或报告不一致的结果，再导出 artifacts。

## 2. 代理模型

对每个候选条件，先通过 `FeatureEncoder` 把类别字段 one-hot、数值字段标准化。设历史观测为 `(z_j, y_j)`，候选特征为 `z_i`，选取距离最近的若干观测：

```text
w_ij = 1 / (||z_i - z_j|| + 0.05)
mu_i = sum_j(w_ij * y_j) / sum_j(w_ij)
```

局部观测离散程度和最近邻距离共同形成保守不确定性 `σ_i`。该模型是可替换的基线适配器，不宣称等价于高斯过程或深度模型。

## 3. 多目标采集函数

每个候选的线性得分为：

```text
a_i = w_e * normalized(mu_i)
    + w_x * normalized(sigma_i)
    + w_c * normalized(1 - cost_i)
    + w_r * normalized(1 - risk_i)
```

候选对 `(i,j)` 的二次项表示条件多样性：

```text
a_ij = w_d * normalized(distance(z_i, z_j))
```

演示配置权重为 exploitation 0.40、exploration 0.25、diversity 0.20、cost 0.10、risk 0.05。归一化仅在当前候选集合内执行，避免不同量纲直接相加。

## 4. QUBO 与约束

令 `x_i=1` 表示选择候选 `i`，优化目标为：

```text
maximize  sum_i(a_i * x_i) + sum_{i<j}(a_ij * x_i * x_j)
```

硬约束包括：

- 固定基数：`Σ_i x_i = K`；
- 预算：`Σ_i cost_i x_i ≤ B`；
- 禁止组合、不可用候选等领域约束。

固定基数在 Warm Start XY-QAOA 中由交换型 mixer 保持在可行子空间。预算和禁止组合在编译阶段预过滤或加入惩罚项；所有解仍必须经过独立 `is_feasible` 验证，不能依赖量子线路本身保证全部业务约束。

## 5. 量子线路与基线

### Warm Start XY-QAOA

- 初态：由可行贪心 Warm Start 生成；
- mixer：相邻比特的 `RXX`/`RYY` 交换门；
- cost phase：按 QUBO 线性项使用 `RZ`，按二次项使用 `RZZ`；
- 角度搜索：固定 warm-start 加逐步收缩扰动，实际期望值来自采样结果；
- 后端：Qiskit Aer；配置 `p=1`、128 shots、最多 8 次目标函数评估。

### 对比基线

- `enumeration`：小规模实例的精确可行枚举；
- `greedy`：逐步最大边际收益；
- `classical_bo`：使用同一采集系数的批量经典基线；
- `simulated_annealing`：在可行解集合上进行随机邻域搜索；
- `penalty_qaoa`：标准 X-mixer 惩罚式 QAOA，用于展示约束处理差异。

## 6. 验证与可复现性

发布推荐前执行：

1. 检查比特串长度和二进制取值；
2. 独立验证固定基数、预算、可用性和禁止组合；
3. 使用同一 QUBO 重新计算目标值，要求绝对误差 `≤1e-8`；
4. 记录后端、宽度、深度、shots、目标函数调用数、耗时和 `fallback`；
5. 保存输入规格、数据审计、特征表、QUBO、求解结果、验证结果和 Agent 事件。

随机种子写入 `SolverConfig`，运行报告引用 artifact 路径。正式评测应固定数据快照和环境锁定文件，避免数据或依赖漂移。

## 7. 失败策略与能力边界

若 Qiskit 不可用或后端异常，系统仅允许进入显式标记的 quantum-inspired fallback；若无可行解、数据不足或验证失败，则返回错误/警告而不发布推荐。当前实现不控制实验设备、不执行用户代码、不做化学安全审批，也不证明量子优势。
