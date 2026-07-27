# 性能与资源报告

## 测试入口

```bash
python scripts/run_demo.py --qubo-device supa --output artifacts/submission-demo.json
python scripts/run_benchmark.py --seeds 1,2,3,4,5 --qubo-device supa \
  --output artifacts/submission-benchmark.json
python scripts/run_supa_correctness.py --device supa \
  --output artifacts/supa-correctness.json
```

## 资源配置

| 参数 | 值 |
| --- | --- |
| 线路模拟后端 | Qiskit Aer（CPU） |
| QUBO 评分后端 | `torch_br` / SUPA（壁仞 GPU） |
| 量子变量上限 | 16 |
| QAOA 深度 | `p=1` |
| shots | 128 |
| 最大目标函数评估 | 8 |
| 噪声模型 | none |
| 本次实测 GPU | Biren106M，32,512 MiB，单卡 |

## 本次运行

| 工作负载 | 墙钟时间 | 结果 |
| --- | ---: | --- |
| 单样例 demo | 约 1.05 秒 | `verified` |
| 5 种子 benchmark | 约 4.29 秒 | 5/5 验证通过 |
| demo 中 QAOA 求解步骤 | 约 0.378 秒 | `qiskit_aer`, `fallback=false` |
| 壁仞 QUBO 批量评分 | CPU `1.733s` / SUPA `1.075s` | `1.612×`，最大误差 `6.171e-5` |
| 壁仞集成 demo 主 QAOA | 约 `1.389s` | `qiskit_aer+torch_supa`，`verified` |
| 壁仞 5 种子完整评测 | `25.19s` | 5/5 `verified`，目标误差均为 0 |

本地数字来自 macOS；壁仞数字来自竞赛 Docker 中的 Biren106M 单卡。赛题建议的单样例 10 分钟和完整评测 30 分钟在两套环境均满足。

## 结果稳定性

| 求解器 | 平均目标值 | 标准差 | 平均耗时（秒） | 可行率 |
| --- | ---: | ---: | ---: | ---: |
| enumeration | 1.989851 | 0.000000 | 0.00967 | 100% |
| greedy | 1.945732 | 0.000000 | 0.000078 | 100% |
| classical_bo | 1.945732 | 0.000000 | 0.000071 | 100% |
| simulated_annealing | 1.981027 | 0.017648 | 0.01356 | 100% |
| penalty_qaoa | 8.484807 | 5.635162 | 0.39300 | 40% |
| warm_start_xy_qaoa | 1.940606 | 0.068720 | 0.38813 | 100% |

## 壁仞正确性与边界

65,536 个 QUBO 输入在 CPU 与 SUPA 上逐项对比，最大绝对误差低于 `1e-4`。完整 demo 的胜出解经 CPU 双精度独立重算后误差为 `0`。Qiskit Aer 线路模拟仍由 CPU 执行，壁仞 GPU 承担的是 QAOA 循环中的批量 QUBO 能量评估；本项目不宣称量子硬件或量子优势。原始日志、JSON 和 SHA-256 位于 `submission/results/biren_single_card/`。
