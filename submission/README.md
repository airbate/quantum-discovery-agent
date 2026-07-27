# Q-Discovery Agent 提交材料包

本目录是量子计算赛道的初评材料索引。源码和可复现实验入口位于仓库根目录；提交时将整个仓库打包，或把根目录作为 `code/` 一并上传。

## 目录

```text
submission/
├── README.md
├── MANIFEST.md
├── docs/
│   ├── scene_description.md
│   ├── scene_description.pdf
│   ├── method_description.md
│   ├── method_description.pdf
│   ├── results_analysis.md
│   ├── results_analysis.pdf
│   └── data_provenance.md
├── results/
│   ├── verification_report.md
│   ├── performance_report.md
│   └── linux_environment_report.md
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
- `pyproject.toml`：依赖和开发环境声明。
- `Dockerfile`、`.dockerignore`：Linux 容器构建环境。
- `environment.yml`：Linux/服务器 Conda 环境。
- `scripts/run_linux.sh`：容器内完整正确性与性能复现入口。
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

## 提交前替换项

当前 `data/examples/demo_candidates.csv` 是合成数据，仅用于验证软件链路。正式科研展示应替换为公开或已授权数据，并同步更新 `docs/data_provenance.md`、配置中的 `dataset_id`、数据快照哈希和许可证说明。

如在壁仞 GPU 平台运行，应在 `docs/results_analysis.md` 中补充机器型号、驱动/软件栈、GPU 参与环节和单卡日志；当前报告中的本地运行数据不得冒充壁仞 GPU 实测数据。
