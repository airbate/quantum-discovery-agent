# Linux 环境验证报告

## 镜像

- 基础镜像：`python:3.11-slim-bookworm`
- 操作系统：Debian GNU/Linux（Docker Linux）
- 实测架构：`aarch64`
- 内核：`Linux 6.12.76-linuxkit`
- Python：`3.11.15`
- Qiskit：`2.5.1`
- Qiskit Aer：`0.17.2`
- 镜像标签：`q-discovery-agent:linux`
- 镜像 ID：`sha256:e57bd072025f1ac0fc6b81074b9ec7431d18969feb7ba38f14a112e68204fb43`
- 镜像大小：约 224.7 MB

## 验证命令

```bash
docker build -t q-discovery-agent:linux .
docker run --rm q-discovery-agent:linux python -m pytest
docker run --rm q-discovery-agent:linux python scripts/run_correctness.py
docker run --rm q-discovery-agent:linux \
  python scripts/run_demo.py --output artifacts/linux-demo.json
docker run --rm q-discovery-agent:linux \
  python scripts/run_benchmark.py --seeds 1,2,3,4,5 \
  --output artifacts/linux-benchmark.json
```

## 验证结果

- 自动化测试：`8 passed`；
- 正确性枚举：15 个组合通过；
- 演示状态：`verified`；
- QAOA 后端：`qiskit_aer`，`fallback=false`；
- 推荐批次：`c08,c10,c13`；
- 目标值重算误差：`0.0`；
- 五种子评测：5 个种子全部完成；
- 最终推荐可行率：`100%`。

## 平台边界

该报告证明项目可在标准 Linux 容器中复现。当前实测来自 Apple Silicon 主机上的 Docker Linux ARM64 容器，量子线路由 CPU 上的 Qiskit Aer 模拟；它不是壁仞 GPU 实测，也不代表量子硬件结果。迁移到壁仞平台时需要使用主办方认可的基础镜像，并补充驱动、设备、单卡资源和运行日志。
