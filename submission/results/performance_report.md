# 性能与资源报告

## 测试入口

```bash
python scripts/run_demo.py --output artifacts/submission-demo.json
python scripts/run_benchmark.py --seeds 1,2,3,4,5 \
  --output artifacts/submission-benchmark.json
```

## 资源配置

| 参数 | 值 |
| --- | --- |
| 后端 | Qiskit Aer 本地模拟器 |
| 量子变量上限 | 16 |
| QAOA 深度 | `p=1` |
| shots | 128 |
| 最大目标函数评估 | 8 |
| 噪声模型 | none |
| 本次实测 GPU | 未使用 GPU；不要解释为壁仞 GPU 实测 |

## 本次运行

| 工作负载 | 墙钟时间 | 结果 |
| --- | ---: | --- |
| 单样例 demo | 约 1.05 秒 | `verified` |
| 5 种子 benchmark | 约 4.29 秒 | 5/5 验证通过 |
| demo 中 QAOA 求解步骤 | 约 0.378 秒 | `qiskit_aer`, `fallback=false` |

以上数字来自当前机器上的 `/usr/bin/time -p`，会随机器、Python 和 Qiskit Aer 版本变化。赛题要求的单样例 10 分钟和完整评测 30 分钟在本次小规模实例上均满足。

## 结果稳定性

| 求解器 | 平均目标值 | 标准差 | 平均耗时（秒） | 可行率 |
| --- | ---: | ---: | ---: | ---: |
| enumeration | 1.989851 | 0.000000 | 0.00967 | 100% |
| greedy | 1.945732 | 0.000000 | 0.000078 | 100% |
| classical_bo | 1.945732 | 0.000000 | 0.000071 | 100% |
| simulated_annealing | 1.981027 | 0.017648 | 0.01356 | 100% |
| penalty_qaoa | 8.484807 | 5.635162 | 0.39300 | 40% |
| warm_start_xy_qaoa | 1.940606 | 0.068720 | 0.38813 | 100% |

## 运行平台迁移说明

正式提交前，在壁仞 GPU 环境执行相同命令并补充：GPU 型号、驱动版本、框架版本、显存峰值、单卡日志和与本地 Aer 结果的差异。当前代码已把后端、宽度、深度、shots、目标函数调用数、耗时和回退状态写入 `resource_usage`。
