# QuantumPilot 实际操作演示视频文稿

建议时长：4 分钟左右

画面规格：1920×1080，录制浏览器与终端

表达方式：真人旁白或现场讲解；关键结果同时用字幕标出
演示原则：只展示真实运行结果，不把合成数据说成科研发现，不把 Qiskit Aer 说成量子硬件

## 录制前准备

打开两个窗口：

1. 浏览器：QuantumPilot Streamlit 页面；
2. 终端：位于项目根目录，字号调到清晰可读。

启动界面：

```bash
source .venv/bin/activate
streamlit run ui/streamlit_app.py
```

准备好以下结果文件，避免视频中等待：

- `artifacts/submission-demo.json`
- `submission/results/biren_single_card/demo-result.json`
- `submission/results/biren_single_card/accelerator.log`
- `submission/results/performance_report.md`

---

## 0:00–0:20｜开场：我们解决什么问题

### 画面

先展示 QuantumPilot 首页，再快速切到候选实验数据表。鼠标停在成本、风险、历史观测和预测目标等字段上。

### 旁白

> 科研人员经常面对同一个问题：候选实验很多，但时间和预算只允许开展其中一小部分。QuantumPilot 不替科学家下结论，而是帮助研究人员在明确的预算、风险和多样性约束下，选择下一批最值得验证的实验。

### 屏幕字幕

```text
QuantumPilot
面向科学发现的 Agent 原生量子优化工作流
```

---

## 0:20–0:50｜自然语言输入：描述目标，而不是编写算法

### 画面

在目标输入框中输入：

> 在总成本不超过 5 的条件下，选择 3 个实验，尽量提高产率，同时兼顾探索性、条件多样性和风险。

点击“解析目标”或对应的运行按钮，展示结构化任务规格：

```text
batch_size = 3
total_budget = 5
objective = maximize
```

### 旁白

> 用户只需要用自然语言描述研究目标。Agent 会把这句话解析成结构化实验设计任务：批次大小为 3，总预算不超过 5，并同时考虑预测收益、不确定性、多样性、成本和风险。无法识别的目标或互相冲突的约束会被直接返回，而不是进入求解流程。

---

## 0:50–1:25｜Agent/Skills：展示完整任务闭环

### 画面

展示任务流程，按顺序高亮：

```text
parse_experiment_goal
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

在数据审计结果处停留 3 秒，展示候选数、缺失字段和可用状态。

### 旁白

> QuantumPilot 不是一次性的问答界面。Agent 会组织一条有放行条件的科研任务链：先验证任务规格和数据质量，再拟合轻量代理模型，估计候选收益与不确定性，随后构造采集函数并编译 QUBO。求解完成后，结果还必须通过独立验证，最后才会生成报告和可复现 artifact。

### 屏幕字幕

```text
输入 → 数据审计 → 建模 → QUBO → 求解 → 独立验证 → 证据导出
```

---

## 1:25–2:05｜量子核心：QUBO 与 Warm Start XY-QAOA

### 画面

展示 QUBO 参数和求解器配置：

```text
variables = 16
p = 1
shots = 128
max_evaluations = 8
backend = qiskit_aer
```

随后展示目标公式：

```text
maximize  Σᵢ(aᵢxᵢ) + Σᵢ<ⱼ(aᵢⱼxᵢxⱼ)
subject to  Σᵢxᵢ = 3
            Σᵢcostᵢxᵢ ≤ 5
