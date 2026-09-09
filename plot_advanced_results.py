"""Create publication-quality figures from DES result files."""

from __future__ import annotations
import argparse
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

import pandas as pd


ROOT = Path(__file__).resolve().parent
RESULTS_DIRECTORY = ROOT / "results"
FIGURES_DIRECTORY = ROOT / "figures"

ARCHITECTURE_COLORS = {
    "baseline": "#6B7280",
    "capacity_matched": "#D97706",
    "refined": "#2563EB",
}

ARCHITECTURE_LABELS = {
    "baseline": "Baseline",
    "capacity_matched": "Capacity-matched",
    "refined": "Refined",
}

def configure_plot_style() -> None:
    """Apply a consistent publication-oriented plot style."""

    plt.rcParams.update(
        {
            "figure.dpi": 120,
            "savefig.dpi": 300,
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "legend.fontsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "grid.linestyle": "--",
        }
    )


def scenario_label(name: str) -> str:
    """Convert a scenario identifier into a readable label."""

    return name.replace("_", " ").title()

def plot_architecture_comparison() -> None:
    """Plot success rate and latency for all scenarios."""

    data = pd.read_csv(
        RESULTS_DIRECTORY
        / "statistical_confidence_intervals.csv"
    )

    scenarios = sorted(data["scenario"].unique())
    architectures = [
        "baseline",
        "capacity_matched",
        "refined",
    ]

    y_positions = np.arange(len(scenarios))
    bar_height = 0.24

    figure, axes = plt.subplots(
        1,
        2,
        figsize=(13, 7),
        constrained_layout=True,
    )

    for index, architecture in enumerate(architectures):
        architecture_data = (
            data[data["architecture"] == architecture]
            .set_index("scenario")
            .loc[scenarios]
        )

        positions = (
            y_positions
            + (index - 1) * bar_height
        )

        success_mean = architecture_data[
            "mean_success_rate"
        ]
        success_error = np.vstack(
            [
                success_mean
                - architecture_data[
                    "success_rate_ci95_low"
                ],
                architecture_data[
                    "success_rate_ci95_high"
                ]
                - success_mean,
            ]
        )

        axes[0].barh(
            positions,
            success_mean,
            height=bar_height,
            xerr=success_error,
            color=ARCHITECTURE_COLORS[architecture],
            label=ARCHITECTURE_LABELS[architecture],
            capsize=2,
        )

        latency_mean = architecture_data[
            "mean_latency_ms"
        ]
        latency_error = np.vstack(
            [
                latency_mean
                - architecture_data[
                    "latency_ci95_low_ms"
                ],
                architecture_data[
                    "latency_ci95_high_ms"
                ]
                - latency_mean,
            ]
        )

        axes[1].barh(
            positions,
            latency_mean,
            height=bar_height,
            xerr=latency_error,
            color=ARCHITECTURE_COLORS[architecture],
            label=ARCHITECTURE_LABELS[architecture],
            capsize=2,
        )

    readable_scenarios = [
        scenario_label(name)
        for name in scenarios
    ]

    for axis in axes:
        axis.set_yticks(y_positions)
        axis.set_yticklabels(readable_scenarios)
        axis.invert_yaxis()

    axes[0].set_title("Success rate by scenario")
    axes[0].set_xlabel("Mean success rate")
    axes[0].set_xlim(0, 1.05)
    axes[0].legend(loc="lower right")

    axes[1].set_title("Mean latency by scenario")
    axes[1].set_xlabel("Mean latency (ms, logarithmic scale)")
    axes[1].set_xscale("log")

    figure.savefig(
        FIGURES_DIRECTORY
        / "architecture_scenario_comparison.png",
        bbox_inches="tight",
    )
    figure.savefig(
        FIGURES_DIRECTORY
        / "architecture_scenario_comparison.pdf",
        bbox_inches="tight",
    )

    plt.close(figure)
