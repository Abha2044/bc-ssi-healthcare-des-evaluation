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


def plot_capacity_attribution() -> None:
    """Plot how capacity and architecture contribute to improvement."""

    data = pd.read_csv(
        RESULTS_DIRECTORY / "capacity_attribution_summary.csv"
    )
    data = data.sort_values(
        "latency_percent_from_architecture"
    ).reset_index(drop=True)

    positions = np.arange(len(data))
    capacity_latency = data[
        "latency_percent_from_capacity"
    ].clip(lower=0.0)
    architecture_latency = data[
        "latency_percent_from_architecture"
    ].clip(lower=0.0)

    figure, axes = plt.subplots(
        1,
        2,
        figsize=(14, 7),
        constrained_layout=True,
    )

    axes[0].barh(
        positions,
        capacity_latency,
        color=ARCHITECTURE_COLORS["capacity_matched"],
        label="Added capacity",
    )
    axes[0].barh(
        positions,
        architecture_latency,
        left=capacity_latency,
        color=ARCHITECTURE_COLORS["refined"],
        label="Architectural refinement",
    )
    axes[0].set_yticks(positions)
    axes[0].set_yticklabels(
        [scenario_label(value) for value in data["scenario"]]
    )
    axes[0].set_xlim(0, 100)
    axes[0].set_xlabel("Share of latency improvement (%)")
    axes[0].set_title("Source of latency improvement")
    axes[0].legend(loc="lower right")

    for index, (capacity, architecture) in enumerate(
        zip(capacity_latency, architecture_latency)
    ):
        if capacity >= 8:
            axes[0].text(
                capacity / 2,
                index,
                f"{capacity:.0f}%",
                ha="center",
                va="center",
                color="white",
                fontsize=8,
            )
        if architecture >= 8:
            axes[0].text(
                capacity + architecture / 2,
                index,
                f"{architecture:.0f}%",
                ha="center",
                va="center",
                color="white",
                fontsize=8,
            )

    capacity_success = data["success_from_capacity"]
    architecture_success = data[
        "success_from_architecture"
    ]
    capacity_error = np.vstack(
        [
            capacity_success
            - data["success_from_capacity_ci95_low"],
            data["success_from_capacity_ci95_high"]
            - capacity_success,
        ]
    ).clip(min=0.0)
    architecture_error = np.vstack(
        [
            architecture_success
            - data["success_from_architecture_ci95_low"],
            data["success_from_architecture_ci95_high"]
            - architecture_success,
        ]
    ).clip(min=0.0)

    bar_height = 0.34
    axes[1].barh(
        positions - bar_height / 2,
        capacity_success,
        height=bar_height,
        xerr=capacity_error,
        color=ARCHITECTURE_COLORS["capacity_matched"],
        label="Added capacity",
        capsize=2,
    )
    axes[1].barh(
        positions + bar_height / 2,
        architecture_success,
        height=bar_height,
        xerr=architecture_error,
        color=ARCHITECTURE_COLORS["refined"],
        label="Architectural refinement",
        capsize=2,
    )
    axes[1].set_yticks(positions)
    axes[1].set_yticklabels([])
    axes[1].set_xlabel("Absolute improvement in success rate")
    axes[1].set_title("Source of success-rate improvement")
    axes[1].axvline(0, color="black", linewidth=0.8)
    axes[1].legend(loc="lower right")

    figure.savefig(
        FIGURES_DIRECTORY / "capacity_attribution.png",
        bbox_inches="tight",
    )
    figure.savefig(
        FIGURES_DIRECTORY / "capacity_attribution.pdf",
        bbox_inches="tight",
    )

    plt.close(figure)


