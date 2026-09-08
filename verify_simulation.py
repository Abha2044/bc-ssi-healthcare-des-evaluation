"""Verification checks for the BC-SSI healthcare DES model."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config_advanced.json"
RESULTS_DIRECTORY = ROOT / "results"
def require(condition: bool, message: str) -> None:
    """Raise a clear error when a verification condition fails."""

    if not condition:
        raise AssertionError(message)


def load_config() -> dict:
    """Load and return the advanced simulation configuration."""

    require(
        CONFIG_PATH.exists(),
        f"Configuration file not found: {CONFIG_PATH}",
    )

    return json.loads(
        CONFIG_PATH.read_text(encoding="utf-8")
    )
def verify_configuration(config: dict) -> None:
    """Check the main simulation and architecture configuration."""

    simulation = config["simulation"]

    require(
        simulation["duration_seconds"] > 0,
        "Simulation duration must be positive.",
    )
    require(
        simulation["replications"] > 0,
        "Replication count must be positive.",
    )
    require(
        0 <= simulation["warmup_seconds"]
        < simulation["duration_seconds"],
        "Warm-up must be between zero and the duration.",
    )

    for scenario, arrival_rate in simulation[
        "arrival_rate_per_second"
    ].items():
        require(
            arrival_rate > 0,
            f"Arrival rate must be positive: {scenario}",
        )

    for architecture in [
        "baseline",
        "capacity_matched",
        "refined",
    ]:
        require(
            architecture in config,
            f"Missing architecture: {architecture}",
        )

        for name, value in config[architecture].items():
            if name.endswith("_capacity"):
                require(
                    isinstance(value, int) and value > 0,
                    f"Invalid capacity: {architecture}.{name}",
                )

def verify_capacity_matched_design(config: dict) -> None:
    """
    Check that capacity-matched keeps baseline behaviour but uses
    the refined architecture's resource capacities.
    """

    baseline = config["baseline"]
    capacity_matched = config["capacity_matched"]
    refined = config["refined"]

    require(
        baseline.keys() == capacity_matched.keys(),
        "Baseline and capacity-matched parameters do not match.",
    )

    for name, baseline_value in baseline.items():
        matched_value = capacity_matched[name]

        if name.endswith("_capacity"):
            require(
                matched_value == refined[name],
                f"Capacity is not matched to refined: {name}",
            )
        else:
            require(
                matched_value == baseline_value,
                f"Non-capacity parameter changed in "
                f"capacity-matched: {name}",
            )

def verify_main_results(config: dict) -> None:
    """Check completeness and valid ranges in the main results."""

    result_path = (
        RESULTS_DIRECTORY
        / "baseline_refined_by_replication.csv"
    )

    require(
        result_path.exists(),
        f"Main result file not found: {result_path}",
    )

    results = pd.read_csv(result_path)

    require(
        not results.empty,
        "Main result file is empty.",
    )
    require(
        not results.isnull().any().any(),
        "Main results contain missing values.",
    )

    architectures = {
        "baseline",
        "capacity_matched",
        "refined",
    }
    scenarios = set(
        config["simulation"]["arrival_rate_per_second"]
    )
    replication_count = int(
        config["simulation"]["replications"]
    )

    require(
        set(results["architecture"]) == architectures,
        "Main results do not contain all architectures.",
    )
    require(
        set(results["scenario"]) == scenarios,
        "Main results do not contain all configured scenarios.",
    )

    expected_rows = (
        len(architectures)
        * len(scenarios)
        * replication_count
    )
    require(
        len(results) == expected_rows,
        f"Expected {expected_rows} result rows, "
        f"but found {len(results)}.",
    )

    require(
        (results["total_requests"] > 0).all(),
        "Some replications contain no requests.",
    )
    require(
        (results["average_latency_ms"] >= 0).all(),
        "A negative average latency was found.",
    )
    require(
        (results["median_latency_ms"] >= 0).all(),
        "A negative median latency was found.",
    )

    rate_columns = [
        column
        for column in results.columns
        if column.endswith("_rate")
    ]

    for column in rate_columns:
        require(
            results[column].between(0, 1).all(),
            f"Values outside [0, 1] found in {column}.",
        )

def verify_sensitivity_results() -> None:
    """Check that every sensitivity summary exists and has data."""

    summary_files = [
        "workload_sensitivity_summary.csv",
        "trust_failure_sensitivity_summary.csv",
        "credential_status_sensitivity_summary.csv",
        "connector_capacity_sensitivity_summary.csv",
        "cache_ttl_sensitivity_summary.csv",
        "session_revalidation_sensitivity_summary.csv",
    ]

    for filename in summary_files:
        result_path = RESULTS_DIRECTORY / filename

        require(
            result_path.exists(),
            f"Sensitivity result not found: {filename}",
        )

        results = pd.read_csv(result_path)

        require(
            not results.empty,
            f"Sensitivity result is empty: {filename}",
        )
        require(
            not results.isnull().any().any(),
            f"Missing values found in: {filename}",
        )

def main() -> None:
    """Run all verification checks."""

    config = load_config()

    verify_configuration(config)
    print("Configuration checks passed.")

    verify_capacity_matched_design(config)
    print("Capacity-matched design checks passed.")

    verify_main_results(config)
    print("Main result checks passed.")

    verify_sensitivity_results()
    print("Sensitivity result checks passed.")

    print("\nAll simulation verification checks passed.")


if __name__ == "__main__":
    main()