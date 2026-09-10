"""Statistical analysis of the BC-SSI healthcare DES results."""

from __future__ import annotations
import argparse
import math
from pathlib import Path

import pandas as pd
from scipy import stats


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


def build_capacity_attribution_summary(
    results: pd.DataFrame,
) -> pd.DataFrame:
    """
    Separate baseline-to-refined gains into capacity and architecture.

    Each calculation is paired by replication. For latency, a reduction
    is an improvement; for success rate, an increase is an improvement.
    Percentage shares are calculated from the mean contributions rather
    than by averaging unstable replication-level ratios.
    """

    required_architectures = {
        "baseline",
        "capacity_matched",
        "refined",
    }
    available_architectures = set(results["architecture"])

    if not required_architectures.issubset(
        available_architectures
    ):
        missing = sorted(
            required_architectures - available_architectures
        )
        raise ValueError(
            "Capacity attribution requires all three architectures. "
            f"Missing: {', '.join(missing)}"
        )

    rows = []

    for scenario in sorted(results["scenario"].unique()):
        scenario_results = results[
            results["scenario"] == scenario
        ]

        latency = scenario_results.pivot(
            index="replication",
            columns="architecture",
            values="average_latency_ms",
        )
        success = scenario_results.pivot(
            index="replication",
            columns="architecture",
            values="success_rate",
        )

        latency = latency.dropna(
            subset=sorted(required_architectures)
        )
        success = success.dropna(
            subset=sorted(required_architectures)
        )

        if not latency.index.equals(success.index):
            raise ValueError(
                "Latency and success replications do not match for "
                f"{scenario}."
            )

        latency_from_capacity = (
            latency["baseline"]
            - latency["capacity_matched"]
        )
        latency_from_architecture = (
            latency["capacity_matched"]
            - latency["refined"]
        )
        latency_total = (
            latency["baseline"] - latency["refined"]
        )

        success_from_capacity = (
            success["capacity_matched"]
            - success["baseline"]
        )
        success_from_architecture = (
            success["refined"]
            - success["capacity_matched"]
        )
        success_total = (
            success["refined"] - success["baseline"]
        )

        (
            latency_total_mean,
            _,
            latency_total_low,
            latency_total_high,
        ) = confidence_interval(latency_total)
        (
            latency_capacity_mean,
            _,
            latency_capacity_low,
            latency_capacity_high,
        ) = confidence_interval(latency_from_capacity)
        (
            latency_architecture_mean,
            _,
            latency_architecture_low,
            latency_architecture_high,
        ) = confidence_interval(latency_from_architecture)

        (
            success_total_mean,
            _,
            success_total_low,
            success_total_high,
        ) = confidence_interval(success_total)
        (
            success_capacity_mean,
            _,
            success_capacity_low,
            success_capacity_high,
        ) = confidence_interval(success_from_capacity)
        (
            success_architecture_mean,
            _,
            success_architecture_low,
            success_architecture_high,
        ) = confidence_interval(success_from_architecture)

        if abs(latency_total_mean) > 1e-12:
            latency_capacity_percent = (
                100.0
                * latency_capacity_mean
                / latency_total_mean
            )
            latency_architecture_percent = (
                100.0
                * latency_architecture_mean
                / latency_total_mean
            )
        else:
            latency_capacity_percent = float("nan")
            latency_architecture_percent = float("nan")

        rows.append(
            {
                "scenario": scenario,
                "replications": len(latency),
                "baseline_mean_latency_ms": latency[
                    "baseline"
                ].mean(),
                "capacity_matched_mean_latency_ms": latency[
                    "capacity_matched"
                ].mean(),
                "refined_mean_latency_ms": latency[
                    "refined"
                ].mean(),
                "latency_total_improvement_ms": (
                    latency_total_mean
                ),
                "latency_total_ci95_low_ms": latency_total_low,
                "latency_total_ci95_high_ms": latency_total_high,
                "latency_from_capacity_ms": latency_capacity_mean,
                "latency_from_capacity_ci95_low_ms": (
                    latency_capacity_low
                ),
                "latency_from_capacity_ci95_high_ms": (
                    latency_capacity_high
                ),
                "latency_from_architecture_ms": (
                    latency_architecture_mean
                ),
                "latency_from_architecture_ci95_low_ms": (
                    latency_architecture_low
                ),
                "latency_from_architecture_ci95_high_ms": (
                    latency_architecture_high
                ),
                "latency_percent_from_capacity": (
                    latency_capacity_percent
                ),
                "latency_percent_from_architecture": (
                    latency_architecture_percent
                ),
                "baseline_mean_success_rate": success[
                    "baseline"
                ].mean(),
                "capacity_matched_mean_success_rate": success[
                    "capacity_matched"
                ].mean(),
                "refined_mean_success_rate": success[
                    "refined"
                ].mean(),
                "success_total_improvement": success_total_mean,
                "success_total_ci95_low": success_total_low,
                "success_total_ci95_high": success_total_high,
                "success_from_capacity": success_capacity_mean,
                "success_from_capacity_ci95_low": (
                    success_capacity_low
                ),
                "success_from_capacity_ci95_high": (
                    success_capacity_high
                ),
                "success_from_architecture": (
                    success_architecture_mean
                ),
                "success_from_architecture_ci95_low": (
                    success_architecture_low
                ),
                "success_from_architecture_ci95_high": (
                    success_architecture_high
                ),
            }
        )

    return pd.DataFrame(rows)

