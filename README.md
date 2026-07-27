# Q-Discovery Agent

Q-Discovery Agent 是一个面向科研实验批次设计的自验证量子—经典协同智能体。它把自然语言科研目标转换成多目标组合优化问题，用代理模型、Warm Start、固定基数约束保持 QAOA 和独立验证器推荐下一批实验。

## 快速运行

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python scripts/run_correctness.py
python scripts/run_demo.py
```

默认环境没有 Qiskit 时，系统会运行一个明确标注的 quantum-inspired fallback。启用真实 Qiskit Aer 模拟器：

```bash
python -m pip install -e ".[quantum]"
python scripts/run_demo.py
```

启动 API：

```bash
uvicorn app.main:app --reload
```

API 默认使用标注为 `fallback=true` 的安全回退，避免部分 Python/ASGI 线程池环境中的原生量子扩展崩溃。确认部署环境稳定后，可显式设置 `Q_DISCOVERY_API_ALLOW_QISKIT=1` 并在 SolverConfig 中使用 `backend=auto` 或 `backend=qiskit`。

启动 UI（需要 `pip install -e ".[ui]"`）：

```bash
streamlit run ui/streamlit_app.py
```

完整多种子评测：

```bash
python scripts/run_benchmark.py --seeds 1,2,3,4,5
python scripts/export_report.py artifacts/demo-result.json --output artifacts/demo-report.md
```

## 结果边界

系统会同时输出量子/量子模拟器结果和经典基线。没有安装 Qiskit 或量子后端失败时，结果会包含 `fallback=true` 与警告；该结果不能被描述为硬件 QAOA 或量子优势证据。

## 文档

- [产品需求文档](./PRD.md)
- [实现 Spec](./IMPLEMENTATION-SPEC.md)
- [Agent/Skill 说明](./skill.md)
- [比赛提交材料索引](./submission/README.md)
- [提交材料清单](./submission/MANIFEST.md)

## 参赛材料

`submission/` 包含场景说明、方法说明、数据使用声明、正确性/性能报告、5 段 Agent/Skill 交互记录和演示脚本。提交时请将整个仓库作为源码包上传，并按 `submission/MANIFEST.md` 检查材料。