def plot_resource_saturation() -> None:
    """Plot mean utilization and identify saturated resources."""

    data = pd.read_csv(
        RESULTS_DIRECTORY / "resource_saturation_summary.csv"
    )

    architectures = [
        "baseline",
        "capacity_matched",
        "refined",
    ]
    scenarios = sorted(data["scenario"].unique())
    resources = (
        data.groupby("resource")["mean_utilization"]
        .max()
        .sort_values(ascending=False)
        .index.tolist()
    )

    figure, axes = plt.subplots(
        1,
        3,
        figsize=(19, 8),
        sharey=True,
        constrained_layout=True,
    )

    image = None

    for index, architecture in enumerate(architectures):
        architecture_data = data[
            data["architecture"] == architecture
        ]
        utilization = (
            architecture_data.pivot(
                index="resource",
                columns="scenario",
                values="mean_utilization",
            )
            .reindex(index=resources, columns=scenarios)
        )
        saturation = (
            architecture_data.pivot(
                index="resource",
                columns="scenario",
                values="saturation_rate",
            )
            .reindex(index=resources, columns=scenarios)
            .fillna(0.0)
        )

        image = axes[index].imshow(
            utilization.to_numpy(dtype=float),
            aspect="auto",
            vmin=0.0,
            vmax=1.0,
            cmap="YlOrRd",
        )
        axes[index].set_title(
            ARCHITECTURE_LABELS[architecture]
        )
        axes[index].set_xticks(np.arange(len(scenarios)))
        axes[index].set_xticklabels(
            [scenario_label(value) for value in scenarios],
            rotation=55,
            ha="right",
            fontsize=8,
        )
        axes[index].set_yticks(np.arange(len(resources)))

        if index == 0:
            axes[index].set_yticklabels(
                [scenario_label(value) for value in resources]
            )
        else:
            axes[index].tick_params(labelleft=False)

        for row_index in range(len(resources)):
            for column_index in range(len(scenarios)):
                if saturation.iloc[row_index, column_index] > 0:
                    axes[index].text(
                        column_index,
                        row_index,
                        "S",
                        ha="center",
                        va="center",
                        color="black",
                        fontweight="bold",
                    )

    colorbar = figure.colorbar(
        image,
        ax=axes,
        shrink=0.78,
        pad=0.02,
    )
    colorbar.set_label("Mean resource utilization")
    figure.suptitle(
        "Resource utilization by architecture and scenario\n"
        "S marks combinations saturated in at least one replication"
    )

    figure.savefig(
        FIGURES_DIRECTORY / "resource_saturation.png",
        bbox_inches="tight",
    )
    figure.savefig(
        FIGURES_DIRECTORY / "resource_saturation.pdf",
        bbox_inches="tight",
    )

    plt.close(figure)


def plot_mixed_workload_stability() -> None:
    """Plot utilization and saturation under shared mixed workloads."""

    data = pd.read_csv(
        RESULTS_DIRECTORY
        / "mixed_workload_resource_summary.csv"
    )
    stability = (
        data.groupby(
            ["workload_multiplier", "architecture"],
            as_index=False,
        )
        .agg(
            peak_mean_utilization=(
                "mean_utilization",
                "max",
            ),
            replication_saturation_rate=(
                "replication_saturation_rate",
                "max",
            ),
        )
    )

    multipliers = sorted(
        stability["workload_multiplier"].unique()
    )
    architectures = [
        "baseline",
        "capacity_matched",
        "refined",
    ]

    figure, axes = plt.subplots(
        1,
        2,
        figsize=(11, 4.5),
        constrained_layout=True,
    )

    for architecture in architectures:
        architecture_data = (
            stability[
                stability["architecture"] == architecture
            ]
            .sort_values("workload_multiplier")
        )
        axes[0].plot(
            architecture_data["workload_multiplier"],
            architecture_data["peak_mean_utilization"],
            marker="o",
            linewidth=2,
            color=ARCHITECTURE_COLORS[architecture],
            label=ARCHITECTURE_LABELS[architecture],
        )

    axes[0].axhline(
        0.95,
        color="#B91C1C",
        linestyle="--",
        linewidth=1.3,
        label="95% saturation threshold",
    )
    axes[0].set_xticks(multipliers)
    axes[0].set_ylim(0, 1.05)
    axes[0].set_xlabel("Mixed-workload multiplier")
    axes[0].set_ylabel("Peak mean resource utilization")
    axes[0].set_title("Shared-resource utilization")
    axes[0].legend()

    positions = np.arange(len(multipliers))
    bar_width = 0.24

    for index, architecture in enumerate(architectures):
        architecture_data = (
            stability[
                stability["architecture"] == architecture
            ]
            .set_index("workload_multiplier")
            .reindex(multipliers)
        )
        axes[1].bar(
            positions + (index - 1) * bar_width,
            architecture_data[
                "replication_saturation_rate"
            ],
            width=bar_width,
            color=ARCHITECTURE_COLORS[architecture],
            label=ARCHITECTURE_LABELS[architecture],
        )

    axes[1].set_xticks(positions)
    axes[1].set_xticklabels(multipliers)
    axes[1].set_ylim(0, 1.05)
    axes[1].set_xlabel("Mixed-workload multiplier")
    axes[1].set_ylabel("Fraction of replications saturated")
    axes[1].set_title("Stability across replications")
    axes[1].legend()

    figure.savefig(
        FIGURES_DIRECTORY / "mixed_workload_stability.png",
        bbox_inches="tight",
    )
    figure.savefig(
        FIGURES_DIRECTORY / "mixed_workload_stability.pdf",
        bbox_inches="tight",
    )

    plt.close(figure)


