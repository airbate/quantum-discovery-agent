# Linux 环境验证报告

## 镜像（ARM64）

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

## 镜像（Intel/AMD CPU，AMD64）

- Docker 平台：`linux/amd64`（x86_64）
- 实测内核：`Linux 6.12.76-linuxkit`
- Python：`3.11.15`
- Qiskit：`2.5.1`
- Qiskit Aer：`0.17.2`
- 镜像标签：`q-discovery-agent:linux-amd64`
- 镜像 ID：`sha256:08e00715dd016998e52c10227beeff904774f137600f68a65e11dd1d27df418c`
- 镜像大小：约 239.9 MB

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

# Intel/AMD x86_64（在 x86 主机上无需额外参数；在 ARM 主机上可用 Docker 仿真验证）
docker build --platform linux/amd64 -t q-discovery-agent:linux-amd64 .
docker run --rm --platform linux/amd64 q-discovery-agent:linux-amd64 python -m pytest
docker run --rm --platform linux/amd64 q-discovery-agent:linux-amd64 python scripts/run_correctness.py
docker run --rm --platform linux/amd64 q-discovery-agent:linux-amd64 \
  python scripts/run_demo.py --output /tmp/amd64-demo.json
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

AMD64 容器验证结果：`x86_64` 内核、`8 passed`、正确性枚举 15 个组合通过、演示状态 `verified`、QAOA 后端为 `qiskit_aer` 且 `fallback=false`，推荐批次为 `c08,c10,c13`，目标值重算误差为 `0.0`。

## 平台边界

该报告证明项目可在标准 Linux ARM64 和 Linux AMD64 容器中复现。Intel 和 AMD 的主流 CPU 均使用 `linux/amd64`，不需要单独的 Intel/AMD 软件包；在 ARM 主机上运行 AMD64 镜像时由 Docker/QEMU 做跨架构仿真。量子线路由 CPU 上的 Qiskit Aer 模拟；这不是壁仞 GPU 实测，也不代表量子硬件结果。迁移到 AMD GPU（ROCm）、Intel GPU 或壁仞平台时，需要另行适配驱动、设备、资源和后端。
