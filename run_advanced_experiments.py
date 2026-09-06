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
    audit_logs: int = 0
    audit_tags: int = 0
    anonymization: int = 0
    revocation_propagation_ms: float = 0.0
    unauthorized_continuation_ms: float = 0.0

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
    audit_logged: int                               
    audit_tagged: int
    revocation_propagation_ms: float = 0.0
    unauthorized_continuation_ms: float = 0.0
    anonymization_applied: int = 0
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
            "anonymizer": ResourcePool(
                name="anonymizer",
                capacity=self.parameters[
                    "anonymizer_capacity"
                ],
                warmup_s=self.warmup_s,
            ),
            "audit": ResourcePool(
                name="audit",
                capacity=self.parameters["audit_service_capacity"],
                warmup_s=self.warmup_s,
            ),
            "connector": ResourcePool(
                name="connector",
                capacity=self.parameters["connector_capacity"],
                warmup_s=self.warmup_s,
            ),
            "fhir": ResourcePool(
                name="fhir",
                capacity=self.parameters["fhir_service_capacity"],
                warmup_s=self.warmup_s,
            ),
                        "queue": ResourcePool(
                name="queue",
                capacity=self.parameters["queue_capacity"],
                warmup_s=self.warmup_s,
            ),
            "orchestrator": ResourcePool(
                name="orchestrator",
                capacity=self.parameters["orchestrator_capacity"],
                warmup_s=self.warmup_s,
            ),
            "session": ResourcePool(
                name="session",
                capacity=self.parameters["session_service_capacity"],
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
        forced_failure: bool = False,
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

            failure_probability = (
                self.parameters.get(
                    "forced_trust_failure_probability",
                    self.parameters["trust_failure_probability"],
                )
                if forced_failure
                else self.parameters["trust_failure_probability"]
            )

            trust_failed = (
                self.random.random() < failure_probability
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

    def revocation_handling(
        self,
        now: float,
        context: RequestContext,
    ) -> Tuple[float, bool]:
        """Propagate consent revocation to an active session."""

        now = self.resource_step(
            now,
            "status",
            self.parameters["revocation_check_mean_ms"],
        )

        if self.parameters.get(
            "session_manager_enabled",
            False,
        ):
            session_start = now

            now = self.resource_step(
                now,
                "session",
                self.parameters["session_sync_mean_ms"],
            )

            context.revocation_propagation_ms = (
                now - session_start
            ) * MS

            interval_seconds = float(
                self.parameters[
                    "session_revalidation_interval_seconds"
                ]
            )

            context.unauthorized_continuation_ms = (
                interval_seconds / 2.0 * MS
                + context.revocation_propagation_ms
            )
        else:
            processing_time = self.service_time_s(
                self.parameters["session_sync_mean_ms"]
            )

            now += processing_time

            context.revocation_propagation_ms = (
                processing_time * MS
            )

            mean_wait_seconds = float(
                self.parameters[
                    "unbounded_next_request_mean_seconds"
                ]
            )

            next_request_wait = self.random.expovariate(
                1.0 / mean_wait_seconds
            )

            context.unauthorized_continuation_ms = (
                next_request_wait * MS
                + context.revocation_propagation_ms
            )

        propagation_failed = (
            self.random.random()
            < self.parameters[
                "revocation_delay_failure_probability"
            ]
        )

        return now, propagation_failed
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

    def anonymization_processing(
        self,
        now: float,
        context: RequestContext,
    ) -> float:
        """Anonymize health data before research donation."""

        if not self.parameters.get(
            "anonymization_enabled",
            False,
        ):
            return now

        context.anonymization = 1

        return self.resource_step(
            now,
            "anonymizer",
            self.parameters["anonymization_mean_ms"],
        )
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

    def audit_logging(
        self,
        now: float,
        context: RequestContext,
    ) -> float:
        """Write an audit event and apply structured tagging when supported."""

        now = self.resource_step(
            now,
            "audit",
            self.parameters["audit_logging_mean_ms"],
        )

        context.audit_logs += 1

        if self.parameters.get(
            "audit_tagging_enabled",
            False,
        ):
            context.audit_tags += 1

        return now

    def connector_processing(
        self,
        now: float,
    ) -> Tuple[float, bool]:
        """Process a cross-layer request and apply connector failover."""

        if not self.parameters.get("connector_full_in_access", False):
            degraded_delay = self.service_time_s(
                self.parameters["connector_processing_mean_ms"] * 0.4
            )
            now += degraded_delay

        now = self.resource_step(
            now,
            "connector",
            self.parameters["connector_processing_mean_ms"],
        )

        connector_failed = (
            self.random.random()
            < self.parameters["connector_failure_probability"]
        )

        if not connector_failed:
            return now, False

        if self.parameters.get("connector_redundancy_enabled", False):
            failover_delay = self.service_time_s(
                self.parameters["connector_processing_mean_ms"] * 0.5
            )
            return now + failover_delay, False

        if not self.parameters.get("circuit_breaker_enabled", False):
            now += self.parameters.get("connector_timeout_ms", 3000) / MS

        return now, True

    def fhir_processing(self, now: float) -> float:
        """Validate and exchange a FHIR resource."""

        now = self.resource_step(
            now,
            "fhir",
            self.parameters["fhir_validation_mean_ms"],
        )

        if not self.parameters.get("fhir_complete_in_integration", False):
            now += self.parameters.get("fhir_cross_layer_penalty_ms", 0) / MS

        return self.resource_step(
            now,
            "fhir",
            self.parameters["fhir_exchange_mean_ms"],
        )

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
            now = self.audit_logging(
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
            audit_logged=context.audit_logs,
            audit_tagged=context.audit_tags,
            
        )

    def process_audit_investigation(
        self,
        request_id: int,
        arrival_time: float,
    ) -> RequestResult:
        """Reconstruct an audit trail for an investigation."""

        context = RequestContext()
        now = arrival_time

        now = self.resource_step(
            now,
            "audit",
            self.parameters["audit_reconstruction_mean_ms"],
        )

        reconstruction_failed = (
            self.random.random()
            < self.parameters[
                "audit_reconstruction_failure_probability"
            ]
        )

        if self.parameters.get("audit_tagging_enabled", False):
            context.audit_tags = 1

        return RequestResult(
            request_id=request_id,
            replication=self.replication,
            architecture=self.architecture,
            scenario="audit_investigation",
            start_time_s=arrival_time,
            end_time_s=now,
            latency_ms=(now - arrival_time) * MS,
            success=not reconstruction_failed,
            failure_reason=(
                "audit_reconstruction_failure"
                if reconstruction_failed
                else ""
            ),
            trust_lookups=0,
            trust_cache_hit=0,
            status_check_used=0,
            obligations_executed=0,
            minimisation_applied=0,
            compliance_recorded=0,
            audit_logged=0,
            audit_tagged=context.audit_tags,
            retry_attempts=0,
            fallback_used=0,
            circuit_opened=0,
        )

    def process_cross_org_exchange(
        self,
        request_id: int,
        arrival_time: float,
    ) -> RequestResult:
        """Exchange a verified FHIR resource across organizations."""

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

        now, trust_failed = self.trust_lookup(now, context)
        connector_failed = False
        status_failed = False

        if not trust_failed:
            now, connector_failed = self.connector_processing(now)

        if not trust_failed and not connector_failed:
            now, status_failed = self.credential_status_check(now, context)

        request_failed = trust_failed or connector_failed or status_failed

        if not request_failed:
            now = self.policy_and_obligation_handling(now, context)
            now = self.data_minimisation(now, context)
            now = self.fhir_processing(now)
            now = self.compliance_recording(now, context)
            now = self.audit_logging(now, context)

        if trust_failed:
            failure_reason = "trust_resolution_failure"
        elif connector_failed:
            failure_reason = "connector_failure"
        elif status_failed:
            failure_reason = "credential_status_failure"
        else:
            failure_reason = ""

        return RequestResult(
            request_id=request_id,
            replication=self.replication,
            architecture=self.architecture,
            scenario="cross_org_exchange",
            start_time_s=arrival_time,
            end_time_s=now,
            latency_ms=(now - arrival_time) * MS,
            success=not request_failed,
            failure_reason=failure_reason,
            trust_lookups=context.trust_lookups,
            trust_cache_hit=context.cache_hits,
            status_check_used=context.status_checks,
            obligations_executed=context.obligations,
            retry_attempts=context.retry_attempts,
            fallback_used=context.fallback_used,
            circuit_opened=context.circuit_opened,
            minimisation_applied=context.minimisation,
            compliance_recorded=context.compliance,
            audit_logged=context.audit_logs,
            audit_tagged=context.audit_tags,
        )
    def process_high_volume_ingestion(
        self,
        request_id: int,
        arrival_time: float,
    ) -> RequestResult:
        """Process one high-volume clinical-data ingestion request."""

        context = RequestContext()
        now = arrival_time

        now = self.resource_step(
            now,
            "queue",
            self.parameters["queue_processing_mean_ms"],
        )

        now = self.resource_step(
            now,
            "orchestrator",
            self.parameters["orchestration_mean_ms"],
        )

        now, connector_failed = self.connector_processing(now)
        trust_failed = False

        if not connector_failed:
            now = self.fhir_processing(now)

            requires_trust_check = (
                self.random.random()
                < self.parameters[
                    "ingestion_trust_check_probability"
                ]
            )

            if requires_trust_check:
                now, trust_failed = self.trust_lookup(
                    now,
                    context,
                )

        request_failed = connector_failed or trust_failed

        if not request_failed:
            now = self.compliance_recording(
                now,
                context,
            )

            now = self.audit_logging(
                now,
                context,
            )

        if connector_failed:
            failure_reason = "connector_failure"
        elif trust_failed:
            failure_reason = "trust_resolution_failure"
        else:
            failure_reason = ""

        return RequestResult(
            request_id=request_id,
            replication=self.replication,
            architecture=self.architecture,
            scenario="high_volume_ingestion",
            start_time_s=arrival_time,
            end_time_s=now,
            latency_ms=(now - arrival_time) * MS,
            success=not request_failed,
            failure_reason=failure_reason,
            trust_lookups=context.trust_lookups,
            trust_cache_hit=context.cache_hits,
            status_check_used=0,
            obligations_executed=0,
            retry_attempts=context.retry_attempts,
            fallback_used=context.fallback_used,
            circuit_opened=context.circuit_opened,
            minimisation_applied=0,
            compliance_recorded=context.compliance,
            audit_logged=context.audit_logs,
            audit_tagged=context.audit_tags,
            revocation_propagation_ms=(context.revocation_propagation_ms),
            unauthorized_continuation_ms=(context.unauthorized_continuation_ms),
        )
        
    def process_consent_revocation(
        self,
        request_id: int,
        arrival_time: float,
    ) -> RequestResult:
        """Process consent revocation for an active access session."""

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

        now, trust_failed = self.trust_lookup(now, context)
        status_failed = False
        revocation_failed = False

        if not trust_failed:
            now, status_failed = self.credential_status_check(
                now,
                context,
            )

        if not trust_failed and not status_failed:
            now = self.policy_and_obligation_handling(
                now,
                context,
            )

            now, revocation_failed = self.revocation_handling(
                now,
                context,
            )

        request_failed = (
            trust_failed
            or status_failed
            or revocation_failed
        )

        if not request_failed:
            now = self.compliance_recording(now, context)
            now = self.audit_logging(now, context)

        if trust_failed:
            failure_reason = "trust_resolution_failure"
        elif status_failed:
            failure_reason = "credential_status_failure"
        elif revocation_failed:
            failure_reason = "revocation_propagation_delay"
        else:
            failure_reason = ""

        return RequestResult(
            request_id=request_id,
            replication=self.replication,
            architecture=self.architecture,
            scenario="consent_revocation",
            start_time_s=arrival_time,
            end_time_s=now,
            latency_ms=(now - arrival_time) * MS,
            success=not request_failed,
            failure_reason=failure_reason,
            trust_lookups=context.trust_lookups,
            trust_cache_hit=context.cache_hits,
            status_check_used=context.status_checks,
            obligations_executed=context.obligations,
            retry_attempts=context.retry_attempts,
            fallback_used=context.fallback_used,
            circuit_opened=context.circuit_opened,
            minimisation_applied=0,
            compliance_recorded=context.compliance,
            audit_logged=context.audit_logs,
            audit_tagged=context.audit_tags,
            revocation_propagation_ms=(
                context.revocation_propagation_ms
            ),
            unauthorized_continuation_ms=(
                context.unauthorized_continuation_ms
            ),
        )

    def process_research_donation(
        self,
        request_id: int,
        arrival_time: float,
    ) -> RequestResult:
        """Process consented health-data donation for research."""

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

        now, trust_failed = self.trust_lookup(now, context)
        status_failed = False

        if not trust_failed:
            now, status_failed = self.credential_status_check(
                now,
                context,
            )

        privacy_failed = not self.parameters.get(
            "anonymization_enabled",
            False,
        )

        if not trust_failed and not status_failed:
            now = self.policy_and_obligation_handling(
                now,
                context,
            )
            now = self.data_minimisation(now, context)
            now = self.anonymization_processing(now, context)

            if not privacy_failed:
                now = self.fhir_processing(now)

            now = self.compliance_recording(now, context)
            now = self.audit_logging(now, context)

        request_failed = (
            trust_failed
            or status_failed
            or privacy_failed
        )

        if trust_failed:
            failure_reason = "trust_resolution_failure"
        elif status_failed:
            failure_reason = "credential_status_failure"
        elif privacy_failed:
            failure_reason = "anonymization_unavailable"
        else:
            failure_reason = ""

        return RequestResult(
            request_id=request_id,
            replication=self.replication,
            architecture=self.architecture,
            scenario="research_donation",
            start_time_s=arrival_time,
            end_time_s=now,
            latency_ms=(now - arrival_time) * MS,
            success=not request_failed,
            failure_reason=failure_reason,
            trust_lookups=context.trust_lookups,
            trust_cache_hit=context.cache_hits,
            status_check_used=context.status_checks,
            obligations_executed=context.obligations,
            retry_attempts=context.retry_attempts,
            fallback_used=context.fallback_used,
            circuit_opened=context.circuit_opened,
            minimisation_applied=context.minimisation,
            compliance_recorded=context.compliance,
            audit_logged=context.audit_logs,
            audit_tagged=context.audit_tags,
            anonymization_applied=context.anonymization,
        )
    def process_multi_device_access(
        self,
        request_id: int,
        arrival_time: float,
    ) -> RequestResult:
        """Process one healthcare episode across multiple devices."""

        context = RequestContext()
        now = arrival_time

        device_count = max(
            1,
            int(self.parameters.get("devices_per_episode", 3)),
        )

        trust_failed = False
        status_failed = False

        for device_index in range(device_count):
            use_shared_session = (
                device_index > 0
                and self.parameters.get(
                    "cross_device_sync_enabled",
                    False,
                )
            )

            if use_shared_session:
                now = self.resource_step(
                    now,
                    "session",
                    self.parameters["session_sync_mean_ms"],
                )
                continue

            now = self.resource_step(
                now,
                "verifier",
                self.parameters[
                    "credential_verification_mean_ms"
                ],
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

            if trust_failed:
                break

            now, status_failed = self.credential_status_check(
                now,
                context,
            )

            if status_failed:
                break

        request_failed = trust_failed or status_failed

        if not request_failed:
            now = self.policy_and_obligation_handling(
                now,
                context,
            )
            now = self.data_minimisation(now, context)
            now = self.compliance_recording(now, context)
            now = self.audit_logging(now, context)

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
            scenario="multi_device_access",
            start_time_s=arrival_time,
            end_time_s=now,
            latency_ms=(now - arrival_time) * MS,
            success=not request_failed,
            failure_reason=failure_reason,
            trust_lookups=context.trust_lookups,
            trust_cache_hit=context.cache_hits,
            status_check_used=context.status_checks,
            obligations_executed=context.obligations,
            retry_attempts=context.retry_attempts,
            fallback_used=context.fallback_used,
            circuit_opened=context.circuit_opened,
            minimisation_applied=context.minimisation,
            compliance_recorded=context.compliance,
            audit_logged=context.audit_logs,
            audit_tagged=context.audit_tags,
        )
    def process_lab_ingestion_recovery(
        self,
        request_id: int,
        arrival_time: float,
    ) -> RequestResult:
        """Process laboratory-data ingestion during disruption."""

        context = RequestContext()
        now = arrival_time

        now = self.resource_step(
            now,
            "queue",
            self.parameters["queue_processing_mean_ms"],
        )

        now = self.resource_step(
            now,
            "orchestrator",
            self.parameters["orchestration_mean_ms"],
        )

        trust_failed = False

        if (
            self.random.random()
            < self.parameters["ingestion_trust_check_probability"]
        ):
            now, trust_failed = self.trust_lookup(
                now,
                context,
                forced_failure=True,
            )

        connector_failed = False

        if not trust_failed:
            now, connector_failed = self.connector_processing(now)

        if not trust_failed and not connector_failed:
            now = self.fhir_processing(now)
            now = self.compliance_recording(now, context)
            now = self.audit_logging(now, context)

        request_failed = trust_failed or connector_failed

        if trust_failed:
            failure_reason = "trust_resolution_failure"
        elif connector_failed:
            failure_reason = "connector_failure"
        else:
            failure_reason = ""

        return RequestResult(
            request_id=request_id,
            replication=self.replication,
            architecture=self.architecture,
            scenario="lab_ingestion_recovery",
            start_time_s=arrival_time,
            end_time_s=now,
            latency_ms=(now - arrival_time) * MS,
            success=not request_failed,
            failure_reason=failure_reason,
            trust_lookups=context.trust_lookups,
            trust_cache_hit=context.cache_hits,
            status_check_used=context.status_checks,
            obligations_executed=context.obligations,
            retry_attempts=context.retry_attempts,
            fallback_used=context.fallback_used,
            circuit_opened=context.circuit_opened,
            minimisation_applied=context.minimisation,
            compliance_recorded=context.compliance,
            audit_logged=context.audit_logs,
            audit_tagged=context.audit_tags,
        )
    def process_consent_based_access(
        self,
        request_id: int,
        arrival_time: float,
    ) -> RequestResult:
        """Process healthcare-data access under active patient consent."""

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

        now, trust_failed = self.trust_lookup(now, context)

        status_failed = False
        revocation_failed = False

        if not trust_failed:
            now, status_failed = self.credential_status_check(
                now,
                context,
            )

        if not trust_failed and not status_failed:
            now = self.policy_and_obligation_handling(
                now,
                context,
            )

            now, revocation_failed = self.revocation_handling(
                now,
                context,
            )

        request_failed = (
            trust_failed
            or status_failed
            or revocation_failed
        )

        if not request_failed:
            now = self.data_minimisation(
                now,
                context,
            )

            now = self.fhir_processing(now)

            now = self.compliance_recording(
                now,
                context,
            )

            now = self.audit_logging(
                now,
                context,
            )

        if trust_failed:
            failure_reason = "trust_resolution_failure"
        elif status_failed:
            failure_reason = "credential_status_failure"
        elif revocation_failed:
            failure_reason = "revocation_propagation_delay"
        else:
            failure_reason = ""

        return RequestResult(
            request_id=request_id,
            replication=self.replication,
            architecture=self.architecture,
            scenario="consent_based_access",
            start_time_s=arrival_time,
            end_time_s=now,
            latency_ms=(now - arrival_time) * MS,
            success=not request_failed,
            failure_reason=failure_reason,
            trust_lookups=context.trust_lookups,
            trust_cache_hit=context.cache_hits,
            status_check_used=context.status_checks,
            obligations_executed=context.obligations,
            retry_attempts=context.retry_attempts,
            fallback_used=context.fallback_used,
            circuit_opened=context.circuit_opened,
            minimisation_applied=context.minimisation,
            compliance_recorded=context.compliance,
            audit_logged=context.audit_logs,
            audit_tagged=context.audit_tags,
            revocation_propagation_ms=(
                context.revocation_propagation_ms
            ),
            unauthorized_continuation_ms=(
                context.unauthorized_continuation_ms
            ),
        )

    def process_trust_failure(
        self,
        request_id: int,
        arrival_time: float,
    ) -> RequestResult:
        """Process access while the trust service is degraded."""

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
            forced_failure=True,
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
            now = self.data_minimisation(now, context)
            now = self.compliance_recording(now, context)
            now = self.audit_logging(now, context)

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
            scenario="trust_failure",
            start_time_s=arrival_time,
            end_time_s=now,
            latency_ms=(now - arrival_time) * MS,
            success=not request_failed,
            failure_reason=failure_reason,
            trust_lookups=context.trust_lookups,
            trust_cache_hit=context.cache_hits,
            status_check_used=context.status_checks,
            obligations_executed=context.obligations,
            retry_attempts=context.retry_attempts,
            fallback_used=context.fallback_used,
            circuit_opened=context.circuit_opened,
            minimisation_applied=context.minimisation,
            compliance_recorded=context.compliance,
            audit_logged=context.audit_logs,
            audit_tagged=context.audit_tags,
        )

    def run_audit_investigation(
        self,
    ) -> List[RequestResult]:
        """Run the audit-investigation scenario."""

        rate = self.simulation[
            "arrival_rate_per_second"
        ]["audit_investigation"]

        arrivals = self.generate_arrivals(rate)
        results = []

        for request_id, arrival_time in enumerate(arrivals, start=1):
            result = self.process_audit_investigation(
                request_id,
                arrival_time,
            )

            if arrival_time >= self.warmup_s:
                results.append(result)

        return results

    def run_cross_org_exchange(self) -> List[RequestResult]:
        """Run the cross-organizational FHIR-exchange scenario."""

        rate = self.simulation[
            "arrival_rate_per_second"
        ]["cross_org_exchange"]

        arrivals = self.generate_arrivals(rate)
        results = []

        for request_id, arrival_time in enumerate(arrivals, start=1):
            result = self.process_cross_org_exchange(
                request_id,
                arrival_time,
            )

            if arrival_time >= self.warmup_s:
                results.append(result)

        return results

    def run_high_volume_ingestion(
        self,
    ) -> List[RequestResult]:
        """Run the high-volume ingestion scenario."""

        rate = self.simulation[
            "arrival_rate_per_second"
        ]["high_volume_ingestion"]

        arrivals = self.generate_arrivals(rate)
        results = []

        for request_id, arrival_time in enumerate(arrivals, start=1):
            result = self.process_high_volume_ingestion(
                request_id,
                arrival_time,
            )

            if arrival_time >= self.warmup_s:
                results.append(result)

        return results

    def run_consent_revocation(
        self,
    ) -> List[RequestResult]:
        """Run the consent-revocation scenario."""

        rate = self.simulation[
            "arrival_rate_per_second"
        ]["consent_revocation"]

        arrivals = self.generate_arrivals(rate)
        results = []

        for request_id, arrival_time in enumerate(arrivals, start=1):
            result = self.process_consent_revocation(
                request_id,
                arrival_time,
            )

            if arrival_time >= self.warmup_s:
                results.append(result)

        return results
    def run_consent_based_access(
        self,
    ) -> List[RequestResult]:
        """Run the consent-based healthcare-access scenario."""

        rate = self.simulation[
            "arrival_rate_per_second"
        ]["consent_based_access"]

        arrivals = self.generate_arrivals(rate)
        results = []

        for request_id, arrival_time in enumerate(arrivals, start=1):
            result = self.process_consent_based_access(
                request_id,
                arrival_time,
            )

            if arrival_time >= self.warmup_s:
                results.append(result)

        return results

    def run_trust_failure(self) -> List[RequestResult]:
        """Run the degraded trust-service scenario."""

        rate = self.simulation[
            "arrival_rate_per_second"
        ]["trust_failure"]

        arrivals = self.generate_arrivals(rate)
        results = []

        for request_id, arrival_time in enumerate(arrivals, start=1):
            result = self.process_trust_failure(
                request_id,
                arrival_time,
            )

            if arrival_time >= self.warmup_s:
                results.append(result)

        return results
    def run_lab_ingestion_recovery(
        self,
    ) -> List[RequestResult]:
        """Run the laboratory-ingestion recovery scenario."""

        rate = self.simulation[
            "arrival_rate_per_second"
        ]["lab_ingestion_recovery"]

        arrivals = self.generate_arrivals(rate)
        results = []

        for request_id, arrival_time in enumerate(
            arrivals,
            start=1,
        ):
            result = self.process_lab_ingestion_recovery(
                request_id,
                arrival_time,
            )

            if arrival_time >= self.warmup_s:
                results.append(result)

        return results

    def run_multi_device_access(
        self,
    ) -> List[RequestResult]:
        """Run the multi-device healthcare-access scenario."""

        rate = self.simulation[
            "arrival_rate_per_second"
        ]["multi_device_access"]

        arrivals = self.generate_arrivals(rate)
        results = []

        for request_id, arrival_time in enumerate(
            arrivals,
            start=1,
        ):
            result = self.process_multi_device_access(
                request_id,
                arrival_time,
            )

            if arrival_time >= self.warmup_s:
                results.append(result)

        return results

    def run_research_donation(
        self,
    ) -> List[RequestResult]:
        """Run the research-donation scenario."""

        rate = self.simulation[
            "arrival_rate_per_second"
        ]["research_donation"]

        arrivals = self.generate_arrivals(rate)
        results = []

        for request_id, arrival_time in enumerate(
            arrivals,
            start=1,
        ):
            result = self.process_research_donation(
                request_id,
                arrival_time,
            )

            if arrival_time >= self.warmup_s:
                results.append(result)

        return results
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
         for scenario in [
            "emergency_access",
            "consent_based_access",
            "audit_investigation",
            "cross_org_exchange",
            "high_volume_ingestion",
            "consent_revocation",
            "trust_failure",
            "lab_ingestion_recovery",
            "multi_device_access",
            "research_donation",
        ]:
            for replication in range(replication_count):
                engine = SimulationEngine(
                    config,
                    architecture,
                    replication,
                )

                if scenario == "emergency_access":
                    replication_results = engine.run()

                elif scenario == "audit_investigation":
                    replication_results = (
                        engine.run_audit_investigation()
                    )

                elif scenario == "cross_org_exchange":
                    replication_results = (
                        engine.run_cross_org_exchange()
                    )

                elif scenario == "high_volume_ingestion":
                    replication_results = (
                        engine.run_high_volume_ingestion()
                    )

                elif scenario == "consent_revocation":
                    replication_results = (
                        engine.run_consent_revocation()
                    )
                elif scenario == "consent_based_access":
                    replication_results = (
                        engine.run_consent_based_access()
                    )

                elif scenario == "trust_failure":
                    replication_results = (
                        engine.run_trust_failure()
                    )

                elif scenario == "lab_ingestion_recovery":
                    replication_results = (
                        engine.run_lab_ingestion_recovery()
                    )

                elif scenario == "multi_device_access":
                    replication_results = (
                        engine.run_multi_device_access()
                    )
                elif scenario == "research_donation":
                    replication_results = (
                        engine.run_research_donation()
                    )
                else:
                    raise ValueError(
                        f"Unknown scenario: {scenario}"
                    )
                all_results.extend(replication_results)

                successful = sum(
                    result.success
                    for result in replication_results
                )

                print(
                    f"{architecture}, {scenario}, "
                    f"replication {replication + 1}: "
                    f"{len(replication_results)} requests, "
                    f"{successful} successful"
                )

    detail = pd.DataFrame(
        asdict(result)
        for result in all_results
    )

    summary = (
        detail.groupby(
            ["architecture", "scenario", "replication"],
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
            audit_logging_rate=("audit_logged", "mean"),
            audit_tagging_rate=("audit_tagged", "mean"),
                        average_revocation_propagation_ms=(
                "revocation_propagation_ms",
                "mean",
            ),
            anonymization_rate=(
                "anonymization_applied",
                "mean",
            ),
            average_unauthorized_continuation_ms=(
                "unauthorized_continuation_ms",
                "mean",
            ),
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
        summary.groupby(["architecture", "scenario"], as_index=False,)
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
            mean_audit_logging_rate=(
                "audit_logging_rate",
                "mean",
            ),
            mean_audit_tagging_rate=(
                "audit_tagging_rate",
                "mean",
            ),

            mean_anonymization_rate=(
                "anonymization_rate",
                "mean",
            ),
            mean_revocation_propagation_ms=(
                "average_revocation_propagation_ms",
                "mean",
            ),
            mean_unauthorized_continuation_ms=(
                "average_unauthorized_continuation_ms",
                "mean",
            ),
        )
    )

    
    print("\nScenario comparison")
    print(overall.to_string(index=False))
    print("\nResults saved in the results directory.")


if __name__ == "__main__":
    main()