def plot_workload_sensitivity() -> None:
    """Plot architecture behaviour as workload increases."""

    data = pd.read_csv(
        RESULTS_DIRECTORY
        / "workload_sensitivity_summary.csv"
    )

    emergency = data[
        data["scenario"] == "emergency_access"
    ]

    figure, axes = plt.subplots(
        1,
        2,
        figsize=(10, 4),
        constrained_layout=True,
    )

    for architecture in [
        "baseline",
        "capacity_matched",
        "refined",
    ]:
        architecture_data = (
            emergency[
                emergency["architecture"] == architecture
            ]
            .sort_values("workload_multiplier")
        )

        label = ARCHITECTURE_LABELS[architecture]
        color = ARCHITECTURE_COLORS[architecture]

        axes[0].plot(
            architecture_data["workload_multiplier"],
            architecture_data["mean_success_rate"],
            marker="o",
            linewidth=2,
            color=color,
            label=label,
        )

        axes[1].plot(
            architecture_data["workload_multiplier"],
            architecture_data["mean_latency_ms"],
            marker="o",
            linewidth=2,
            color=color,
            label=label,
        )

    axes[0].set_title("Success under increasing workload")
    axes[0].set_xlabel("Workload multiplier")
    axes[0].set_ylabel("Mean success rate")
    axes[0].set_ylim(0.94, 1.0)
    axes[0].legend()

    axes[1].set_title("Latency under increasing workload")
    axes[1].set_xlabel("Workload multiplier")
    axes[1].set_ylabel(
        "Mean latency (ms, logarithmic scale)"
    )
    axes[1].set_yscale("log")

    figure.savefig(
        FIGURES_DIRECTORY / "workload_sensitivity.png",
        bbox_inches="tight",
    )
    figure.savefig(
        FIGURES_DIRECTORY / "workload_sensitivity.pdf",
        bbox_inches="tight",
    )

    plt.close(figure)


def plot_trust_failure_sensitivity() -> None:
    """Plot resilience as trust-service failures increase."""

    data = pd.read_csv(
        RESULTS_DIRECTORY
        / "trust_failure_sensitivity_summary.csv"
    )

    figure, axes = plt.subplots(
        1,
        2,
        figsize=(10, 4),
        constrained_layout=True,
    )

    for architecture in [
        "baseline",
        "capacity_matched",
        "refined",
    ]:
        architecture_data = (
            data[data["architecture"] == architecture]
            .sort_values("trust_failure_probability")
        )

        label = ARCHITECTURE_LABELS[architecture]
        color = ARCHITECTURE_COLORS[architecture]

        axes[0].plot(
            architecture_data[
                "trust_failure_probability"
            ],
            architecture_data[
                "mean_trust_resolution_success_rate"
            ],
            marker="o",
            linewidth=2,
            color=color,
            label=label,
        )

        axes[1].plot(
            architecture_data[
                "trust_failure_probability"
            ],
            architecture_data["mean_latency_ms"],
            marker="o",
            linewidth=2,
            color=color,
            label=label,
        )

    axes[0].set_title("Trust resolution success")
    axes[0].set_xlabel("Trust-service failure probability")
    axes[0].set_ylabel("Mean resolution success rate")
    axes[0].set_ylim(0.75, 1.01)
    axes[0].legend()

    axes[1].set_title("Latency during trust-service failures")
    axes[1].set_xlabel("Trust-service failure probability")
    axes[1].set_ylabel("Mean latency (ms)")
    axes[1].legend()

    figure.savefig(
        FIGURES_DIRECTORY
        / "trust_failure_sensitivity.png",
        bbox_inches="tight",
    )
    figure.savefig(
        FIGURES_DIRECTORY
        / "trust_failure_sensitivity.pdf",
        bbox_inches="tight",
    )

    plt.close(figure)   

def plot_cache_ttl_sensitivity() -> None:
    """Plot cache latency benefit and estimated staleness risk."""

    data = pd.read_csv(
        RESULTS_DIRECTORY
        / "cache_ttl_sensitivity_summary.csv"
    ).sort_values("cache_ttl_seconds")

    figure, axes = plt.subplots(
        1,
        2,
        figsize=(10, 4),
        constrained_layout=True,
    )

    axes[0].plot(
        data["cache_ttl_seconds"],
        data["mean_latency_ms"],
        marker="o",
        linewidth=2,
        color=ARCHITECTURE_COLORS["refined"],
    )
    axes[0].set_title("Latency benefit of trust caching")
    axes[0].set_xlabel("Cache TTL (seconds)")
    axes[0].set_ylabel("Mean latency (ms)")
    axes[0].set_xscale("log")

    axes[1].plot(
        data["cache_ttl_seconds"],
        data["mean_estimated_stale_cache_risk"],
        marker="o",
        linewidth=2,
        color="#DC2626",
    )
    axes[1].set_title("Estimated stale-cache risk")
    axes[1].set_xlabel("Cache TTL (seconds)")
    axes[1].set_ylabel("Estimated stale-cache risk")
    axes[1].set_xscale("log")
    axes[1].set_ylim(0, 0.65)

    figure.savefig(
        FIGURES_DIRECTORY
        / "cache_ttl_tradeoff.png",
        bbox_inches="tight",
    )
    figure.savefig(
        FIGURES_DIRECTORY
        / "cache_ttl_tradeoff.pdf",
        bbox_inches="tight",
    )

    plt.close(figure)

