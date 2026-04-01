# IBKR Institutional Trading Platform

**⚠️ WARNING: This system is designed to trade REAL MONEY. Use with extreme caution.**

A tier-1 institutional-grade algorithmic trading platform connected to Interactive Brokers, targeting 2026 production quality standards with sub-millisecond latency and comprehensive risk management.

## 🏗️ Architecture Overview

- **Ultra-low latency event-driven architecture** using asyncio + uvloop
- **Multi-strategy, multi-account, multi-asset class** support
- **Institutional-grade risk engine** with real-time Greeks, VaR, stress testing
- **Advanced execution algorithms**: Adaptive Iceberg, TWAP/VWAP/POV, Implementation Shortfall
- **Market microstructure intelligence**: VPIN, queue position estimation, liquidity forecasting
- **Full observability**: Prometheus metrics, OpenTelemetry tracing, structured logging

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 14+ with TimescaleDB extension
- Redis 7+
- Interactive Brokers TWS or Gateway running

### Installation

```bash
# Clone repository
cd "d:\roch\stock\ibkr bot"

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Copy environment template
copy .env.template .env

# Edit .env with your configuration
# CRITICAL: Review all settings, especially IBKR connection and risk limits
```

### Database Setup

```bash
# Install PostgreSQL and TimescaleDB
# Create database and user
createdb ibkr_trading
psql ibkr_trading -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"

# Run migrations
python scripts/db_migration.py
```

### Running

```bash
# Paper trading (SAFE - recommended for testing)
python scripts/run_paper.py

# Backtesting
python scripts/run_backtest.py --config config/backtest.yaml

# Production (DANGEROUS - only after extensive testing)
# NEVER run this without thorough testing and proper risk limits
python scripts/run_production.py
```

## 📊 System Components

### Core Infrastructure
- **Event Loop**: uvloop-based event loop with priority queues
- **Event Bus**: High-performance pub/sub for component communication
- **Configuration**: Pydantic v2 models with YAML support

### Connectivity
- **IBKR Gateway**: Connection management, market data, orders, positions, executions
- **Session Recovery**: Automatic reconnection and state reconciliation

### Market Data
- **Tick Engine**: Tick-by-tick processing with gap detection
- **Bar Aggregator**: Multi-timeframe bar construction
- **Order Book**: Virtual order book reconstruction

### Market Microstructure
- **Flow Toxicity**: VPIN and Hawkes process intensity
- **Queue Position**: Estimate fill probability and time-to-fill
- **Liquidity Forecast**: Short-term volume and spread prediction

### Risk Engine
- **Greeks Engine**: Real-time delta, gamma, vega, theta, vanna, volga
- **VaR**: Multi-horizon Historical/Parametric/Monte Carlo VaR
- **Stress Testing**: Historical scenarios and synthetic shocks
- **Position Limits**: Dynamic liquidity-adjusted limits
- **Pre-trade Checks**: 10+ layer validation cascade
- **Circuit Breakers**: Portfolio/strategy/symbol level kill switches

### Order Management
- **Order Lifecycle**: Complete state machine with reconciliation
- **Parent-Child**: Hierarchical order model
- **Smart Modification**: Race condition handling
- **Shadow Orders**: Sub-millisecond stop/take reaction

### Execution Algorithms
- **Adaptive Iceberg**: Microstructure-aware slice sizing
- **TWAP/VWAP/POV**: Smart participation algorithms
- **Implementation Shortfall**: RL-style aggression scheduling
- **Darkpool Seeking**: ATS liquidity hunting
- **Anti-Gaming**: Randomization to avoid detection

### Strategy Framework
- **Market Making**: Adverse selection aware spread positioning
- **Statistical Arbitrage**: Cointegration with Kalman/particle filters
- **Momentum**: Breakout with microstructure filters
- **Mean Reversion**: Adaptive lookback with optimal execution
- **ML/RL**: Online learning infrastructure
- **HFT Alpha**: Micro-price and order flow signals