def plot_atam_gap_tracking() -> None:
    """Plot runtime ATAM-gap encounter rates by scenario."""

    data = pd.read_csv(
        RESULTS_DIRECTORY / "gap_tracking_summary.csv"
    )
    architectures = [
        "baseline",
        "capacity_matched",
        "refined",
    ]
    scenarios = sorted(data["scenario"].unique())
    gaps = [f"G{index}" for index in range(1, 14)]

    figure, axes = plt.subplots(
        1,
        3,
        figsize=(19, 7),
        sharey=True,
        constrained_layout=True,
    )
    image = None

    for index, architecture in enumerate(architectures):
        architecture_data = data[
            data["architecture"] == architecture
        ]
        matrix = (
            architecture_data.pivot(
                index="scenario",
                columns="gap",
                values="mean_gap_encounter_rate",
            )
            .reindex(index=scenarios, columns=gaps)
            .fillna(0.0)
        )

        image = axes[index].imshow(
            matrix.to_numpy(dtype=float),
            aspect="auto",
            vmin=0.0,
            vmax=1.0,
            cmap="Blues",
        )
        axes[index].set_title(
            ARCHITECTURE_LABELS[architecture]
        )
        axes[index].set_xticks(np.arange(len(gaps)))
        axes[index].set_xticklabels(
            ["G4*" if gap == "G4" else gap for gap in gaps],
            rotation=45,
            ha="right",
        )
        axes[index].set_yticks(np.arange(len(scenarios)))

        if index == 0:
            axes[index].set_yticklabels(
                [scenario_label(value) for value in scenarios]
            )
        else:
            axes[index].tick_params(labelleft=False)

    colorbar = figure.colorbar(
        image,
        ax=axes,
        shrink=0.78,
        pad=0.02,
    )
    colorbar.set_label("Mean request gap-encounter rate")
    figure.suptitle(
        "Runtime ATAM-gap tracking by architecture and scenario\n"
        "G4* is only partially modelled and is not counted as "
        "runtime evidence"
    )

    figure.savefig(
        FIGURES_DIRECTORY / "atam_gap_tracking.png",
        bbox_inches="tight",
    )
    figure.savefig(
        FIGURES_DIRECTORY / "atam_gap_tracking.pdf",
        bbox_inches="tight",
    )

    plt.close(figure)

def plot_ablation_comparison() -> None:
    """Plot overall ablation outcomes with 95% confidence intervals."""

    data = pd.read_csv(
        RESULTS_DIRECTORY
        / "ablation_overall_confidence_intervals.csv"
    ).sort_values("mean_latency_ms")

    labels = [
        variant.replace("_", " ")
        for variant in data["variant"]
    ]

    colors = [
        "#4C72B0" if variant == "baseline"
        else "#55A868" if variant == "full_refined"
        else "#999999"
        for variant in data["variant"]
    ]

    latency_error = np.vstack([
        data["mean_latency_ms"]
        - data["latency_ci95_low_ms"],
        data["latency_ci95_high_ms"]
        - data["mean_latency_ms"],
    ])

    success_error = np.vstack([
        data["mean_success_rate"]
        - data["success_rate_ci95_low"],
        data["success_rate_ci95_high"]
        - data["mean_success_rate"],
    ])

    figure, axes = plt.subplots(
        1,
        2,
        figsize=(14, 7),
        constrained_layout=True,
    )

    axes[0].barh(
        labels,
        data["mean_latency_ms"],
        xerr=latency_error,
        color=colors,
        capsize=3,
    )
    axes[0].invert_yaxis()
    axes[0].set_title("Latency by refinement package")
    axes[0].set_xlabel("Mean latency (ms)")

    axes[1].barh(
        labels,
        data["mean_success_rate"],
        xerr=success_error,
        color=colors,
        capsize=3,
    )
    axes[1].invert_yaxis()
    axes[1].set_title("Success rate by refinement package")
    axes[1].set_xlabel("Mean success rate")
    axes[1].set_xlim(
        max(
            0.0,
            float(data["success_rate_ci95_low"].min()) - 0.02,
        ),
        1.0,
    )

    figure.suptitle(
        "Ablation results across ten scenarios",
        fontsize=15,
    )
    figure.supxlabel(
        "Equal scenario weights; error bars show 95% "
        "Student-t confidence intervals",
        fontsize=9,
    )

    for extension in ("png", "pdf"):
        figure.savefig(
            FIGURES_DIRECTORY
            / f"ablation_comparison.{extension}",
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
    plot_capacity_attribution()
    plot_resource_saturation()
    plot_mixed_workload_stability()
    plot_ablation_comparison()
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
    print("Created capacity_attribution.png")
    print("Created capacity_attribution.pdf")
    print("Created resource_saturation.png")
    print("Created resource_saturation.pdf")
    print("Created mixed_workload_stability.png")
    print("Created mixed_workload_stability.pdf")
    print("Created atam_gap_tracking.png")
    print("Created atam_gap_tracking.pdf")
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