```

### 旁白

> 每个候选实验对应一个二进制变量。线性项综合预测收益、不确定性、成本和风险，二次项奖励候选之间的多样性。固定批次大小由 XY mixer 保持在可行子空间内，Warm Start 使用一个可行的贪心批次初始化线路。这里的 Qiskit Aer 是运行在经典 CPU 上的量子线路模拟器，不是真实量子硬件。

---

## 2:05–2:35｜壁仞 GPU：参与核心 QUBO 评分

### 画面

切到壁仞单卡结果，依次标出：

```text
backend = qiskit_aer+torch_supa
device = Biren106M
QUBO inputs = 65,536
CPU = 1.733s
SUPA = 1.075s
speedup = 1.612×
max_abs_error = 6.171e-5
```

### 旁白

> 在竞赛环境中，Qiskit Aer 仍然在 CPU 上生成线路测量样本。壁仞 Biren106M 通过 torch_br 和 SUPA 批量计算 QUBO 能量，参与角度期望值比较和候选评分。在 65,536 个输入上，评分时间从 1.733 秒下降到 1.075 秒，约为 1.612 倍加速；最大绝对误差为 6.171 乘以 10 的负 5 次方。这个数字只对应当前提交工作负载，不代表量子优势。

---

## 2:35–3:15｜推荐结果：先验证，再发布

### 画面

返回推荐结果页面，放大显示：

```text
selected = c08, c10, c13
selected_count = 3
total_cost = 3.3
budget = 5
status = verified
objective_abs_error = 0
fallback = false
```

再展示经典基线比较，至少包含 enumeration、greedy、simulated_annealing 和 warm_start_xy_qaoa。

### 旁白

> 本次演示推荐 c08、c10 和 c13。系统独立检查了固定批次、预算、候选可用性和目标值：最终选择数量为 3，总成本为 3.3，没有超过预算 5，目标值独立重算误差为 0，状态为 verified，并且没有进入 fallback。QuantumPilot 同时保留精确枚举、贪心、模拟退火和其他求解器结果，避免只展示单一算法的成功样例。

### 屏幕字幕

```text
结果必须通过独立验证，才能进入科研工作流
```

---

## 3:15–3:40｜可复现证据：让评委能够重新运行

### 画面

切到终端，实际执行：

```bash
python scripts/run_demo.py --qubo-device cpu \
  --output artifacts/submission-demo.json
```

如果在壁仞环境录制，则执行：

```bash
python3 scripts/run_demo.py --qubo-device supa \
  --output artifacts/biren-demo.json
```

展示最终输出中的 `verified`，再快速打开 JSON、运行日志和 SHA-256 文件。

### 旁白

> 每次运行都会保存任务规格、数据审计、QUBO、后端、随机种子、求解结果和验证报告。评委可以使用同一条命令重新生成结果，并通过日志和 SHA-256 检查证据是否对应当前提交版本。单样例和完整评测都远低于赛题建议的时间限制。

---

## 3:40–4:00｜结尾：明确价值与边界

### 画面

回到 QuantumPilot 首页或项目收尾页，显示三类应用方向：新药筛选、先进材料、绿色催化。

### 旁白

> 当前演示使用合成数据，证明的是自然语言、Agent 编排、量子优化、GPU 加速和独立验证组成的流程能够运行和复现，它不证明真实化学性能，也不证明量子优势。下一步，我们将接入公开或授权的真实科研数据，并由领域专家评估推荐质量。QuantumPilot 希望让下一批实验更值得被开展，也让每一次推荐都能被复核。

### 结束字幕

```text
QuantumPilot
Quantum Intelligence for Scientific Discovery
让下一批实验，更值得被开展。
```

---

## 录制时不要说错的四句话

不要说：

> 壁仞 GPU 模拟了量子线路。

正确说法：

> Qiskit Aer 在 CPU 上模拟量子线路，壁仞 GPU 批量计算 QUBO 能量。

不要说：

> 项目实现了量子优势。

正确说法：

> 当前结果证明软件链路和混合计算流程可运行，不构成量子优势证据。

不要说：

> 系统发现了新的药物、材料或催化剂。

正确说法：

> 系统在合成数据上完成候选实验优先级排序，真实科研结论需要后续实验验证。

不要说：

> 1.612× 是整个系统的端到端加速。

正确说法：

> 1.612× 是当前工作负载中 QUBO 批量能量评分环节的实测加速。

## 剪辑建议

- 页面操作尽量使用真实录屏，不使用与系统无关的概念动画替代结果页面。
- 等待计算时可做 2–4 倍加速，但不要删除命令和最终退出状态。
- 每个关键数字至少停留 2 秒，并用局部放大或字幕强调。
- 背景音乐控制在旁白以下约 18–24 dB，不使用人工合成旁白。
- 最终成片建议控制在 4 分钟以内；若平台要求 3 分钟，可删除三个应用场景的展开，只保留结尾一屏概览。
