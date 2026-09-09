"""Statistical analysis of the BC-SSI healthcare DES results."""

from __future__ import annotations
import argparse
import math
from pathlib import Path

import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parent
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

def build_latency_percentiles(
    detail: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate request-latency percentiles per replication."""

    rows = []

    grouped = detail.groupby(
        ["architecture", "scenario", "replication"],
        sort=True,
    )

    for (
        architecture,
        scenario,
        replication,
    ), group in grouped:
        latency = group["latency_ms"].astype(float)

        rows.append(
            {
                "architecture": architecture,
                "scenario": scenario,
                "replication": replication,
                "requests": len(group),
                "p50_latency_ms": latency.quantile(0.50),
                "p95_latency_ms": latency.quantile(0.95),
                "p99_latency_ms": latency.quantile(0.99),
                "maximum_latency_ms": latency.max(),
            }
        )

    return pd.DataFrame(rows)

def build_latency_percentile_summary(
    percentiles: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize latency percentiles across replications."""

    rows = []

    grouped = percentiles.groupby(
        ["architecture", "scenario"],
        sort=True,
    )

    for (architecture, scenario), group in grouped:
        row = {
            "architecture": architecture,
            "scenario": scenario,
            "replications": len(group),
        }

        for column in [
            "p50_latency_ms",
            "p95_latency_ms",
            "p99_latency_ms",
            "maximum_latency_ms",
        ]:
            mean, _, ci_low, ci_high = confidence_interval(
                group[column]
            )

            prefix = column.replace("_latency_ms", "")

            row[f"mean_{column}"] = mean
            row[f"{prefix}_ci95_low_ms"] = ci_low
            row[f"{prefix}_ci95_high_ms"] = ci_high

        rows.append(row)

    return pd.DataFrame(rows)
def parse_arguments() -> argparse.Namespace:
    """Read the result directory from the command line."""

    parser = argparse.ArgumentParser(
        description=(
            "Analyse BC-SSI healthcare DES results."
        )
    )

    parser.add_argument(
        "--results-directory",
        default="results",
        help=(
            "Result directory relative to the project "
            "directory."
        ),
    )

    return parser.parse_args()
def main() -> None:
    """Create statistical summaries from simulation replications."""

arguments = parse_arguments()

results_directory = (
        ROOT / arguments.results_directory
    )
input_path = (
        results_directory
        / "baseline_refined_by_replication.csv"
    )
detail_input_path = (
        results_directory
        / "baseline_refined_detail.csv"
    )

if not input_path.exists():
        raise FileNotFoundError(
            f"Simulation result file not found: {input_path}"
        )

results = pd.read_csv(input_path)

if not detail_input_path.exists():
        raise FileNotFoundError(
            f"Detailed result file not found: "
            f"{detail_input_path}"
        )

detail = pd.read_csv(detail_input_path)

latency_percentiles = build_latency_percentiles(
        detail
    )
latency_percentile_summary = (
        build_latency_percentile_summary(
            latency_percentiles
        )
    )
confidence_summary = (
        build_confidence_interval_summary(results)
    )
paired_summary = build_paired_comparison_summary(results)
confidence_summary.to_csv(
        results_directory
        / "statistical_confidence_intervals.csv",
        index=False,
    )

paired_summary.to_csv(
        results_directory
        / "statistical_paired_comparisons.csv",
        index=False,
    )

latency_percentiles.to_csv(
        results_directory
        / "latency_percentiles_by_replication.csv",
        index=False,
    )
latency_percentile_summary.to_csv(
        results_directory
        / "latency_percentiles_summary.csv",
        index=False,
    )

print("Statistical analysis completed.")
print(
        "Created statistical_confidence_intervals.csv"
    )
print(
        "Created statistical_paired_comparisons.csv"
    )
print(
        "Created latency percentile result files."
    )

if __name__ == "__main__":
    main()