def build_ablation_confidence_summary(
    results: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate 95% confidence intervals for ablation outcomes."""

    required_columns = {
        "variant",
        "scenario",
        "replication",
        "success_rate",
        "average_latency_ms",
    }

    missing_columns = required_columns - set(results.columns)
    if missing_columns:
        raise ValueError(
            "Ablation results are missing columns: "
            + ", ".join(sorted(missing_columns))
        )

    rows = []

    for (variant, scenario), group in results.groupby(
        ["variant", "scenario"],
        sort=True,
    ):
        (
            success_mean,
            success_std,
            success_low,
            success_high,
        ) = confidence_interval(group["success_rate"])

        (
            latency_mean,
            latency_std,
            latency_low,
            latency_high,
        ) = confidence_interval(group["average_latency_ms"])

        rows.append({
            "variant": variant,
            "scenario": scenario,
            "replications": group["replication"].nunique(),
            "mean_success_rate": success_mean,
            "success_rate_std": success_std,
            "success_rate_ci95_low": success_low,
            "success_rate_ci95_high": success_high,
            "mean_latency_ms": latency_mean,
            "latency_std_ms": latency_std,
            "latency_ci95_low_ms": latency_low,
            "latency_ci95_high_ms": latency_high,
        })

    return pd.DataFrame(rows)
def build_ablation_paired_comparisons(
    results: pd.DataFrame,
) -> pd.DataFrame:
    """Compare each ablation variant with baseline by replication."""

    rows = []

    variants = sorted(
        variant
        for variant in results["variant"].unique()
        if variant != "baseline"
    )

    for scenario in sorted(results["scenario"].unique()):
        scenario_data = results[
            results["scenario"] == scenario
        ]

        baseline = scenario_data[
            scenario_data["variant"] == "baseline"
        ][
            [
                "replication",
                "success_rate",
                "average_latency_ms",
            ]
        ]

        for variant in variants:
            variant_data = scenario_data[
                scenario_data["variant"] == variant
            ][
                [
                    "replication",
                    "success_rate",
                    "average_latency_ms",
                ]
            ]

            paired = baseline.merge(
                variant_data,
                on="replication",
                suffixes=("_baseline", "_variant"),
                validate="one_to_one",
            )

            if len(paired) != len(baseline):
                raise ValueError(
                    f"Unmatched ablation replications: "
                    f"{variant}, {scenario}"
                )

            (
                success_gain,
                success_low,
                success_high,
                success_p_value,
            ) = paired_test(
                paired["success_rate_variant"],
                paired["success_rate_baseline"],
            )

            (
                latency_reduction,
                latency_low,
                latency_high,
                latency_p_value,
            ) = paired_test(
                paired["average_latency_ms_baseline"],
                paired["average_latency_ms_variant"],
            )

            rows.append({
                "variant": variant,
                "scenario": scenario,
                "replications": len(paired),
                "success_rate_gain": success_gain,
                "success_gain_ci95_low": success_low,
                "success_gain_ci95_high": success_high,
                "success_p_value": success_p_value,
                "latency_reduction_ms": latency_reduction,
                "latency_reduction_ci95_low_ms": latency_low,
                "latency_reduction_ci95_high_ms": latency_high,
                "latency_p_value": latency_p_value,
            })

    return pd.DataFrame(rows)

def build_ablation_overall_summary(
    results: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize ablation outcomes with equal scenario weights."""

    # First average the ten scenarios within each replication.
    by_replication = (
        results.groupby(
            ["variant", "replication"],
            as_index=False,
        )
        .agg(
            success_rate=("success_rate", "mean"),
            average_latency_ms=("average_latency_ms", "mean"),
        )
    )

    rows = []

    for variant, group in by_replication.groupby(
        "variant",
        sort=True,
    ):
        (
            success_mean,
            success_std,
            success_low,
            success_high,
        ) = confidence_interval(group["success_rate"])

        (
            latency_mean,
            latency_std,
            latency_low,
            latency_high,
        ) = confidence_interval(group["average_latency_ms"])

        rows.append({
            "variant": variant,
            "replications": group["replication"].nunique(),
            "mean_success_rate": success_mean,
            "success_rate_std": success_std,
            "success_rate_ci95_low": success_low,
            "success_rate_ci95_high": success_high,
            "mean_latency_ms": latency_mean,
            "latency_std_ms": latency_std,
            "latency_ci95_low_ms": latency_low,
            "latency_ci95_high_ms": latency_high,
        })

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

    ablation_input_path = (
        results_directory
        / "ablation_by_replication.csv"
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

    detail = pd.read_csv(
        detail_input_path,
        low_memory=False,
    )
    if not ablation_input_path.exists():
        raise FileNotFoundError(
            f"Ablation result file not found: "
            f"{ablation_input_path}"
        )

    ablation_results = pd.read_csv(ablation_input_path)

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
    attribution_summary = build_capacity_attribution_summary(
        results
    )
    ablation_confidence_summary = (
        build_ablation_confidence_summary(
            ablation_results
        )
    )
    ablation_paired_comparisons = (
        build_ablation_paired_comparisons(
            ablation_results
        )
    )

    ablation_overall_summary = (
        build_ablation_overall_summary(
            ablation_results
        )
    )
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

    ablation_confidence_summary.to_csv(
        results_directory
        / "ablation_confidence_intervals.csv",
        index=False,
    )

    ablation_paired_comparisons.to_csv(
        results_directory
        / "ablation_paired_comparisons.csv",
        index=False,
    )

    ablation_overall_summary.to_csv(
        results_directory
        / "ablation_overall_confidence_intervals.csv",
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
    print("Created capacity_attribution_summary.csv")
    print("Created ablation_confidence_intervals.csv")
    print("Created ablation_paired_comparisons.csv")
    print(
        "Created ablation_overall_confidence_intervals.csv"
    )

if __name__ == "__main__":
    main()
