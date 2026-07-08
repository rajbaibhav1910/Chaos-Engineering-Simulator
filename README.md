<div align="center">

# 🐒 Chaos Engineering Simulator

**A dependency-free Python simulator that proves resilience patterns work — with numbers.**

[![Python](https://img.shields.io/badge/Python-3.7+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![No Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](#license)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-blueviolet.svg)](#contributing)

*Inspired by Netflix's Chaos Monkey and AWS Fault Injection Simulator*

</div>

---

## 🎯 The Idea

Cloud systems don't fail politely — servers crash, networks lag, dependencies time out.
**Chaos engineering** is the practice of deliberately injecting failure into a system
*on purpose*, so you can prove it survives before your customers find out the hard way.

This simulator builds a tiny chain of microservices, unleashes a chaos monkey on them,
and measures exactly how much **retries**, **circuit breakers**, and **fallbacks**
improve survival — same chaos, same seed, side-by-side comparison.

```
auth-svc  →  payment-svc  →  inventory-svc
   ⚡           ⚡                ⚡
 chaos        chaos            chaos
```

## 📊 The Result

Running the same chaotic conditions twice — once raw, once with resilience patterns applied:

| | Without Resilience | With Resilience |
|---|---|---|
| **End-to-end success rate** | 37.0% | **100.0%** 🎉 |
| **Approach** | Single attempt, fail fast | Retry → Circuit Breaker → Fallback |

> Same random seed. Same injected chaos. The only difference is the resilience layer.

## 🧠 What's Implemented

| Pattern | What it does | Why it matters |
|---|---|---|
| **Retry** | Re-attempts a failed call before giving up | Absorbs transient blips (network jitter, brief overload) |
| **Circuit Breaker** | Trips OPEN after repeated failures, blocks calls, tests recovery via HALF_OPEN | Stops hammering a dying service — protects it *and* the caller |
| **Fallback** | Returns a cached/default response instead of failing the request | Degrades gracefully instead of crashing the whole chain |

### Circuit breaker state machine

```
        failures ≥ threshold
  CLOSED ──────────────────────▶ OPEN
    ▲                              │
    │                              │ cooldown elapses
    │ test call succeeds           ▼
    └──────────────────────── HALF_OPEN
                 test call fails
                        └──────────▶ back to OPEN
```

## 🚀 Quick Start

```bash
git clone https://github.com/rajbaibhav1910/Chaos-Engineering-Simulator.git
cd Chaos-Engineering-Simulator

# Side-by-side comparison (recommended)
python chaos_sim.py --compare --requests 200 --failure-rate 0.3

# Or run a single scenario
python chaos_sim.py --requests 200 --failure-rate 0.3                  # with resilience
python chaos_sim.py --requests 200 --failure-rate 0.3 --no-resilience  # without
```

No `pip install` needed — pure Python 3 standard library.

## 📟 Sample Output

```
=== WITHOUT resilience patterns ===
End-to-end request success rate: 74/200 (37.0%)

Service        Success   Failed    Fallback  CB Trips
-------------------------------------------------------
auth-svc       134       66        0         0
payment-svc    102       32        0         0
inventory-svc  74        28        0         0

=== WITH resilience patterns (retry + circuit breaker + fallback) ===
End-to-end request success rate: 200/200 (100.0%)

Service        Success   Failed    Fallback  CB Trips
-------------------------------------------------------
auth-svc       199       1         1         0
payment-svc    194       6         6         0
inventory-svc  165       8         35        4

Resilience patterns improved end-to-end success rate by 63.0 percentage points.
```

## ⚙️ CLI Options

| Flag | Default | Description |
|---|---|---|
| `--requests` | `200` | Number of end-to-end requests to simulate |
| `--failure-rate` | `0.3` | Per-call chaos failure probability (0–1) |
| `--no-resilience` | off | Disable retries / circuit breaker / fallback |
| `--compare` | off | Run both scenarios with identical chaos, side by side |

## 🔭 Roadmap / Extensions

- [ ] Exponential backoff with jitter on retries
- [ ] Turn each `Service` into a real Flask microservice, inject chaos over HTTP
- [ ] Export metrics in Prometheus format, visualize in Grafana
- [ ] Model network partitions (reachable but returns stale data)
- [ ] Deploy the 3 services on AWS Lambda and chaos-test them for real
- [ ] Add a `sticky failure` mode where one bad deploy degrades over time

## 🧩 Why This Project

Most beginner cloud projects stop at "deploy X to AWS." This one goes a layer deeper —
it's about **reliability engineering**: the discipline behind SLAs, SRE error budgets,
and why companies like Netflix run chaos experiments in production, on purpose.

## 🤝 Contributing

Issues and PRs welcome — extend an algorithm, add a new resilience pattern, or wire it
up to a real cloud provider. See the [Roadmap](#-roadmap--extensions) for ideas.

## 📄 License

[MIT](LICENSE) — free to use, modify, and learn from.

---

<div align="center">
<sub>Built as a hands-on exploration of cloud reliability patterns.</sub>
</div>
