# QuantumPilot 提交材料

> 2026 书生国智科探挑战赛暨飞翔杯 AI Agent/Skills 开发大赛 · 量子计算赛道

## 立即查看

| 材料 | 说明 | 一键入口 |
| --- | --- | --- |
| 项目概念讲解 | 2 分 16 秒，介绍科研问题、量子方法、应用场景与能力边界 | [▶ 直接播放 MP4](https://raw.githubusercontent.com/airbate/quantum-discovery-agent/main/submission/demo/QuantumPilot_%E9%A1%B9%E7%9B%AE%E6%A6%82%E5%BF%B5%E8%AE%B2%E8%A7%A3_%E5%89%AA%E6%98%A0%E6%88%90%E7%89%87.mp4) |
| Skill 实际操作 | 约 3 分 45 秒，展示自然语言任务、推荐结果、资源记录和验证链路 | [▶ 直接播放 MP4](https://raw.githubusercontent.com/airbate/quantum-discovery-agent/main/submission/demo/QuantumPilot_Skill%E5%AE%9E%E9%99%85%E6%93%8D%E4%BD%9C%E6%BC%94%E7%A4%BA_%E5%89%AA%E6%98%A0%E6%88%90%E7%89%87.mp4) |
| 学术答辩材料 | 12 页方法、实测结果、壁仞平台证据和应用边界 | [在线查看](https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fraw.githubusercontent.com%2Fairbate%2Fquantum-discovery-agent%2Fmain%2Fsubmission%2Fpresentation%2FQuantumPilot_%E5%AD%A6%E6%9C%AF%E7%AD%94%E8%BE%A9%E7%A8%BF.pptx) · [下载 PPTX](https://raw.githubusercontent.com/airbate/quantum-discovery-agent/main/submission/presentation/QuantumPilot_%E5%AD%A6%E6%9C%AF%E7%AD%94%E8%BE%A9%E7%A8%BF.pptx) |

## 提交入口

- Skill 定义：[根目录 `SKILL.md`](../SKILL.md)
- 源码：[`app/`](../app/) 与 [`ui/`](../ui/)
- 完整依赖：[`pyproject.toml`](../pyproject.toml)、[`environment.yml`](../environment.yml)、[`Dockerfile`](../Dockerfile)
- 一键演示：[`scripts/run_demo.py`](../scripts/run_demo.py)
- 正确性验证：[`scripts/run_correctness.py`](../scripts/run_correctness.py)
- 性能评测：[`scripts/run_benchmark.py`](../scripts/run_benchmark.py)
- 壁仞证据采集：[`scripts/collect_single_card_evidence.sh`](../scripts/collect_single_card_evidence.sh)
- 逐项材料映射：[`MANIFEST.md`](./MANIFEST.md)
- 合规检查：[`COMPLIANCE_CHECKLIST.md`](./COMPLIANCE_CHECKLIST.md)

## 材料目录

```text
submission/
├── README.md
├── MANIFEST.md
├── COMPLIANCE_CHECKLIST.md
├── docs/
│   ├── scene_description.md / .pdf
│   ├── method_description.md / .pdf
│   ├── results_analysis.md / .pdf
│   ├── data_provenance.md
│   └── open_source_attribution.md
├── results/
│   ├── verification_report.md
│   ├── performance_report.md
│   ├── linux_environment_report.md
│   ├── correctness.log
│   ├── benchmark.log
│   └── biren_single_card/
│       ├── README.md
│       ├── environment.log
│       ├── supa-correctness.json / .log
│       ├── demo-result.json / .log
│       ├── benchmark-result.json / .log
│       ├── accelerator.log
│       ├── pytest.log
│       └── SHA256SUMS.txt
├── agent_logs/
│   ├── interaction_01.md
│   ├── interaction_02.md
│   ├── interaction_03.md
│   ├── interaction_04.md
│   └── interaction_05.md
├── demo/
│   ├── QuantumPilot_项目概念讲解_剪映成片.mp4
│   ├── QuantumPilot_Skill实际操作演示_剪映成片.mp4
│   ├── actual_demo_video_script.md
│   ├── demo_script.md
│   └── presentation_outline.md
└── presentation/
    └── QuantumPilot_学术答辩稿.pptx
```

## 一键复现

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,quantum,ui]"

python scripts/run_correctness.py
python scripts/run_demo.py --qubo-device cpu \
  --output artifacts/submission-demo.json
python scripts/run_benchmark.py --seeds 1,2,3,4,5 \
  --output artifacts/submission-benchmark.json
python -m pytest -q
```

预期结果为 `correctness passed`、演示状态 `verified`、五种子最终推荐可行率 `1.0` 和 `12 passed`。未安装 Qiskit 时会明确标记 `fallback=true`，该结果只能用于验证软件链路。

## 壁仞单卡复现

```bash
source /usr/local/birensupa/sdk/1.11.0.0.rc2/scripts/brsw_set_env.sh >/dev/null
python3 -m pip install -e ".[dev,quantum]"
python3 scripts/run_supa_correctness.py --device supa \
  --output artifacts/supa-correctness.json
python3 scripts/run_demo.py --qubo-device supa \
  --output artifacts/biren-demo.json
python3 scripts/run_benchmark.py --seeds 1,2,3,4,5 \
  --qubo-device supa --output artifacts/biren-benchmark.json
```

Qiskit Aer 在线路模拟环节运行于 CPU；SUPA GPU 用于批量 QUBO 能量评分。所有原始服务器日志、结果和 SHA-256 位于 [`results/biren_single_card/`](./results/biren_single_card/)。

## 结果边界

当前候选数据是合成验收数据，用于证明软件闭环、约束验证和平台复现，不代表真实湿实验发现。Qiskit Aer 是量子线路模拟器；项目不宣称量子硬件执行或量子优势。`1.612×` 仅对应本次 SUPA 批量 QUBO 评分内核实测，不代表端到端系统加速比。
