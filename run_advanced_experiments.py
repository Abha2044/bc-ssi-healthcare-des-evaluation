"""Discrete-event evaluation of the BC-SSI healthcare architecture."""
from __future__ import annotations
import json
import math
import random
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import asdict, dataclass


MS = 1000.0


@dataclass
class RequestContext:
    """State accumulated while processing one request."""

    trust_lookups: int = 0
    retry_attempts: int = 0


@dataclass
class RequestResult:
    """Result produced for one simulated request."""

    request_id: int
    replication: int
    scenario: str
    start_time_s: float
    end_time_s: float
    latency_ms: float
    success: bool
    failure_reason: str
    trust_lookups: int


class ResourcePool:
    """A simple multi-server queue used by the simulation."""

    def __init__(self, name: str, capacity: int, warmup_s: float = 0.0):
        self.name = name
        self.capacity = max(1, int(capacity))
        self.warmup_s = float(warmup_s)
        self.next_available = [0.0 for _ in range(self.capacity)]
        self.busy_time = 0.0
        self.wait_time = 0.0
        self.calls = 0
        self.max_wait = 0.0

    def process(
        self,
        now: float,
        service_time_s: float,
    ) -> Tuple[float, float]:
        """Process one request and return its finish time and waiting time."""

        server_index = min(
            range(self.capacity),
            key=lambda index: self.next_available[index],
        )

        start = max(now, self.next_available[server_index])
        wait = max(0.0, start - now)
        finish = start + max(0.0, service_time_s)

        self.next_available[server_index] = finish

        if start >= self.warmup_s:
            self.busy_time += max(0.0, service_time_s)
            self.wait_time += wait
            self.max_wait = max(self.max_wait, wait)
            self.calls += 1

        return finish, wait

    def stats(self, horizon_s: float) -> Dict[str, float]:
        """Return utilization and queue statistics."""

        measured_duration = max(horizon_s - self.warmup_s, 1e-9)

        utilization = self.busy_time / (
            measured_duration * self.capacity
        )

        average_wait_ms = (
            self.wait_time / self.calls * MS
            if self.calls
            else 0.0
        )

        return {
            "calls": self.calls,
            "utilization": utilization,
            "average_wait_ms": average_wait_ms,
            "maximum_wait_ms": self.max_wait * MS,
        }

class SimulationEngine:
    """Runs the initial baseline emergency-access simulation."""

    def __init__(self, config: Dict, replication: int):
        self.replication = replication
        self.config = config
        self.simulation = config["simulation"]
        self.parameters = config["baseline"]

        base_seed = int(
            self.simulation.get("random_seed", 42)
        )

        self.random = random.Random(
            base_seed + 10000 * replication
        )

        self.duration_s = float(
            self.simulation["duration_seconds"]
        )

        self.warmup_s = float(
            self.simulation.get("warmup_seconds", 0.0)
        )

        self.resources = {
            "verifier": ResourcePool(
                name="verifier",
                capacity=self.parameters["verifier_capacity"],
                warmup_s=self.warmup_s,
            ),
            "trust": ResourcePool(
                name="trust",
                capacity=self.parameters["trust_service_capacity"],
                warmup_s=self.warmup_s,
            ),
        }

    def    service_time_s(
        self,
        mean_ms: float,
        std_ms: float | None = None,
    ) -> float:
        """Generate a positive lognormal service time."""

        if std_ms is None:
            std_ms = max(mean_ms * 0.15, 1.0)

        mean_ms = max(mean_ms, 1e-6)
        variance = std_ms**2

        sigma_squared = math.log(
            1.0 + variance / mean_ms**2
        )

        mu = math.log(mean_ms) - 0.5 * sigma_squared
        sigma = math.sqrt(sigma_squared)

        sampled_ms = self.random.lognormvariate(mu, sigma)

        return max(1.0, sampled_ms) / MS

    def resource_step(
        self,
        now: float,
        resource_name: str,
        mean_ms: float,
        std_ms: float | None = None,
    ) -> float:
        """Process one architectural service step."""

        service_time = self.service_time_s(mean_ms, std_ms)

        finish, _ = self.resources[resource_name].process(
            now,
            service_time,
        )

        return finish

    def generate_arrivals(self, rate: float) -> List[float]:
        """Generate request arrivals using a Poisson process."""

        arrivals = []
        current_time = 0.0

        while current_time < self.duration_s:
            current_time += self.random.expovariate(rate)

            if current_time < self.duration_s:
                arrivals.append(current_time)

        return arrivals

    def run_emergency_request(
        self,
        request_id: int,
        arrival_time: float,
    ) -> RequestResult:
        """Process one emergency-access request."""

        context = RequestContext()
        now = arrival_time

        now = self.resource_step(
            now,
            "verifier",
            self.parameters["credential_verification_mean_ms"],
        )

        now = self.resource_step(
            now,
            "verifier",
            self.parameters["did_resolution_mean_ms"],
        )

        context.trust_lookups += 1

        now = self.resource_step(
            now,
            "trust",
            self.parameters["trust_lookup_mean_ms"],
            self.parameters["trust_lookup_std_ms"],
        )

        trust_failed = (
            self.random.random()
            < self.parameters["trust_failure_probability"]
        )

        return RequestResult(
        request_id=request_id,
        replication=self.replication,
        scenario="emergency_access",
        start_time_s=arrival_time,
        end_time_s=now,
        latency_ms=(now - arrival_time) * MS,
        success=not trust_failed,
        failure_reason=(
        "trust_resolution_failure"
        if trust_failed
        else ""
    ),
    trust_lookups=context.trust_lookups,
)

    def run(self) -> List[RequestResult]:
        """Run the baseline emergency-access scenario."""

        rate = self.simulation[
            "arrival_rate_per_second"
        ]["emergency_access"]

        arrivals = self.generate_arrivals(rate)
        results = []

        for request_id, arrival_time in enumerate(arrivals, start=1):
            result = self.run_emergency_request(
                request_id,
                arrival_time,
            )

            if arrival_time >= self.warmup_s:
                results.append(result)

        return results

def main() -> None:
    """Run repeated baseline simulations and save the results."""

    root = Path(__file__).resolve().parent
    config_path = root / "config_baseline.json"

    config = json.loads(
        config_path.read_text(encoding="utf-8")
    )

    replication_count = int(
        config["simulation"]["replications"]
    )

    all_results = []

    for replication in range(replication_count):
        engine = SimulationEngine(config, replication)
        replication_results = engine.run()
        all_results.extend(replication_results)

        successful = sum(
            result.success
            for result in replication_results
        )

        print(
            f"Replication {replication + 1}: "
            f"{len(replication_results)} requests, "
            f"{successful} successful"
        )

    detail = pd.DataFrame(
        asdict(result)
        for result in all_results
    )

    summary = (
        detail.groupby("replication", as_index=False)
        .agg(
            total_requests=("request_id", "count"),
            success_rate=("success", "mean"),
            average_latency_ms=("latency_ms", "mean"),
            median_latency_ms=("latency_ms", "median"),
        )
    )

    output_directory = root / "results"
    output_directory.mkdir(exist_ok=True)

    detail.to_csv(
        output_directory / "baseline_detail.csv",
        index=False,
    )

    summary.to_csv(
        output_directory / "baseline_by_replication.csv",
        index=False,
    )

    print("\nBaseline simulation completed.")
    print(summary.to_string(index=False))
    print("\nResults saved in the results directory.")


if __name__ == "__main__":
    main()