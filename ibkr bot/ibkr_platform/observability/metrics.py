"""
Prometheus metrics infrastructure.

Defines all metrics for the trading platform:
- Latency distributions (histograms)
- Throughput counters
- State gauges (positions, orders, P&L)
- Business metrics (fill ratios, slippage, etc.)

CRITICAL: Metric updates must be extremely fast - avoid locks.
"""

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Summary,
    start_http_server,
)

from ibkr_platform.core.config import ObservabilityConfig


# Create custom registry to avoid conflicts
registry = CollectorRegistry()


# ============================================================================
# LATENCY METRICS (Histograms for percentiles)
# ============================================================================

# Decision to order submission latency (the most critical metric)
decision_to_order_latency = Histogram(
    "decision_to_order_latency_seconds",
    "Latency from decision to order submission",
    buckets=[
        0.0001,  # 100μs
        0.0005,  # 500μs
        0.001,  # 1ms
        0.005,  # 5ms
        0.01,  # 10ms
        0.05,  # 50ms
        0.1,  # 100ms
        0.5,  # 500ms
        1.0,  # 1s
    ],
    registry=registry,
)

# Market data processing latency
market_data_processing_latency = Histogram(
    "market_data_processing_latency_seconds",
    "Latency to process market data updates",
    labelnames=["data_type"],  # tick, bar, orderbook
    buckets=[0.00001, 0.00005, 0.0001, 0.0005, 0.001, 0.005, 0.01],
    registry=registry,
)

# Order acknowledgement latency
order_ack_latency = Histogram(
    "order_acknowledgement_latency_seconds",
    "Latency from submission to broker acknowledgement",
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
    registry=registry,
)

# Risk check latency
risk_check_latency = Histogram(
    "risk_check_latency_seconds",
    "Pre-trade risk check latency",
    labelnames=["check_type"],
    buckets=[0.00001, 0.00005, 0.0001, 0.0005, 0.001],
    registry=registry,
)


# ============================================================================
# THROUGHPUT METRICS (Counters)
# ============================================================================

# Market data
ticks_received = Counter(
    "ticks_received_total",
    "Total ticks received",
    labelnames=["symbol"],
    registry=registry,
)

bars_received = Counter(
    "bars_received_total",
    "Total bars received",
    labelnames=["symbol", "timeframe"],
    registry=registry,
)

# Orders
orders_created = Counter(
    "orders_created_total",
    "Total orders created",
    labelnames=["strategy_id", "side", "order_type"],
    registry=registry,
)

orders_submitted = Counter(
    "orders_submitted_total",
    "Total orders submitted to broker",
    labelnames=["strategy_id", "side"],
    registry=registry,
)

orders_filled = Counter(
    "orders_filled_total",
    "Total orders filled",
    labelnames=["strategy_id", "side"],
    registry=registry,
)

orders_cancelled = Counter(
    "orders_cancelled_total",
    "Total orders cancelled",
    labelnames=["strategy_id", "reason"],
    registry=registry,
)

orders_rejected = Counter(
    "orders_rejected_total",
    "Total orders rejected",
    labelnames=["strategy_id", "reason"],
    registry=registry,
)

# Executions
executions_received = Counter(
    "executions_received_total",
    "Total executions received",
    labelnames=["strategy_id", "side"],
    registry=registry,
)

total_shares_traded = Counter(
    "shares_traded_total",
    "Total shares traded",
    labelnames=["strategy_id", "side"],
    registry=registry,
)

total_notional_traded = Counter(
    "notional_traded_total_usd",
    "Total notional value traded (USD)",
    labelnames=["strategy_id", "side"],
    registry=registry,
)

# Risk
risk_checks_performed = Counter(
    "risk_checks_performed_total",
    "Total risk checks performed",
    labelnames=["check_type"],
    registry=registry,
)

risk_checks_failed = Counter(
    "risk_checks_failed_total",
    "Total risk checks failed",
    labelnames=["check_type", "reason"],
    registry=registry,
)

circuit_breaker_triggers = Counter(
    "circuit_breaker_triggers_total",
    "Total circuit breaker triggers",
    labelnames=["breaker_name"],
    registry=registry,
)


# ============================================================================
# STATE METRICS (Gauges)
# ============================================================================

# Positions
active_positions = Gauge(
    "active_positions",
    "Number of active positions",
    labelnames=["strategy_id"],
    registry=registry,
)

gross_exposure_usd = Gauge(
    "gross_exposure_usd",
    "Gross exposure in USD",
    labelnames=["strategy_id"],
    registry=registry,
)

net_exposure_usd = Gauge(
    "net_exposure_usd",
    "Net exposure in USD",
    labelnames=["strategy_id"],
    registry=registry,
)

