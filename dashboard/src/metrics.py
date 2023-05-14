"""Collection of all Prometheus counters."""
from prometheus_client import Counter

PROM_REQ_CNT = Counter(
    name="requests",
    documentation="Count web requests",
    labelnames=["method", "path", "code"],
)
