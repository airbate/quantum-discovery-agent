# 开源资源与来源声明

本项目的业务编排、QUBO 构造、Warm Start/XY mixer 线路组织、验证器、报告链路和演示数据由参赛项目实现。以下公开开源软件通过 Python 包依赖使用，没有复制其仓库源码到本项目。

| 资源 | 用途 | 来源 | 许可证 |
| --- | --- | --- | --- |
| Python | 运行时 | <https://www.python.org/> | PSF License |
| Qiskit | 量子线路构建与转译 | <https://github.com/Qiskit/qiskit> | Apache-2.0 |
| Qiskit Aer | 本地量子线路模拟 | <https://github.com/Qiskit/qiskit-aer> | Apache-2.0 |
| FastAPI | HTTP API | <https://github.com/fastapi/fastapi> | MIT |
| Pydantic | 数据模型与输入校验 | <https://github.com/pydantic/pydantic> | MIT |
| Uvicorn | ASGI 服务运行 | <https://github.com/encode/uvicorn> | BSD-3-Clause |
| Streamlit | 可选演示界面 | <https://github.com/streamlit/streamlit> | Apache-2.0 |
| pytest | 自动化测试 | <https://github.com/pytest-dev/pytest> | MIT |
| HTTPX | API 集成测试 | <https://github.com/encode/httpx> | BSD-3-Clause |
| HyperFrames | HTML 动效视频的校验与确定性 MP4 渲染 | <https://github.com/heygen-com/hyperframes> | Apache-2.0 |
| GSAP | 视频中的帧级时间线动画 | <https://gsap.com/> | GSAP Standard License |
| FFmpeg | 最终视频转码与兼容性检查 | <https://ffmpeg.org/> | LGPL/GPL，取决于构建选项 |

竞赛 Docker 另行预装 SUPA SDK、`torch_br`、UnitaryLab 和 `unitarylab_algorithms`。这些组件用于壁仞单卡适配和环境验证，不随本仓库再分发；版本和路径以 `submission/results/biren_single_card/environment.log` 为准，使用权限遵循竞赛平台提供方条款。

实际安装版本由 `pyproject.toml`、容器构建日志和 `python -m pip freeze` 共同确定。正式归档时应保存依赖锁定清单或容器镜像摘要；上游版权和许可证归各自权利人所有。

概念讲解的视觉源稿使用 HyperFrames 和 GSAP 制作；两支最终成片由参赛者在剪映中剪辑，并使用 FFmpeg 转换为 GitHub 可直接打开的 H.264/AAC MP4。仓库只提交最终视频，不再分发剪映工程、缓存或第三方素材。参赛者对最终视频中使用的旁白、字幕、音乐和画面素材承担授权责任。

## 数据与论文

当前 `data/examples/demo_candidates.csv` 是项目自建的合成验收数据，不来源于第三方论文或数据库。真实数据替换时，必须在 `data_provenance.md` 中补充 DOI/URL、版本、下载日期、许可证、快照 SHA-256 和字段映射。论文只作为方法调研来源时也应在展示材料中列出完整参考文献，不能暗示论文作者参与本项目或为本项目结果背书。