# Orders
active_orders = Gauge(
    "active_orders",
    "Number of active orders",
    labelnames=["strategy_id", "status"],
    registry=registry,
)

# P&L
realized_pnl_usd = Gauge(
    "realized_pnl_usd",
    "Realized P&L in USD",
    labelnames=["strategy_id"],
    registry=registry,
)

unrealized_pnl_usd = Gauge(
    "unrealized_pnl_usd",
    "Unrealized P&L in USD",
    labelnames=["strategy_id"],
    registry=registry,
)

total_pnl_usd = Gauge(
    "total_pnl_usd",
    "Total P&L in USD",
    labelnames=["strategy_id"],
    registry=registry,
)

# Risk metrics
portfolio_var = Gauge(
    "portfolio_var_usd",
    "Portfolio Value at Risk (USD)",
    labelnames=["horizon"],  # 1min, 5min, 30min, daily
    registry=registry,
)

portfolio_delta = Gauge(
    "portfolio_delta",
    "Portfolio delta exposure",
    registry=registry,
)

portfolio_gamma = Gauge(
    "portfolio_gamma",
    "Portfolio gamma exposure",
    registry=registry,
)

margin_used = Gauge(
    "margin_used_usd",
    "Margin used (USD)",
    registry=registry,
)

margin_available = Gauge(
    "margin_available_usd",
    "Margin available (USD)",
    registry=registry,
)

margin_utilization = Gauge(
    "margin_utilization_ratio",
    "Margin utilization ratio (0-1)",
    registry=registry,
)

# System health
connection_status = Gauge(
    "connection_status",
    "Connection status (1=connected, 0=disconnected)",
    labelnames=["service"],  # ibkr, database, redis
    registry=registry,
)


# ============================================================================
# BUSINESS METRICS (Summaries for percentiles)
# ============================================================================

fill_price_vs_decision_price = Summary(
    "fill_price_vs_decision_price_bps",
    "Fill price vs decision price in basis points (slippage)",
    labelnames=["strategy_id", "side"],
    registry=registry,
)

fill_ratio = Summary(
    "fill_ratio",
    "Fill ratio for orders (0-1)",
    labelnames=["strategy_id", "order_type"],
    registry=registry,
)

time_in_position_seconds = Summary(
    "time_in_position_seconds",
    "Time in position before exit",
    labelnames=["strategy_id"],
    registry=registry,
)


# ============================================================================
# INITIALIZATION
# ============================================================================

_metrics_server_started = False


def start_metrics_server(config: ObservabilityConfig) -> None:
    """
    Start Prometheus metrics HTTP server.
    
    Args:
        config: Observability configuration
    """
    global _metrics_server_started
    
    if not config.prometheus_enabled:
        return
    
    if _metrics_server_started:
        return
    
    start_http_server(config.prometheus_port, registry=registry)
    _metrics_server_started = True
    
    # Initialize connection status to 0
    connection_status.labels(service="ibkr").set(0)
    connection_status.labels(service="database").set(0)
    connection_status.labels(service="redis").set(0)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def record_order_created(strategy_id: str, side: str, order_type: str) -> None:
    """Record order creation."""
    orders_created.labels(strategy_id=strategy_id, side=side, order_type=order_type).inc()


def record_order_filled(strategy_id: str, side: str, shares: float, notional: float) -> None:
    """Record order fill."""
    orders_filled.labels(strategy_id=strategy_id, side=side).inc()
    total_shares_traded.labels(strategy_id=strategy_id, side=side).inc(shares)
    total_notional_traded.labels(strategy_id=strategy_id, side=side).inc(notional)


def record_risk_check(check_type: str, passed: bool, reason: str = "") -> None:
    """Record risk check."""
    risk_checks_performed.labels(check_type=check_type).inc()
    if not passed:
        risk_checks_failed.labels(check_type=check_type, reason=reason).inc()


def update_portfolio_metrics(
    strategy_id: str,
    gross_exposure: float,
    net_exposure: float,
    realized_pnl: float,
    unrealized_pnl: float,
) -> None:
    """Update portfolio metrics."""
    gross_exposure_usd.labels(strategy_id=strategy_id).set(gross_exposure)
    net_exposure_usd.labels(strategy_id=strategy_id).set(net_exposure)
    realized_pnl_usd.labels(strategy_id=strategy_id).set(realized_pnl)
    unrealized_pnl_usd.labels(strategy_id=strategy_id).set(unrealized_pnl)
    total_pnl_usd.labels(strategy_id=strategy_id).set(realized_pnl + unrealized_pnl)
