"""Discrete-event evaluation of the BC-SSI healthcare architecture."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

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


def check_resource_pool() -> None:
    """Run a small queue test before adding the complete simulation."""

    pool = ResourcePool(name="trust", capacity=1)

    first_finish, first_wait = pool.process(
        now=0.0,
        service_time_s=1.0,
    )

    second_finish, second_wait = pool.process(
        now=0.5,
        service_time_s=1.0,
    )

    assert first_finish == 1.0
    assert first_wait == 0.0
    assert second_finish == 2.0
    assert second_wait == 0.5

    print("ResourcePool check passed.")


if __name__ == "__main__":
    check_resource_pool()