# 壁仞单卡实测证据

## 环境

- GPU：Biren106M，单卡，32,512 MiB；
- Driver / SUPA：1.11.0 / 1.11；
- Python：3.10.12；
- PyTorch：2.9.0+cu128；
- Qiskit / Aer：2.5.1 / 0.17.2；
- `torch.supa.device_count()`：1。

## 核心计算

Qiskit Aer 在 CPU 上生成 QAOA 测量样本；`SupaQUBOEvaluator` 通过 `torch_br` 将批量 QUBO 能量评分放到 SUPA GPU，用于角度期望值计算与加速评分。最终候选统一由 CPU 双精度重算和排序，防止 FP32 误差改变接近候选的顺序。

## 结果

| 验证项 | 结果 |
| --- | --- |
| 自动化测试 | 12 passed |
| QUBO 工作负载 | 65,536 比特串，16 变量，16 线性项，112 二次项 |
| CPU / SUPA 耗时 | 1.733s / 1.075s |
| 加速比 | 1.612× |
| CPU / SUPA 最大绝对误差 | `6.171e-5`，阈值 `1e-4` |
| 集成 demo | `verified`，`qiskit_aer+torch_supa`，`fallback=false` |
| demo 目标值重算误差 | 0 |
| 五种子完整评测 | 5/5 `verified`，25.19s |

`SHA256SUMS.txt` 覆盖服务器拉取的原始证据文件。Qiskit Aer 不是量子硬件，当前加速比也不构成量子优势证据。
