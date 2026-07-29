from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from app.agents.orchestrator import AgentOrchestrator, parse_experiment_goal
from app.data.ingest import load_candidates_csv
from app.domain.models import CandidateSource, ExperimentDesignSpec

st.set_page_config(page_title="QuantumPilot Skill", layout="wide")
st.title("QuantumPilot Skill")
st.caption("从自然语言科研目标到可验证实验批次的量子—经典协同 Skill")
st.info("演示模式：Qiskit Aer 负责量子线路模拟，CPU 负责本地 QUBO 能量评分；壁仞 SUPA 单卡结果见提交证据包。")

with st.expander("查看 Skill 能力契约"):
    st.markdown(
        """
        - **输入**：科研目标、候选数据、历史观测、批次规模、预算与约束
        - **调用链**：目标解析 → 数据审计 → 代理模型 → QUBO → QAOA/经典基线 → 独立验证 → 证据导出
        - **输出**：主推荐及备选批次、量子资源、基线比较、验证报告与完整 Agent 事件
        - **边界**：不控制实验设备，不提供化学安全审批，不把模拟结果描述成量子硬件或量子优势
        """
    )

data_path = st.text_input("CSV 数据路径", "data/examples/demo_candidates.csv")
goal = st.text_area(
    "科研目标",
    "在预算 5 内选择 3 个反应条件，最大化产率，同时保留实验多样性",
)
batch_size = st.number_input("批次大小", min_value=1, max_value=20, value=3)
run_button = st.button("运行一轮实验设计", type="primary")

if run_button:
    path = Path(data_path)
    if not path.exists():
        st.error(f"找不到数据文件：{path}")
        st.stop()
    feature_columns = ["ligand", "solvent", "base", "temperature"]
    candidates, observations = load_candidates_csv(path, feature_columns=feature_columns)
    parsed = parse_experiment_goal(goal, default_batch_size=int(batch_size))
    spec = ExperimentDesignSpec(
        run_id="streamlit-demo",
        name="streamlit-demo",
        candidate_source=CandidateSource(dataset_id=path.stem, feature_columns=feature_columns),
        batch={"size": parsed["batch_size"], "total_budget": parsed["total_budget"]},
        solver={"backend": "auto", "qubo_evaluation_device": "cpu"},
    )
    with st.spinner("QuantumPilot Skill 正在编排 Agent、代理模型、QUBO 和验证器..."):
        result = AgentOrchestrator().run(spec, candidates, observations)
    primary = result.recommendations[0]
    verification = result.verification

    if result.status.value == "verified" and not primary.resource_usage.fallback:
        st.success("运行完成：量子—经典流程已通过独立验证，可以发布推荐。")
    else:
        st.warning("运行已完成，但检测到回退或验证警告；请查看资源记录。")

    status_col, backend_col, batch_col, verify_col = st.columns(4)
    status_col.metric("运行状态", result.status.value.upper())
    backend_col.metric("计算后端", primary.resource_usage.backend)
    batch_col.metric("主推荐批次", " · ".join(primary.candidate_ids))
    verify_col.metric("独立验证", str(verification.status).upper())

    left, right = st.columns(2)
    with left:
        st.subheader("推荐批次")
        for recommendation in result.recommendations:
            st.write(
                {
                    "batch": recommendation.batch_id,
                    "candidates": recommendation.candidate_ids,
                    "objective": round(recommendation.predicted_objective, 4),
                    "solver": recommendation.solver_kind.value,
                }
            )
    with right:
        st.subheader("量子资源")
        st.json(primary.resource_usage.model_dump(mode="json"))
        st.subheader("验证结果")
        st.json(verification.model_dump(mode="json"))
    st.subheader("Agent 调用链")
    st.json(result.agent_events)
    st.download_button(
        "下载运行结果",
        data=json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2),
        file_name="q_discovery_run.json",
        mime="application/json",
    )