def plot_session_revalidation_sensitivity() -> None:
    """Plot security exposure and revalidation overhead."""

    data = pd.read_csv(
        RESULTS_DIRECTORY
        / "session_revalidation_sensitivity_summary.csv"
    )

    base_rate = (
        data[data["revocations_per_hour"] == 1]
        .sort_values("revalidation_interval_seconds")
    )

    figure, axes = plt.subplots(
        1,
        3,
        figsize=(13, 4),
        constrained_layout=True,
    )

    axes[0].plot(
        base_rate["revalidation_interval_seconds"],
        base_rate["mean_unauthorized_continuation_ms"]
        / 1000.0,
        marker="o",
        linewidth=2,
        color="#DC2626",
    )
    axes[0].set_title("Unauthorized continuation")
    axes[0].set_xlabel("Revalidation interval (seconds)")
    axes[0].set_ylabel("Mean continuation (seconds)")

    axes[1].plot(
        base_rate["revalidation_interval_seconds"],
        base_rate[
            "mean_expected_checks_per_session_hour"
        ],
        marker="o",
        linewidth=2,
        color=ARCHITECTURE_COLORS["refined"],
    )
    axes[1].set_title("Revalidation overhead")
    axes[1].set_xlabel("Revalidation interval (seconds)")
    axes[1].set_ylabel("Expected checks per session-hour")

    for revocation_rate in sorted(
        data["revocations_per_hour"].unique()
    ):
        rate_data = (
            data[
                data["revocations_per_hour"]
                == revocation_rate
            ]
            .sort_values(
                "revalidation_interval_seconds"
            )
        )

        axes[2].plot(
            rate_data[
                "revalidation_interval_seconds"
            ],
            rate_data[
                "mean_estimated_exposure_seconds_per_hour"
            ],
            marker="o",
            linewidth=2,
            label=f"{revocation_rate:g} per hour",
        )

    axes[2].set_title("Estimated exposure")
    axes[2].set_xlabel("Revalidation interval (seconds)")
    axes[2].set_ylabel("Exposure seconds per hour")
    axes[2].legend(title="Revocations")

    figure.savefig(
        FIGURES_DIRECTORY
        / "session_revalidation_tradeoff.png",
        bbox_inches="tight",
    )
    figure.savefig(
        FIGURES_DIRECTORY
        / "session_revalidation_tradeoff.pdf",
        bbox_inches="tight",
    )

    plt.close(figure)

def plot_credential_status_sensitivity() -> None:
    """Plot effects of credential-status service failures."""

    data = pd.read_csv(
        RESULTS_DIRECTORY
        / "credential_status_sensitivity_summary.csv"
    )

    figure, axes = plt.subplots(
        1,
        2,
        figsize=(10, 4),
        constrained_layout=True,
    )

    for architecture in [
        "baseline",
        "capacity_matched",
        "refined",
    ]:
        architecture_data = (
            data[data["architecture"] == architecture]
            .sort_values("status_failure_probability")
        )

        label = ARCHITECTURE_LABELS[architecture]
        color = ARCHITECTURE_COLORS[architecture]

        axes[0].plot(
            architecture_data[
                "status_failure_probability"
            ],
            architecture_data["mean_success_rate"],
            marker="o",
            linewidth=2,
            color=color,
            label=label,
        )

        axes[1].plot(
            architecture_data[
                "status_failure_probability"
            ],
            architecture_data[
                "mean_status_check_failure_rate"
            ],
            marker="o",
            linewidth=2,
            color=color,
            label=label,
        )

    axes[0].set_title("Overall request success")
    axes[0].set_xlabel("Status-service failure probability")
    axes[0].set_ylabel("Mean success rate")
    axes[0].set_ylim(0.85, 1.01)
    axes[0].legend()

    axes[1].set_title("Detected status-check failures")
    axes[1].set_xlabel("Status-service failure probability")
    axes[1].set_ylabel("Mean status-check failure rate")
    axes[1].set_ylim(0, 0.12)
    axes[1].legend()

    figure.savefig(
        FIGURES_DIRECTORY
        / "credential_status_sensitivity.png",
        bbox_inches="tight",
    )
    figure.savefig(
        FIGURES_DIRECTORY
        / "credential_status_sensitivity.pdf",
        bbox_inches="tight",
    )

    plt.close(figure)
