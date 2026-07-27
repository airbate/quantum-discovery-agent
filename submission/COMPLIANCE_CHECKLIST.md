# 提交合规检查表

本表依据赛事“提交与评审、统一要求、提交规范”逐项映射。`已具备` 表示仓库中已有可复核材料。

| 要求 | 状态 | 材料与说明 |
| --- | --- | --- |
| `skill.md` | 已具备 | 根目录 `skill.md`，包含任务流程、调用链、输入输出、自然语言示例和能力边界 |
| 应用原型或系统代码 | 已具备 | `app/`、`ui/`、`tests/` |
| 场景说明 | 已具备 | `submission/docs/scene_description.md/.pdf` |
| 方法与核心量子环节 | 已具备 | `submission/docs/method_description.md/.pdf`、`app/optimization/` |
| 完整依赖和运行命令 | 已具备 | `pyproject.toml`、`Dockerfile`、`environment.yml`、根目录 `README.md` |
| 正确性脚本与结果 | 已具备 | `scripts/run_correctness.py`、`submission/results/correctness.log`、`verification_report.md` |
| 性能脚本与报告 | 已具备 | `scripts/run_benchmark.py`、`benchmark.log`、`performance_report.md` |
| Agent/Skill 至少 5 段交互 | 已具备 | `submission/agent_logs/interaction_01.md` 至 `interaction_05.md`，并有 `agent_events.json` 支撑 |
| 结果分析与正确性说明 | 已具备 | `submission/docs/results_analysis.md/.pdf`、`submission/results/verification_report.md` |
| 平台和运行环境说明 | 已具备 | `linux_environment_report.md` 与 `biren_single_card/environment.log` |
| 公开资源来源声明 | 已具备 | `submission/docs/data_provenance.md`、`open_source_attribution.md` |
| 演示样例小于 10 分钟 | 已具备 | 当前约 1 秒，见 `performance_report.md` |
| 完整评测小于 30 分钟 | 已具备 | 当前五种子约 4 秒，见 `performance_report.md` |
| 展示材料 | 部分具备 | `submission/demo/demo_script.md`、`presentation_outline.md`；正式 PPT、录屏和截图仍建议制作 |
| 单卡运行日志/截图/结果 | 已具备 | `submission/results/biren_single_card/`，含环境、测试、demo、benchmark、SUPA 对照和哈希 |
| 壁仞 GPU 核心计算说明 | 已具备 | `SupaQUBOEvaluator` 承担 QAOA 批量能量评分；Aer 线路模拟仍在 CPU |

## 最终提交前必须完成

1. 录制 3 分钟演示，覆盖自然语言输入、Agent 调用链、QUBO/QAOA、SUPA 评分、独立验证和能力边界。
2. 提交前在最终代码提交上再执行一次 `bash scripts/collect_single_card_evidence.sh`，核对 SHA-256。
3. 截图应包含 `brsmi` 单卡信息和结果摘要；原始文本日志继续作为可检索证据。

## 评审叙事建议

评审展示应围绕一条可核验主线：自然语言科研目标被解析为结构化任务，Agent 先审计数据并建立代理模型，再把实验批次选择编译成 QUBO，由 Warm Start XY-QAOA 与经典基线共同求解，最后由独立验证器阻断不可行结果并导出完整证据链。不要把合成数据说成科研发现，也不要把 Aer 模拟说成量子硬件或量子优势。
