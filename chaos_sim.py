"""Chaos Engineering Simulator.

Pure-Python portfolio project that demonstrates:
- Chaos injection (failures + latency)
- Circuit breaker resilience pattern
- Retries + fallback behavior
- Side-by-side comparison with identical random seed
"""

from __future__ import annotations

import argparse
import random
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class ServiceStats:
    """Tracks per-service outcomes for a simulation run."""

    success_count: int = 0
    failed_count: int = 0
    fallback_count: int = 0
    circuit_breaker_trip_count: int = 0


@dataclass
class SimulationResult:
    """Aggregated simulation result object."""

    total_requests: int
    end_to_end_successes: int
    end_to_end_failures: int
    services: Dict[str, ServiceStats]

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.end_to_end_successes / self.total_requests) * 100.0


class ChaosMonkey:
    """Injects random failures and latency spikes into service calls."""

    def __init__(
        self,
        failure_rate: float = 0.2,
        latency_spike_rate: float = 0.2,
        max_latency_ms: int = 40,
        rng: Optional[random.Random] = None,
    ) -> None:
        self.failure_rate = failure_rate
        self.latency_spike_rate = latency_spike_rate
        self.max_latency_ms = max_latency_ms
        self.rng = rng or random.Random()

    def maybe_add_latency(self) -> None:
        """Sleep briefly to simulate a latency spike."""
        if self.rng.random() < self.latency_spike_rate:
            latency_ms = self.rng.uniform(1, self.max_latency_ms)
            time.sleep(latency_ms / 1000.0)

    def maybe_fail(self) -> bool:
        """Return True when call should fail."""
        return self.rng.random() < self.failure_rate


class CircuitBreaker:
    """Classic CLOSED -> OPEN -> HALF_OPEN circuit breaker."""

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    def __init__(self, failure_threshold: int = 3, cooldown_seconds: float = 0.2) -> None:
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.state = self.CLOSED
        self._consecutive_failures = 0
        self._opened_at: Optional[float] = None
        self.trip_count = 0

    def allow_request(self) -> bool:
        """Check if the call is allowed in current breaker state."""
        if self.state == self.CLOSED:
            return True

        if self.state == self.OPEN:
            if self._opened_at is None:
                self._opened_at = time.monotonic()
            elapsed = time.monotonic() - self._opened_at
            if elapsed >= self.cooldown_seconds:
                self.state = self.HALF_OPEN
                return True
            return False

        # HALF_OPEN: allow one test request
        return True

    def record_success(self) -> None:
        """Record a successful call and close/reset as needed."""
        self._consecutive_failures = 0
        if self.state in (self.HALF_OPEN, self.OPEN):
            self.state = self.CLOSED
            self._opened_at = None

    def record_failure(self) -> None:
        """Record a failed call and trip circuit if threshold reached."""
        if self.state == self.HALF_OPEN:
            self._trip_open()
            return

        self._consecutive_failures += 1
        if self._consecutive_failures >= self.failure_threshold:
            self._trip_open()

    def _trip_open(self) -> None:
        self.state = self.OPEN
        self._opened_at = time.monotonic()
        self._consecutive_failures = 0
        self.trip_count += 1


class Service:
    """Represents a microservice with optional resilience mechanisms."""

    def __init__(
        self,
        name: str,
        chaos_monkey: ChaosMonkey,
        max_retries: int = 0,
        circuit_breaker: Optional[CircuitBreaker] = None,
        fallback_response: Optional[str] = None,
    ) -> None:
        self.name = name
        self.chaos_monkey = chaos_monkey
        self.max_retries = max_retries
        self.circuit_breaker = circuit_breaker
        self.fallback_response = fallback_response
        self.stats = ServiceStats()

    def handle_call(self) -> Tuple[bool, str]:
        """Process one request through this service."""
        attempts = self.max_retries + 1

        for _ in range(attempts):
            if self.circuit_breaker and not self.circuit_breaker.allow_request():
                return self._use_fallback_or_fail("circuit-open")

            self.chaos_monkey.maybe_add_latency()
            failed = self.chaos_monkey.maybe_fail()

            if failed:
                if self.circuit_breaker:
                    self.circuit_breaker.record_failure()
                    self.stats.circuit_breaker_trip_count = self.circuit_breaker.trip_count
                continue

            if self.circuit_breaker:
                self.circuit_breaker.record_success()
            self.stats.success_count += 1
            return True, f"{self.name}:ok"

        return self._use_fallback_or_fail("max-retries-exhausted")

    def _use_fallback_or_fail(self, reason: str) -> Tuple[bool, str]:
        if self.fallback_response is not None:
            self.stats.success_count += 1
            self.stats.fallback_count += 1
            return True, f"{self.name}:fallback({reason})"

        self.stats.failed_count += 1
        return False, f"{self.name}:failed({reason})"