### Persistence
- **PostgreSQL + TimescaleDB**: Historical data and state
- **Redis**: Hot-path cache for positions and orders
- **Backup**: Continuous state persistence

### Observability
- **Structured Logging**: JSON logs with correlation IDs
- **Prometheus Metrics**: Latency, throughput, P&L, risk
- **OpenTelemetry**: End-to-end distributed tracing
- **Dashboard**: Real-time monitoring (Grafana)

## 🔒 Safety Features

### Pre-trade Risk Checks
1. Order size sanity (not too large/small)
2. Price collar (near last trade)
3. Position limits (per symbol, sector, geography)
4. Margin requirements
5. Notional/concentration limits
6. Symbol/contract validation
7. Market hours check
8. Strategy-specific rules
9. Kill switch status
10. Rate limiting

### Circuit Breakers
- **Portfolio Level**: Maximum daily loss
- **Strategy Level**: Per-strategy P&L limits
- **Symbol Level**: Excessive loss on single instrument
- **Drawdown**: Maximum drawdown from high-water mark
- **Manual**: Emergency kill switch

### Position Reconciliation
- Automatic reconciliation every 5 minutes
- On reconnect after disconnect
- On demand via script
- Alerts on discrepancies

## 📈 Performance Characteristics

- **Decision to Order Latency**: Sub-millisecond (target <500μs)
- **Event Processing**: 100,000+ events/second
- **Market Data Throughput**: 1M+ ticks/second
- **Order Submission**: <1ms to gateway
- **Risk Calculation**: <100μs for pre-trade checks

## ⚠️ Critical Warnings

### NEVER DO THESE IN PRODUCTION

1. ❌ Run untested strategies with real money
2. ❌ Disable pre-trade risk checks
3. ❌ Trade without position limits
4. ❌ Use market orders blindly
5. ❌ Ignore order rejections
6. ❌ Assume fills (always wait for confirmation)
7. ❌ Run without monitoring/alerting
8. ❌ Skip position reconciliation
9. ❌ Modify risk limits without approval
10. ❌ Trust a single data source

### Regulatory Compliance

- Maintain complete audit trail of all orders (MiFID II, CAT)
- Document best execution
- Implement pre-trade and post-trade controls
- Proper short sale locate/borrow
- Wash sale awareness

## 🧪 Testing

```bash
# Run unit tests
pytest tests/unit -v

# Run integration tests (requires test IBKR account)
pytest tests/integration -v --slow

# Run performance benchmarks
pytest tests/performance -v --benchmark

# Type checking
mypy ibkr_platform

# Linting
ruff check ibkr_platform
```

## 📚 Documentation

- [Architecture Documentation](docs/architecture/)
- [Operations Guide](docs/operations/)
- [Safety Guidelines](docs/safety/)
- [API Reference](docs/api/)

## 🐛 Troubleshooting

### Connection Issues
- Verify TWS/Gateway is running
- Check firewall settings
- Confirm client ID is unique
- Review connection logs

### Data Quality Issues
- Check for stale quotes (timestamp validation)
- Monitor for crossed markets
- Verify contract specifications
- Check for corporate actions

### Order Issues
- Review order rejection logs
- Verify margin requirements
- Check position limits
- Confirm market hours

## 📞 Support

For issues:
1. Check logs in `logs/` directory
2. Review Prometheus metrics at `http://localhost:9090`
3. Check database for historical state
4. Review circuit breaker status

## 📜 License

Proprietary - Internal Use Only

## ⚖️ Disclaimer

**THIS SOFTWARE IS PROVIDED FOR EDUCATIONAL AND RESEARCH PURPOSES ONLY.**

Trading involves substantial risk of loss. This software is provided "as is" without warranty of any kind. The developers and contributors are not responsible for any trading losses incurred while using this software.

**NEVER RISK MORE THAN YOU CAN AFFORD TO LOSE.**

Always paper trade extensively before using any real capital. Understand your strategies completely before deployment. Monitor systems continuously during operation.
