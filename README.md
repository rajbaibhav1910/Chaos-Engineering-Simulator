# Chaos Engineering Simulator

A pure Python 3 project that demonstrates chaos engineering and resilience patterns in a microservice chain:

`auth-svc -> payment-svc -> inventory-svc`

The simulator injects random failures and latency spikes, then compares end-to-end outcomes **with** and **without** resilience controls.

## What Chaos Engineering Is (And Why It Matters)

Chaos engineering is the disciplined practice of injecting controlled failure into systems to validate reliability assumptions before real incidents happen.

- **Netflix Chaos Monkey** popularized randomly terminating instances in production-like environments to force fault-tolerant design.
- **AWS Fault Injection Simulator (FIS)** provides managed experiments that inject infrastructure and application faults in AWS environments.

Why it matters:

- Cloud systems fail in partial, non-obvious ways.
- Resilience patterns must be tested, not assumed.
- Teams can discover weak points early and improve incident readiness.

## Resilience Patterns Implemented

### 1) Chaos Monkey (Failure + Latency Injection)

- Randomly fails service calls (`failure_rate`).
- Randomly adds latency spikes to simulate slow dependencies.
- Purpose: create realistic stress/failure conditions.

### 2) Retries

- Each service can retry failed calls (`max_retries`).
- Purpose: recover from transient faults (blips, packet loss, temporary overload).

### 3) Circuit Breaker (3-State)

- States: `CLOSED -> OPEN -> HALF_OPEN`.
- Trips to `OPEN` after repeated failures (`failure_threshold`).
- While `OPEN`, calls are blocked for a cooldown period.
- After cooldown, allows a test request in `HALF_OPEN`.
- On test success: closes to `CLOSED`; on failure: reopens.
- Purpose: prevent cascading failure and reduce pressure on unhealthy dependencies.

### 4) Fallback Response

- When retries fail (or breaker is open), service can return a degraded response.
- Purpose: preserve end-user experience and keep workflows alive in degraded mode.

## Circuit Breaker State Machine

1. **CLOSED**
   - Normal operation.
   - Failures are counted.
2. **OPEN**
   - Triggered when consecutive failures reach threshold.
   - Requests are rejected fast (fail-fast).
3. **HALF_OPEN**
   - Entered after cooldown.
   - One test call probes recovery:
     - Success -> `CLOSED`
     - Failure -> `OPEN`

## Usage

Run with resilience only (default mode):

```bash
python chaos_sim.py
```

Run a side-by-side comparison with identical random seed:

```bash
python chaos_sim.py --compare --requests 200 --failure-rate 0.3
```

You can also control reproducibility:

```bash
python chaos_sim.py --compare --requests 500 --failure-rate 0.25 --seed 123
```

## Example Output (Illustrative)

```text
=== Chaos Engineering Simulator: Comparison Report ===
----------------------------------------------------------------------------------------------------------
Metric                            Without resilience          With resilience                 Delta
----------------------------------------------------------------------------------------------------------
End-to-end success rate                        35.0%                     100.0%             +65.0 pts
Successful requests                              70                        200                 +130
Failed requests                                 130                          0                 -130
----------------------------------------------------------------------------------------------------------
```

## Interpreting Per-Service Stats

Each service reports:

- `success count`: calls that returned success (including fallback-successes).
- `failed count`: hard failures with no fallback available.
- `fallback count`: degraded-but-successful responses.
- `circuit breaker trip count`: number of times breaker transitioned to `OPEN`.

## Extension Ideas

- Replace simulated services with real Flask/FastAPI microservices.
- Add exponential backoff + jitter to retries.
- Add timeout budgets and bulkhead isolation.
- Emit metrics to Prometheus/Grafana.
- Deploy handlers to AWS Lambda and run controlled chaos experiments for real.

## Requirements

- Python 3.x
- No third-party packages (standard library only)
- No cloud account or credentials required