def run_simulation(
    num_requests: int,
    failure_rate: float,
    resilient: bool,
    seed: int,
) -> SimulationResult:
    """Run end-to-end requests through auth -> payment -> inventory chain."""
    rng = random.Random(seed)
    chaos_monkey = ChaosMonkey(
        failure_rate=failure_rate,
        latency_spike_rate=0.2,
        max_latency_ms=10,
        rng=rng,
    )

    if resilient:
        services: List[Service] = [
            Service(
                "auth-svc",
                chaos_monkey=chaos_monkey,
                max_retries=2,
                circuit_breaker=CircuitBreaker(failure_threshold=3, cooldown_seconds=0.03),
                fallback_response="AUTH_DEGRADED",
            ),
            Service(
                "payment-svc",
                chaos_monkey=chaos_monkey,
                max_retries=2,
                circuit_breaker=CircuitBreaker(failure_threshold=3, cooldown_seconds=0.03),
                fallback_response="PAYMENT_RETRY_QUEUED",
            ),
            Service(
                "inventory-svc",
                chaos_monkey=chaos_monkey,
                max_retries=2,
                circuit_breaker=CircuitBreaker(failure_threshold=3, cooldown_seconds=0.03),
                fallback_response="INVENTORY_STALE_CACHE",
            ),
        ]
    else:
        services = [
            Service("auth-svc", chaos_monkey=chaos_monkey),
            Service("payment-svc", chaos_monkey=chaos_monkey),
            Service("inventory-svc", chaos_monkey=chaos_monkey),
        ]

    end_to_end_successes = 0
    end_to_end_failures = 0

    for _ in range(num_requests):
        request_ok = True
        for service in services:
            ok, _ = service.handle_call()
            if not ok:
                request_ok = False
                break

        if request_ok:
            end_to_end_successes += 1
        else:
            end_to_end_failures += 1

    return SimulationResult(
        total_requests=num_requests,
        end_to_end_successes=end_to_end_successes,
        end_to_end_failures=end_to_end_failures,
        services={svc.name: svc.stats for svc in services},
    )


def _print_single_report(label: str, result: SimulationResult) -> None:
    print(f"\n=== {label} ===")
    print(
        f"Requests: {result.total_requests} | "
        f"End-to-end success: {result.end_to_end_successes} | "
        f"Failure: {result.end_to_end_failures} | "
        f"Success rate: {result.success_rate:.1f}%"
    )
    print("-" * 79)
    print(
        f"{'Service':<15} {'Success':>8} {'Failed':>8} {'Fallback':>9} {'CB Trips':>9}"
    )
    print("-" * 79)
    for service_name, stats in result.services.items():
        print(
            f"{service_name:<15} {stats.success_count:>8} {stats.failed_count:>8} "
            f"{stats.fallback_count:>9} {stats.circuit_breaker_trip_count:>9}"
        )


def _print_compare_report(baseline: SimulationResult, resilient: SimulationResult) -> None:
    print("\n=== Chaos Engineering Simulator: Comparison Report ===")
    print("-" * 106)
    print(
        f"{'Metric':<30} {'Without resilience':>24} {'With resilience':>24} {'Delta':>20}"
    )
    print("-" * 106)

    baseline_rate = baseline.success_rate
    resilient_rate = resilient.success_rate
    delta = resilient_rate - baseline_rate

    print(
        f"{'End-to-end success rate':<30} "
        f"{baseline_rate:>23.1f}% "
        f"{resilient_rate:>23.1f}% "
        f"{delta:>19.1f} pts"
    )
    print(
        f"{'Successful requests':<30} "
        f"{baseline.end_to_end_successes:>24} "
        f"{resilient.end_to_end_successes:>24} "
        f"{(resilient.end_to_end_successes - baseline.end_to_end_successes):>20}"
    )
    print(
        f"{'Failed requests':<30} "
        f"{baseline.end_to_end_failures:>24} "
        f"{resilient.end_to_end_failures:>24} "
        f"{(resilient.end_to_end_failures - baseline.end_to_end_failures):>20}"
    )
    print("-" * 106)

    print("\nPer-service details")
    print("-" * 106)
    print(
        f"{'Service':<15} {'Mode':<20} {'Success':>8} {'Failed':>8} "
        f"{'Fallback':>9} {'CB Trips':>9}"
    )
    print("-" * 106)

    for service_name in baseline.services:
        base = baseline.services[service_name]
        res = resilient.services[service_name]
        print(
            f"{service_name:<15} {'Without resilience':<20} {base.success_count:>8} "
            f"{base.failed_count:>8} {base.fallback_count:>9} {base.circuit_breaker_trip_count:>9}"
        )
        print(
            f"{'':<15} {'With resilience':<20} {res.success_count:>8} "
            f"{res.failed_count:>8} {res.fallback_count:>9} {res.circuit_breaker_trip_count:>9}"
        )
        print("-" * 106)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Chaos Engineering Simulator")
    parser.add_argument("--requests", type=int, default=100, help="Number of requests to simulate")
    parser.add_argument(
        "--failure-rate",
        type=float,
        default=0.2,
        help="Failure probability injected by chaos monkey (0.0 to 1.0)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Run both without and with resilience using the same random seed",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.compare:
        baseline = run_simulation(
            num_requests=args.requests,
            failure_rate=args.failure_rate,
            resilient=False,
            seed=args.seed,
        )
        resilient = run_simulation(
            num_requests=args.requests,
            failure_rate=args.failure_rate,
            resilient=True,
            seed=args.seed,
        )
        _print_compare_report(baseline, resilient)
    else:
        result = run_simulation(
            num_requests=args.requests,
            failure_rate=args.failure_rate,
            resilient=True,
            seed=args.seed,
        )
        _print_single_report("With resilience", result)


if __name__ == "__main__":
    main()
