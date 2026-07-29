# Submission Manifest

## 项目信息

- 项目名称：QuantumPilot
- 工程名称：Q-Discovery Agent
- 参赛方向：量子应用与跨界探索
- 当前任务：有限预算下的科研实验批次设计
- 版本：0.1.0
- 量子线路后端：Qiskit Aer（CPU 模拟）
- GPU 核心环节：`torch_br` / SUPA 批量 QUBO 能量评分
- 量子配置：16 个变量、QAOA 深度 `p=1`、128 shots、最多 8 次目标函数评估

## 评审要求映射

| 评审要求 | 对应材料 |
| --- | --- |
| `SKILL.md` | 根目录 [`SKILL.md`](../SKILL.md)，含标准 frontmatter、触发描述、输入输出、调用链、验证门禁和能力边界 |
| 项目源码 | [`app/`](../app/)、[`ui/`](../ui/) |
| 依赖与运行命令 | [`pyproject.toml`](../pyproject.toml)、[`environment.yml`](../environment.yml)、[`Dockerfile`](../Dockerfile)、根目录 [`README.md`](../README.md) |
| 正确性脚本与结果 | [`scripts/run_correctness.py`](../scripts/run_correctness.py)、[`results/verification_report.md`](./results/verification_report.md)、[`results/correctness.log`](./results/correctness.log) |
| 性能脚本与报告 | [`scripts/run_benchmark.py`](../scripts/run_benchmark.py)、[`results/performance_report.md`](./results/performance_report.md)、[`results/benchmark.log`](./results/benchmark.log) |
| Linux 可复现环境 | [`scripts/run_linux.sh`](../scripts/run_linux.sh)、[`results/linux_environment_report.md`](./results/linux_environment_report.md) |
| 壁仞单卡日志与结果 | [`results/biren_single_card/`](./results/biren_single_card/)，含环境、测试、SUPA 对照、集成演示、五种子结果和 SHA-256 |
| Agent/Skill 开发日志 | [`agent_logs/interaction_01.md`](./agent_logs/interaction_01.md) 至 [`interaction_05.md`](./agent_logs/interaction_05.md) |
| Agent 原始事件 | [`results/agent_events.json`](./results/agent_events.json) |
| 场景说明 | [`docs/scene_description.pdf`](./docs/scene_description.pdf) 与同名 Markdown 源文件 |
| 方法与量子核心 | [`docs/method_description.pdf`](./docs/method_description.pdf)、[`app/optimization/`](../app/optimization/) |
| 结果分析与正确性 | [`docs/results_analysis.pdf`](./docs/results_analysis.pdf)、[`results/verification_report.md`](./results/verification_report.md) |
| 数据来源声明 | [`docs/data_provenance.md`](./docs/data_provenance.md) |
| 开源资源声明 | [`docs/open_source_attribution.md`](./docs/open_source_attribution.md) |
| 项目概念视频 | [`demo/QuantumPilot_项目概念讲解_剪映成片.mp4`](./demo/QuantumPilot_项目概念讲解_剪映成片.mp4) |
| Skill 实际操作视频 | [`demo/QuantumPilot_Skill实际操作演示_剪映成片.mp4`](./demo/QuantumPilot_Skill实际操作演示_剪映成片.mp4) |
| 学术答辩 PPT | [`presentation/QuantumPilot_学术答辩稿.pptx`](./presentation/QuantumPilot_学术答辩稿.pptx) |
| 演示文稿 | [`demo/actual_demo_video_script.md`](./demo/actual_demo_video_script.md)、[`demo/demo_script.md`](./demo/demo_script.md) |
| 逐项合规检查 | [`COMPLIANCE_CHECKLIST.md`](./COMPLIANCE_CHECKLIST.md) |

## 已复现结果

本地与 Linux 环境：

- 正确性脚本枚举 15 个固定基数可行组合并通过独立验证；
- 演示状态为 `verified`，目标值独立重算误差为 0；
- 五随机种子完成验证，最终推荐可行率 100%；
- 当前自动化测试为 `12 passed`。

竞赛 Docker 的 Biren106M 单卡环境：

- `torch.supa.device_count()` 为 1，Driver/SUPA 为 1.11；
- 65,536 个 QUBO 输入的 CPU/SUPA 最大误差为 `6.171e-5`，阈值为 `1e-4`；
- 评分内核耗时为 `1.733s / 1.075s`，本次实测加速约 `1.612×`；
- 集成演示状态为 `verified`，后端记录为 `qiskit_aer+torch_supa`；
- 五种子评测为 5/5 `verified`，总墙钟时间 25.19 秒。

## 诚实性声明

演示数据为合成反应条件数据，不代表真实湿实验结论。QAOA 结果来自 Qiskit Aer 模拟器，不是量子硬件执行。壁仞 GPU 参与批量 QUBO 能量评分，不参与 Qiskit Aer 线路模拟；本项目不宣称量子优势，也不把单个计算内核的加速扩展为端到端加速。