def plot_connector_capacity_sensitivity() -> None:
    """Plot latency and connector waiting as capacity changes."""

    data = pd.read_csv(
        RESULTS_DIRECTORY
        / "connector_capacity_sensitivity_summary.csv"
    )

    figure, axes = plt.subplots(
        1,
        2,
        figsize=(10, 4),
        constrained_layout=True,
    )

    for architecture in [
        "baseline",
        "capacity_matched",
        "refined",
    ]:
        architecture_data = (
            data[data["architecture"] == architecture]
            .sort_values("connector_capacity")
        )

        label = ARCHITECTURE_LABELS[architecture]
        color = ARCHITECTURE_COLORS[architecture]

        axes[0].plot(
            architecture_data["connector_capacity"],
            architecture_data["mean_latency_ms"],
            marker="o",
            linewidth=2,
            color=color,
            label=label,
        )

        axes[1].plot(
            architecture_data["connector_capacity"],
            architecture_data[
                "mean_connector_wait_ms"
            ],
            marker="o",
            linewidth=2,
            color=color,
            label=label,
        )

    axes[0].set_title("Latency by connector capacity")
    axes[0].set_xlabel("Connector capacity")
    axes[0].set_ylabel("Mean latency (ms)")
    axes[0].legend()

    axes[1].set_title("Connector queue waiting")
    axes[1].set_xlabel("Connector capacity")
    axes[1].set_ylabel("Mean connector wait (ms)")
    axes[1].legend()

    figure.savefig(
        FIGURES_DIRECTORY
        / "connector_capacity_sensitivity.png",
        bbox_inches="tight",
    )
    figure.savefig(
        FIGURES_DIRECTORY
        / "connector_capacity_sensitivity.pdf",
        bbox_inches="tight",
    )

    plt.close(figure)

def parse_arguments() -> argparse.Namespace:
    """Read result and figure directories from the command line."""

    parser = argparse.ArgumentParser(
        description=(
            "Plot BC-SSI healthcare DES results."
        )
    )

    parser.add_argument(
        "--results-directory",
        default="results",
        help=(
            "Input result directory relative to the "
            "project directory."
        ),
    )

    parser.add_argument(
        "--figures-directory",
        default="figures",
        help=(
            "Output figure directory relative to the "
            "project directory."
        ),
    )

    return parser.parse_args()
def main() -> None:
    """Generate all publication figures."""
    global RESULTS_DIRECTORY
    global FIGURES_DIRECTORY

    arguments = parse_arguments()

    RESULTS_DIRECTORY = (
        ROOT / arguments.results_directory
    )
    FIGURES_DIRECTORY = (
        ROOT / arguments.figures_directory
    )
    FIGURES_DIRECTORY.mkdir(exist_ok=True)
    configure_plot_style()

    plot_architecture_comparison()
    plot_workload_sensitivity()
    plot_trust_failure_sensitivity()
    plot_cache_ttl_sensitivity()
    plot_session_revalidation_sensitivity()
    plot_credential_status_sensitivity()
    plot_connector_capacity_sensitivity()

    print(
        "Created architecture_scenario_comparison.png"
)
    print(
        "Created architecture_scenario_comparison.pdf"
    )
    print("Created workload_sensitivity.png")
    print("Created workload_sensitivity.pdf")
    print("Created trust_failure_sensitivity.png")
    print("Created trust_failure_sensitivity.pdf")
    print("Created cache_ttl_tradeoff.png")
    print("Created cache_ttl_tradeoff.pdf")
    print("Created session_revalidation_tradeoff.png")
    print("Created session_revalidation_tradeoff.pdf")
    print("Created credential_status_sensitivity.png")
    print("Created credential_status_sensitivity.pdf")
    print("Created connector_capacity_sensitivity.png")
    print("Created connector_capacity_sensitivity.pdf")
if __name__ == "__main__":
    main()