from app.agents.orchestrator import parse_experiment_goal


def test_parse_chinese_batch_and_budget_goal() -> None:
    result = parse_experiment_goal(
        "在总成本不超过 5 的条件下，选择 3 个实验，尽量提高产率。"
    )

    assert result["batch_size"] == 3
    assert result["total_budget"] == 5.0
    assert result["objective_direction"] == "maximize"
    assert result["warnings"] == []


def test_parse_budget_aliases() -> None:
    assert parse_experiment_goal("选择 2 个实验，预算=3.5")["total_budget"] == 3.5
    assert parse_experiment_goal("batch 4, cost <= 6")["total_budget"] == 6.0
