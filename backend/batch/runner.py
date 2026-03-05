"""Batch test orchestrator.

Runs multiple test scenarios in parallel, coordinating:
- Agent loop execution
- AI user simulation
- LLM-as-Judge evaluation per turn
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path

from backend.models.conversation import Conversation
from backend.agent.loop import agent_loop_sync
from backend.batch.user_simulator import simulate_user_response
from backend.evaluation.judge import evaluate_turn

_SCENARIOS_PATH = Path(__file__).parent / "scenarios.json"
_RESULTS_DIR = Path(__file__).parent / "results"
_RESULTS_DIR.mkdir(exist_ok=True)

# In-memory results store
_results: dict[str, dict] = {}


def load_scenarios(scenario_ids: list[str] | None = None) -> list[dict]:
    """Load test scenarios from JSON file."""
    with open(_SCENARIOS_PATH, "r", encoding="utf-8") as f:
        scenarios = json.load(f)

    if scenario_ids:
        scenarios = [s for s in scenarios if s["id"] in scenario_ids]

    return scenarios


async def run_single_scenario(scenario: dict) -> dict:
    """Run a single test scenario: agent + user simulator + evaluation.

    Returns a result dict with conversation, evaluations, and metrics.
    """
    conversation = Conversation()
    evaluations = []
    turn_results = []

    # Opening message from the simulated user
    user_message = scenario["opening_message"]
    conversation.add_user_message(user_message)

    max_turns = scenario.get("max_turns", 8)

    for turn in range(max_turns):
        # Agent responds
        try:
            agent_result = await agent_loop_sync(conversation)
        except Exception as e:
            turn_results.append(
                {
                    "turn": turn + 1,
                    "user_message": user_message,
                    "agent_response": f"[ERROR: {str(e)}]",
                    "tool_calls": [],
                    "evaluation": None,
                }
            )
            break

        agent_response = agent_result["response"]

        # Evaluate this turn
        try:
            conv_history = [
                {"role": m.role, "content": m.content}
                for m in conversation.messages
                if m.role in ("user", "assistant")
            ]
            eval_result = await evaluate_turn(conv_history, agent_response)
        except Exception:
            eval_result = {
                "relevance": {"score": 0, "reasoning": "Evaluation failed"},
                "accuracy": {"score": 0, "reasoning": "Evaluation failed"},
                "helpfulness": {"score": 0, "reasoning": "Evaluation failed"},
                "tone": {"score": 0, "reasoning": "Evaluation failed"},
                "overall": {"score": 0, "reasoning": "Evaluation failed"},
            }

        evaluations.append(eval_result)
        turn_results.append(
            {
                "turn": turn + 1,
                "user_message": user_message,
                "agent_response": agent_response,
                "tool_calls": agent_result.get("tool_calls", []),
                "iterations": agent_result.get("iterations", 0),
                "evaluation": eval_result,
            }
        )

        # Check if conversation should end
        if conversation.escalated:
            break

        # Check if the agent seems to have resolved the issue
        if turn >= 2 and any(
            phrase in agent_response.lower()
            for phrase in [
                "glad i could help",
                "happy to help",
                "resolved",
                "working now",
                "let me know if you need",
            ]
        ):
            break

        # Simulate next user response (unless this is the last turn)
        if turn < max_turns - 1:
            try:
                conv_history_for_sim = [
                    {"role": m.role, "content": m.content}
                    for m in conversation.messages
                    if m.role in ("user", "assistant")
                ]
                user_message = await simulate_user_response(
                    conv_history_for_sim, scenario, turn + 1
                )
                conversation.add_user_message(user_message)
            except Exception as e:
                user_message = f"[Simulator error: {str(e)}]"
                break

    # Calculate aggregate metrics
    valid_evals = [e for e in evaluations if e.get("overall", {}).get("score", 0) > 0]
    avg_score = (
        sum(e["overall"]["score"] for e in valid_evals) / len(valid_evals)
        if valid_evals
        else 0
    )

    return {
        "scenario_id": scenario["id"],
        "scenario_name": scenario["name"],
        "product": scenario["product"],
        "category": scenario["issue_category"],
        "total_turns": len(turn_results),
        "escalated": conversation.escalated,
        "avg_overall_score": round(avg_score, 2),
        "turns": turn_results,
        "evaluations_summary": {
            "avg_relevance": _avg_score(evaluations, "relevance"),
            "avg_accuracy": _avg_score(evaluations, "accuracy"),
            "avg_helpfulness": _avg_score(evaluations, "helpfulness"),
            "avg_tone": _avg_score(evaluations, "tone"),
            "avg_overall": round(avg_score, 2),
        },
    }


def _avg_score(evaluations: list[dict], key: str) -> float:
    valid = [e[key]["score"] for e in evaluations if e.get(key, {}).get("score", 0) > 0]
    return round(sum(valid) / len(valid), 2) if valid else 0


async def run_batch_tests(
    run_id: str,
    scenario_ids: list[str] | None = None,
    concurrency: int = 3,
) -> dict:
    """Run batch tests with controlled concurrency.

    Args:
        run_id: Unique identifier for this batch run
        scenario_ids: Optional list of specific scenario IDs to run
        concurrency: Max concurrent scenario executions
    """
    scenarios = load_scenarios(scenario_ids)

    _results[run_id] = {
        "run_id": run_id,
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "total_scenarios": len(scenarios),
        "completed": 0,
        "results": [],
    }

    semaphore = asyncio.Semaphore(concurrency)

    async def run_with_semaphore(scenario: dict) -> dict:
        async with semaphore:
            result = await run_single_scenario(scenario)
            _results[run_id]["completed"] += 1
            return result

    try:
        tasks = [run_with_semaphore(s) for s in scenarios]
        scenario_results = await asyncio.gather(*tasks, return_exceptions=True)

        final_results = []
        for r in scenario_results:
            if isinstance(r, Exception):
                final_results.append({"error": str(r)})
            else:
                final_results.append(r)

        _results[run_id]["results"] = final_results
        _results[run_id]["status"] = "completed"
        _results[run_id]["completed_at"] = datetime.now().isoformat()

        # Calculate overall metrics
        valid = [r for r in final_results if "avg_overall_score" in r]
        _results[run_id]["overall_avg_score"] = (
            round(sum(r["avg_overall_score"] for r in valid) / len(valid), 2)
            if valid
            else 0
        )

        # Save to file
        result_path = _RESULTS_DIR / f"{run_id}.json"
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(_results[run_id], f, indent=2, ensure_ascii=False)

    except Exception as e:
        _results[run_id]["status"] = "failed"
        _results[run_id]["error"] = str(e)

    return _results[run_id]


def get_results(run_id: str) -> dict | None:
    """Get results for a batch run."""
    if run_id in _results:
        return _results[run_id]

    # Try loading from file
    result_path = _RESULTS_DIR / f"{run_id}.json"
    if result_path.exists():
        with open(result_path, "r", encoding="utf-8") as f:
            return json.load(f)

    return None
