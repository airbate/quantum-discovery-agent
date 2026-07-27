# Q-Discovery Agent 提交材料包

本目录是量子计算赛道的初评材料索引。源码和可复现实验入口位于仓库根目录；提交时将整个仓库打包，或把根目录作为 `code/` 一并上传。

## 目录

```text
submission/
├── README.md
├── MANIFEST.md
├── COMPLIANCE_CHECKLIST.md
├── docs/
│   ├── scene_description.md
│   ├── scene_description.pdf
│   ├── method_description.md
│   ├── method_description.pdf
│   ├── results_analysis.md
│   ├── results_analysis.pdf
│   ├── data_provenance.md
│   └── open_source_attribution.md
├── results/
│   ├── verification_report.md
│   ├── performance_report.md
│   ├── linux_environment_report.md
│   └── biren_single_card/
│       ├── README.md
│       ├── environment.log
│       ├── supa-correctness.json
│       ├── demo-result.json
│       ├── benchmark-result.json
│       ├── accelerator.log
│       └── SHA256SUMS.txt
├── agent_logs/
│   ├── interaction_01.md
│   ├── interaction_02.md
│   ├── interaction_03.md
│   ├── interaction_04.md
│   └── interaction_05.md
└── demo/
    └── demo_script.md
```

## 根目录中的必交文件

- `skill.md`：Agent/Skill 能力边界、工具链路和交互契约。
- `app/`：源码。
- `tests/`：单元、集成和端到端测试。
- `scripts/run_correctness.py`：正确性验证入口。
- `scripts/run_benchmark.py`：多随机种子性能/稳定性入口。
- `scripts/run_demo.py`：单样例演示入口。
- `scripts/run_supa_correctness.py`：CPU/SUPA 批量 QUBO 评分正确性与性能对照。
- `pyproject.toml`：依赖和开发环境声明。
- `Dockerfile`、`.dockerignore`：Linux 容器构建环境。
- `environment.yml`：Linux/服务器 Conda 环境。
- `scripts/run_linux.sh`：容器内完整正确性与性能复现入口。
- `scripts/collect_single_card_evidence.sh`：最终单卡平台的环境、设备、日志、结果和哈希采集入口。
- `data/examples/`：可公开分发的合成演示数据和配置。

## 一键复现

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,quantum]"
python scripts/run_correctness.py
python scripts/run_demo.py --output artifacts/submission-demo.json
python scripts/run_benchmark.py --seeds 1,2,3,4,5 \
  --output artifacts/submission-benchmark.json
```

`run_demo.py` 默认使用 Qiskit Aer；没有安装可选量子依赖时，系统会明确标注 `fallback=true`，不得将回退结果描述为硬件量子优势。

`submission/results/` 中的摘要 JSON 和日志是可直接上传的轻量证据；完整 artifact JSON 由复现命令生成到 `artifacts/`，该目录中的中间文件默认不纳入源码提交。

`docs/` 中的 PDF 由对应 Markdown 源文件导出，适合作为报名系统的展示文档；若系统只接受单个文件，优先上传 PDF，同时保留 Markdown 和源码用于复核。

## 壁仞单卡复现

```bash
source /usr/local/birensupa/sdk/1.11.0.0.rc2/scripts/brsw_set_env.sh >/dev/null
python3 -m pip install -e ".[dev,quantum]"
python3 scripts/run_supa_correctness.py --device supa
python3 scripts/run_demo.py --qubo-device supa --output artifacts/biren-demo.json
```

实测原始证据已归档在 `results/biren_single_card/`。Qiskit Aer 线路模拟运行在 CPU；SUPA GPU 负责 QAOA 批量 QUBO 能量评分，二者在资源字段中分别记录。

## 提交前替换项

当前 `data/examples/demo_candidates.csv` 是合成数据，仅用于验证软件链路。正式科研展示应替换为公开或已授权数据，并同步更新 `docs/data_provenance.md`、配置中的 `dataset_id`、数据快照哈希和许可证说明。

逐项提交状态见 [`COMPLIANCE_CHECKLIST.md`](./COMPLIANCE_CHECKLIST.md)。正式上传前仍建议补充 `brsmi` 和演示页面截图，并在最终 Git commit 上重跑一次证据采集脚本。
