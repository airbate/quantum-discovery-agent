# 提交合规检查表

本表依据赛事“提交与评审、统一要求、提交规范”逐项映射。`通过` 表示 GitHub 仓库已有可复核材料。

| 要求 | 状态 | 材料与说明 |
| --- | --- | --- |
| `SKILL.md` | 通过 | 根目录 `SKILL.md`，含标准 frontmatter、任务流程、调用链、输入输出、自然语言示例和能力边界 |
| 应用原型或系统代码 | 通过 | `app/`、`ui/`、`tests/` |
| 场景说明文档 | 通过 | `submission/docs/scene_description.md/.pdf` |
| 方法与核心量子环节 | 通过 | `submission/docs/method_description.md/.pdf`、`app/optimization/` |
| 完整依赖和运行命令 | 通过 | `pyproject.toml`、`Dockerfile`、`environment.yml`、根目录 `README.md` |
| 正确性脚本与结果 | 通过 | `scripts/run_correctness.py`、`correctness.log`、`verification_report.md` |
| 性能脚本与报告 | 通过 | `scripts/run_benchmark.py`、`benchmark.log`、`performance_report.md` |
| Agent/Skill 至少 5 段交互 | 通过 | `interaction_01.md` 至 `interaction_05.md`，并有 `agent_events.json` 支撑 |
| 任务流程与调用链 | 通过 | `SKILL.md`、五段交互记录、实际操作视频 |
| 输入输出与自然语言交互 | 通过 | `SKILL.md`、`interaction_01.md`、Streamlit 界面及实际操作视频 |
| 结果分析与正确性说明 | 通过 | `results_analysis.md/.pdf`、`verification_report.md` |
| 平台、环境和核心计算说明 | 通过 | `linux_environment_report.md`、`biren_single_card/environment.log`、`method_description.md` |
| 壁仞单卡运行日志/结果 | 通过 | `biren_single_card/` 含环境、测试、demo、benchmark、SUPA 对照和哈希；文本日志满足“日志或截图”要求 |
| 开源资源来源声明 | 通过 | `data_provenance.md`、`open_source_attribution.md` |
| 演示样例小于 10 分钟 | 通过 | 单样例计算约 1 秒；实际操作视频约 3 分 45 秒 |
| 完整评测小于 30 分钟 | 通过 | 本地五种子约 4 秒；壁仞五种子 25.19 秒 |
| 展示材料 | 通过 | 项目概念视频、Skill 实际操作视频、12 页学术答辩 PPT |
| 能力边界 | 通过 | 明确合成数据、Aer 模拟器、SUPA 评分环节和无量子优势声明 |

## 最终提交确认

- [x] 两支视频与 PPT 已上传 GitHub，并在 README 顶部提供直接入口。
- [x] Skill 名称、项目名称和展示材料统一使用 `QuantumPilot`。
- [x] 主批次候选数与推荐策略数已拆分为两个字段，避免 `3/4` 语义混淆。
- [x] 壁仞服务器原始证据保持不改动，SHA-256 可复核。
- [x] 构建缓存、虚拟环境、PPT 检查文件和视频工程未纳入最终提交。
- [ ] 在比赛平台填写 GitHub 地址、学科、标签和公开可见性，并点击“发布”。

## 评审叙事

自然语言科研目标先被解析为结构化任务；Agent 完成数据审计和代理模型拟合，将有限预算下的实验批次选择编译为 QUBO，再由 Warm Start XY-QAOA 与经典基线共同求解。独立验证器会阻断违反固定基数、预算或目标一致性的结果，并导出资源、后端、随机种子和 artifact 证据链。
