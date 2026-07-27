from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from app.agents.orchestrator import AgentOrchestrator, parse_experiment_goal
from app.data.ingest import load_candidates_csv
from app.domain.models import CandidateSource, ExperimentDesignSpec

st.set_page_config(page_title="Q-Discovery Agent", layout="wide")
st.title("Q-Discovery Agent")
st.caption("科研实验批次设计的自验证量子—经典协同智能体")

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
    )
    with st.spinner("运行 Agent、代理模型、QUBO 和验证器..."):
        result = AgentOrchestrator().run(spec, candidates, observations)
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
        st.subheader("验证结果")
        st.json(result.verification.model_dump(mode="json"))
    st.subheader("Agent 调用链")
    st.json(result.agent_events)
    st.download_button(
        "下载运行结果",
        data=json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2),
        file_name="q_discovery_run.json",
        mime="application/json",
    )
