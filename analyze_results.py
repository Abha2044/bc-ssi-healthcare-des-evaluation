"""Statistical analysis of the BC-SSI healthcare DES results."""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parent
RESULTS_DIRECTORY = ROOT / "results"
INPUT_PATH = (
    RESULTS_DIRECTORY
    / "baseline_refined_by_replication.csv"
)
def confidence_interval(
    values: pd.Series,
    confidence: float = 0.95,
) -> tuple[float, float, float, float]:
    """
    Return the mean, standard deviation and confidence limits.

    The interval uses Student's t distribution because each group
    contains a relatively small number of replications.
    """

    clean_values = values.dropna().astype(float)
    sample_size = len(clean_values)

    if sample_size == 0:
        raise ValueError("Cannot analyse an empty sample.")

    mean = float(clean_values.mean())

    if sample_size == 1:
        return mean, 0.0, mean, mean

    standard_deviation = float(clean_values.std(ddof=1))
    standard_error = standard_deviation / math.sqrt(sample_size)

    critical_value = float(
        stats.t.ppf(
            (1.0 + confidence) / 2.0,
            df=sample_size - 1,
        )
    )

    margin = critical_value * standard_error

    return (
        mean,
        standard_deviation,
        mean - margin,
        mean + margin,
    )

def build_confidence_interval_summary(
    results: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate 95% confidence intervals for the main outcomes."""

    rows = []

    grouped = results.groupby(
        ["architecture", "scenario"],
        sort=True,
    )

    for (architecture, scenario), group in grouped:
        (
            success_mean,
            success_std,
            success_ci_low,
            success_ci_high,
        ) = confidence_interval(group["success_rate"])

        (
            latency_mean,
            latency_std,
            latency_ci_low,
            latency_ci_high,
        ) = confidence_interval(group["average_latency_ms"])

        rows.append(
            {
                "architecture": architecture,
                "scenario": scenario,
                "replications": len(group),
                "mean_success_rate": success_mean,
                "success_rate_std": success_std,
                "success_rate_ci95_low": success_ci_low,
                "success_rate_ci95_high": success_ci_high,
                "mean_latency_ms": latency_mean,
                "latency_std_ms": latency_std,
                "latency_ci95_low_ms": latency_ci_low,
                "latency_ci95_high_ms": latency_ci_high,
            }
        )

    return pd.DataFrame(rows)
def paired_test(
    first: pd.Series,
    second: pd.Series,
) -> tuple[float, float, float, float]:
    """
    Return the paired mean difference, confidence limits and p-value.
    """

    differences = (
        first.astype(float).reset_index(drop=True)
        - second.astype(float).reset_index(drop=True)
    )

    (
        mean_difference,
        _,
        ci_low,
        ci_high,
    ) = confidence_interval(differences)

    if (differences == 0).all():
        p_value = 1.0
    else:
        test_result = stats.ttest_rel(
            first.astype(float),
            second.astype(float),
        )
        p_value = float(test_result.pvalue)

    return mean_difference, ci_low, ci_high, p_value

def build_paired_comparison_summary(
    results: pd.DataFrame,
) -> pd.DataFrame:
    """Compare architectures using matched replication numbers."""

    comparisons = [
        ("baseline", "capacity_matched"),
        ("baseline", "refined"),
        ("capacity_matched", "refined"),
    ]

    rows = []

    for scenario in sorted(results["scenario"].unique()):
        scenario_results = results[
            results["scenario"] == scenario
        ]

        for first_name, second_name in comparisons:
            first = (
                scenario_results[
                    scenario_results["architecture"]
                    == first_name
                ]
                .sort_values("replication")
                .reset_index(drop=True)
            )

            second = (
                scenario_results[
                    scenario_results["architecture"]
                    == second_name
                ]
                .sort_values("replication")
                .reset_index(drop=True)
            )

            if len(first) != len(second):
                raise ValueError(
                    f"Unequal replication counts for {scenario}: "
                    f"{first_name} and {second_name}"
                )

            (
                success_difference,
                success_ci_low,
                success_ci_high,
                success_p_value,
            ) = paired_test(
                second["success_rate"],
                first["success_rate"],
            )

            (
                latency_reduction,
                latency_ci_low,
                latency_ci_high,
                latency_p_value,
            ) = paired_test(
                first["average_latency_ms"],
                second["average_latency_ms"],
            )

            rows.append(
                {
                    "scenario": scenario,
                    "comparison": (
                        f"{first_name}_vs_{second_name}"
                    ),
                    "replications": len(first),
                    "success_rate_improvement": (
                        success_difference
                    ),
                    "success_difference_ci95_low": (
                        success_ci_low
                    ),
                    "success_difference_ci95_high": (
                        success_ci_high
                    ),
                    "success_p_value": success_p_value,
                    "latency_reduction_ms": latency_reduction,
                    "latency_reduction_ci95_low_ms": (
                        latency_ci_low
                    ),
                    "latency_reduction_ci95_high_ms": (
                        latency_ci_high
                    ),
                    "latency_p_value": latency_p_value,
                }
            )

    return pd.DataFrame(rows)
def main() -> None:
    """Create statistical summaries from simulation replications."""

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Simulation result file not found: {INPUT_PATH}"
        )

    results = pd.read_csv(INPUT_PATH)

    confidence_summary = (
        build_confidence_interval_summary(results)
    )
    paired_summary = build_paired_comparison_summary(results)

    confidence_summary.to_csv(
        RESULTS_DIRECTORY
        / "statistical_confidence_intervals.csv",
        index=False,
    )

    paired_summary.to_csv(
        RESULTS_DIRECTORY
        / "statistical_paired_comparisons.csv",
        index=False,
    )

    print("Statistical analysis completed.")
    print(
        "Created statistical_confidence_intervals.csv"
    )
    print(
        "Created statistical_paired_comparisons.csv"
    )


if __name__ == "__main__":
    main()