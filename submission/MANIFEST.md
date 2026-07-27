# Submission Manifest

## 项目

- 项目名称：Q-Discovery Agent
- 参赛方向：量子应用与跨界探索（以量子模拟/算法演示为支撑）
- 版本：0.1.0
- 复现入口：`scripts/run_demo.py`
- 主要量子后端：Qiskit Aer（CPU 模拟器）+ `torch_br` / SUPA（QUBO 评分）
- 量子配置：16 个变量上限、QAOA 深度 `p=1`、128 shots、最多 8 次目标函数评估

## 材料映射

| 评审要求 | 本仓库材料 |
| --- | --- |
| `skill.md` | `skill.md` |
| 项目源码 | `app/`、`ui/` |
| 依赖与运行命令 | `pyproject.toml`、`Dockerfile`、`environment.yml`、`scripts/run_linux.sh`、根目录 `README.md` |
| 正确性脚本与结果 | `scripts/run_correctness.py`、`submission/results/verification_report.md` |
| 性能脚本与报告 | `scripts/run_benchmark.py`、`submission/results/performance_report.md` |
| Linux 可复现环境 | `Dockerfile`、`environment.yml`、`scripts/run_linux.sh`、`submission/results/linux_environment_report.md` |
| 单卡运行日志/结果 | `submission/results/biren_single_card/`，含环境、测试、SUPA 对照、集成 demo、五种子结果和 SHA-256 |
| Agent/Skill 交互日志 | `submission/agent_logs/interaction_01.md` 至 `interaction_05.md` |
| 场景和方法说明 | `submission/docs/scene_description.pdf`、`submission/docs/method_description.pdf`（源文件为同名 `.md`，样式为 `pdf.css`） |
| 数据使用声明 | `submission/docs/data_provenance.md` |
| 开源资源来源声明 | `submission/docs/open_source_attribution.md` |
| 演示脚本 | `submission/demo/demo_script.md` |
| 逐项合规检查 | `submission/COMPLIANCE_CHECKLIST.md` |
| 单卡证据采集 | `scripts/collect_single_card_evidence.sh` |

## 复现记录

本次材料生成于 2026-07-28。使用 macOS 本地 Python 3.11 虚拟环境、Qiskit Aer 后端执行：

- 正确性：15 个固定基数可行组合全部通过独立验证。
- 演示：`verified`，硬约束通过，目标值独立重算误差为 0。
- 多种子：5/5 个种子完成验证，最终推荐可行率 100%。
- 端到端脚本墙钟时间：演示约 1.05 秒，多种子评测约 4.29 秒；时间随机器和依赖版本变化。

同日使用竞赛 Docker 的 Biren106M 单卡执行：

- `torch.supa.device_count()` 为 1，Driver/SUPA 为 1.11；
- 65,536 个 QUBO 输入 CPU/SUPA 最大误差 `6.171e-5`，评分加速约 `1.612×`；
- 集成 demo 为 `verified`，后端 `qiskit_aer+torch_supa`，目标值重算误差 0；
- 五种子评测 5/5 `verified`，总墙钟时间 25.19 秒。

## 诚实性声明

本仓库不宣称量子优势。QAOA 结果来自 Qiskit Aer 模拟器；当量子依赖不可用或后端失败时，会显式进入带警告的量子启发式回退。演示数据为合成反应条件数据，不代表真实湿实验结论。

壁仞 GPU 参与 QUBO 批量能量评分，不参与 Qiskit Aer 线路模拟；因此项目只陈述 SUPA 评分环节的实测加速，不把它扩展为整个量子模拟器的 GPU 加速或量子优势。
