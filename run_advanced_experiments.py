"""Discrete-event evaluation of the BC-SSI healthcare architecture."""

from __future__ import annotations

import json
import math
import random
import pandas as pd
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Tuple




MS = 1000.0


@dataclass
class RequestContext:
    """State accumulated while processing one request."""

    trust_lookups: int = 0
    cache_hits: int = 0
    retry_attempts: int = 0
    fallback_used: int = 0
    circuit_opened: int = 0
    status_checks: int = 0
    obligations:  int = 0
    minimisation:int = 0
    compliance:int = 0

@dataclass
class RequestResult:
    """Result produced for one simulated request."""

    request_id: int
    replication: int
    architecture: str
    scenario: str
    start_time_s: float
    end_time_s: float
    latency_ms: float
    success: bool
    failure_reason: str
    trust_lookups: int
    trust_cache_hit: int
    status_check_used: int
    obligations_executed: int
    retry_attempts: int
    fallback_used: int
    circuit_opened: int
    minimisation_applied: int
    compliance_recorded: int

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

    def __init__(
        self,
        config: Dict,
        architecture: str,
        replication: int,
    ):
        self.config = config
        self.architecture = architecture
        self.replication = replication
        self.simulation = config["simulation"]
        self.parameters = config[architecture]

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
            "status": ResourcePool(
                name="status",
                capacity=self.parameters["status_service_capacity"],
                warmup_s=self.warmup_s,
            ),
            "trust": ResourcePool(
                name="trust",
                capacity=self.parameters["trust_service_capacity"],
                warmup_s=self.warmup_s,
            ),
            "policy": ResourcePool(
                name="policy",
                capacity=self.parameters["policy_engine_capacity"],
                warmup_s=self.warmup_s,
            ),
            "compliance": ResourcePool(
                name="compliance",
                capacity=self.parameters["compliance_service_capacity"],
                warmup_s=self.warmup_s,
            ),
        }

    def service_time_s(
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

    def trust_lookup(
        self,
        now: float,
        context: RequestContext,
    ) -> Tuple[float, bool]:
        """Resolve trust using cache, retries and bounded fallback."""

        context.trust_lookups += 1

        cache_enabled = self.parameters.get(
            "trust_cache_enabled",
            False,
        )

        cache_hit_probability = self.parameters.get(
            "trust_cache_hit_probability",
            0.0,
        )

        if (
            cache_enabled
            and self.random.random() < cache_hit_probability
        ):
            context.cache_hits += 1

            cache_delay = self.service_time_s(
                self.parameters["cached_trust_lookup_mean_ms"],
                self.parameters["cached_trust_lookup_std_ms"],
            )

            return now + cache_delay, False

        maximum_attempts = max(
            1,
            int(self.parameters.get("max_retry_attempts", 1)),
        )

        trust_failed = True

        for attempt in range(maximum_attempts):
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

            if not trust_failed:
                return now, False

            if attempt < maximum_attempts - 1:
                context.retry_attempts += 1

                backoff_ms = (
                    self.parameters["retry_backoff_base_ms"]
                    * (2**attempt)
                )

                now += backoff_ms / MS

        if self.parameters.get("fallback_trust_enabled", False):
            context.fallback_used = 1

            fallback_delay = self.service_time_s(
                self.parameters["cached_trust_lookup_mean_ms"] * 1.5,
                self.parameters["cached_trust_lookup_std_ms"],
            )

            now += fallback_delay

            if self.parameters.get(
                "circuit_breaker_enabled",
                False,
            ):
                context.circuit_opened = 1

            return now, False

        now += self.parameters.get("trust_timeout_ms", 5000) / MS

        return now, True

    def credential_status_check(
        self,
        now: float,
        context: RequestContext,
    ) -> Tuple[float, bool]:
        """Check whether the verified credential remains valid."""

        if not self.parameters.get(
            "explicit_status_check_enabled",
            False,
        ):
            return now, False

        context.status_checks += 1

        now = self.resource_step(
            now,
            "status",
            self.parameters["credential_status_mean_ms"],
        )

        failed = (
            self.random.random()
            < self.parameters[
                "credential_status_failure_probability"
            ]
        )

        return now, failed

    def policy_and_obligation_handling(
        self,
        now: float,
        context: RequestContext,
    ) -> float:
        """Evaluate policy and execute obligations when supported."""

        now = self.resource_step(
            now,
            "policy",
            self.parameters["policy_evaluation_mean_ms"],
        )

        if not self.parameters.get(
            "obligation_handling_enabled",
            False,
        ):
            return now

        context.obligations += 1

        now = self.resource_step(
            now,
            "policy",
            self.parameters["obligation_handling_mean_ms"],
        )

        return now
    def data_minimisation(
        self,
        now: float,
        context: RequestContext,
    ) -> float:
        """Apply data minimization when the architecture supports it."""

        if not self.parameters.get(
            "data_minimization_enabled",
            False,
        ):
            return now

        context.minimisation += 1

        processing_time = self.service_time_s(
            self.parameters["data_minimization_mean_ms"]
        )

        return now + processing_time

    def compliance_recording(
        self,
        now: float,
        context: RequestContext,
    ) -> float:
        """Record the compliance event when the component is available."""

        required = self.parameters.get(
            "compliance_required",
            False,
        )

        if not required:
            deployment_probability = self.parameters.get(
                "compliance_optional_deployment_probability",
                0.5,
            )

            if self.random.random() >= deployment_probability:
                return now

        context.compliance += 1

        now = self.resource_step(
            now,
            "compliance",
            self.parameters["compliance_recording_mean_ms"],
        )

        return now

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

        now, trust_failed = self.trust_lookup(
            now,
            context,
        )

        status_failed = False

        if not trust_failed:
            now, status_failed = self.credential_status_check(
                now,
                context,
            )

        request_failed = trust_failed or status_failed

        if not request_failed:
            now = self.policy_and_obligation_handling(
                now,
                context,
             )
            now = self.data_minimisation(
                now,
                context,
            )

            now = self.compliance_recording(
                now,
                context,
            )
        
        if trust_failed:
            failure_reason = "trust_resolution_failure"
        elif status_failed:
            failure_reason = "credential_status_failure"
        else:
            failure_reason = ""

        return RequestResult(
            request_id=request_id,
            replication=self.replication,
            architecture=self.architecture,
            scenario="emergency_access",
            start_time_s=arrival_time,
            end_time_s=now,
            latency_ms=(now - arrival_time) * MS,
            success=not request_failed,
            failure_reason=failure_reason,
            trust_lookups=context.trust_lookups,
            trust_cache_hit=context.cache_hits,
            status_check_used=context.status_checks,
            obligations_executed=context.obligations,
            minimisation_applied=context.minimisation,
            compliance_recorded=context.compliance,
            retry_attempts=context.retry_attempts,
            fallback_used=context.fallback_used, 
            circuit_opened=context.circuit_opened,
            
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
    """Compare baseline and refined architecture simulations."""

    root = Path(__file__).resolve().parent
    config_path = root / "config_advanced.json"

    config = json.loads(
        config_path.read_text(encoding="utf-8")
    )

    replication_count = int(
        config["simulation"]["replications"]
    )

    all_results = []

    for architecture in ["baseline", "refined"]:
        for replication in range(replication_count):
            engine = SimulationEngine(
                config,
                architecture,
                replication,
            )

            replication_results = engine.run()
            all_results.extend(replication_results)

            successful = sum(
                result.success
                for result in replication_results
            )

            print(
                f"{architecture}, replication {replication + 1}: "
                f"{len(replication_results)} requests, "
                f"{successful} successful"
            )

    detail = pd.DataFrame(
        asdict(result)
        for result in all_results
    )

    summary = (
        detail.groupby(
            ["architecture", "replication"],
            as_index=False,
        )
        .agg(
            total_requests=("request_id", "count"),
            success_rate=("success", "mean"),
            average_latency_ms=("latency_ms", "mean"),
            median_latency_ms=("latency_ms", "median"),
            cache_hit_rate=("trust_cache_hit", "mean"),
            status_check_rate=("status_check_used", "mean"),
            average_retry_attempts=("retry_attempts", "mean"),
            fallback_rate=("fallback_used", "mean"),
            circuit_open_rate=("circuit_opened", "mean"),
            obligation_execution_rate=(
                "obligations_executed",
                "mean",
            ),
            minimisation_rate=("minimisation_applied", "mean"),
            compliance_recording_rate=("compliance_recorded", "mean"),
        )
    )

    output_directory = root / "results"
    output_directory.mkdir(exist_ok=True)

    detail.to_csv(
        output_directory / "baseline_refined_detail.csv",
        index=False,
    )

    summary.to_csv(
        output_directory / "baseline_refined_by_replication.csv",
        index=False,
    )

    overall = (
        summary.groupby("architecture", as_index=False)
        .agg(
            mean_success_rate=("success_rate", "mean"),
            mean_latency_ms=("average_latency_ms", "mean"),
            mean_cache_hit_rate=("cache_hit_rate", "mean"),
            mean_status_check_rate=("status_check_rate", "mean"),
            mean_retry_attempts=("average_retry_attempts", "mean"),
            mean_fallback_rate=("fallback_rate", "mean"),
            mean_circuit_open_rate=("circuit_open_rate", "mean"),
            mean_obligation_execution_rate=(
                "obligation_execution_rate",
                "mean",
            ),
            mean_minimisation_rate=(
                "minimisation_rate",
                "mean",
            ),
            mean_compliance_recording_rate=(
                "compliance_recording_rate",
                "mean",
            ),
        )
    )

    print("\nBaseline-versus-refined comparison")
    print(overall.to_string(index=False))
    print("\nResults saved in the results directory.")


if __name__ == "__main__":
    main()
