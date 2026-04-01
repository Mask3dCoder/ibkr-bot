-- Initialize TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    order_id UUID PRIMARY KEY,
    client_order_id VARCHAR(50) UNIQUE NOT NULL,
    broker_order_id BIGINT,
    parent_order_id UUID REFERENCES orders(order_id),
    
    -- Contract
    symbol VARCHAR(20) NOT NULL,
    asset_class VARCHAR(10) NOT NULL,
    exchange VARCHAR(20),
    
    -- Order details
    side VARCHAR(4) NOT NULL,
    order_type VARCHAR(20) NOT NULL,
    quantity DECIMAL(18, 8) NOT NULL,
    filled_quantity DECIMAL(18, 8) DEFAULT 0,
    
    -- Pricing
    limit_price DECIMAL(18, 8),
    stop_price DECIMAL(18, 8),
    avg_fill_price DECIMAL(18, 8),
    
    -- Status
    status VARCHAR(20) NOT NULL,
    status_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    submitted_at TIMESTAMPTZ,
    acknowledged_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    -- Attribution
    strategy_id VARCHAR(50),
    account VARCHAR(50),
    
    -- Metadata
    metadata JSONB
);

CREATE INDEX idx_orders_symbol ON orders(symbol);
CREATE INDEX idx_orders_strategy ON orders(strategy_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);

-- Executions table
CREATE TABLE IF NOT EXISTS executions (
    execution_id VARCHAR(50) PRIMARY KEY,
    order_id UUID NOT NULL REFERENCES orders(order_id),
    broker_order_id BIGINT NOT NULL,
    
    -- Contract
    symbol VARCHAR(20) NOT NULL,
    
    -- Execution details
    side VARCHAR(4) NOT NULL,
    quantity DECIMAL(18, 8) NOT NULL,
    price DECIMAL(18, 8) NOT NULL,
    
    -- Costs
    commission DECIMAL(18, 8) DEFAULT 0,
    realized_pnl DECIMAL(18, 8),
    
    -- Timestamp
    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Attribution
    strategy_id VARCHAR(50),
    account VARCHAR(50),
    exchange VARCHAR(20)
);

CREATE INDEX idx_executions_symbol ON executions(symbol);
CREATE INDEX idx_executions_order_id ON executions(order_id);
CREATE INDEX idx_executions_executed_at ON executions(executed_at DESC);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('executions', 'executed_at', if_not_exists => TRUE);

-- Positions table
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    account VARCHAR(50) NOT NULL,
    
    -- Position
    quantity DECIMAL(18, 8) NOT NULL,
    avg_cost DECIMAL(18, 8) NOT NULL,
    
    -- P&L
    realized_pnl DECIMAL(18, 8) DEFAULT 0,
    unrealized_pnl DECIMAL(18, 8),
    
    -- Market data
    last_price DECIMAL(18, 8),
    market_value DECIMAL(18, 8),
    
    -- Attribution
    strategy_id VARCHAR(50),
    
    -- Timestamps
    opened_at TIMESTAMPTZ,
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(symbol, account, strategy_id)
);

CREATE INDEX idx_positions_symbol ON positions(symbol);
CREATE INDEX idx_positions_account ON positions(account);
CREATE INDEX idx_positions_strategy ON positions(strategy_id);

-- Market data - ticks
CREATE TABLE IF NOT EXISTS ticks (
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    
    -- Price data
    bid DECIMAL(18, 8),
    ask DECIMAL(18, 8),
    last DECIMAL(18, 8),
    
    -- Size data
    bid_size INTEGER,
    ask_size INTEGER,
    last_size INTEGER,
    volume BIGINT,
    
    -- Flags
    is_trade BOOLEAN DEFAULT FALSE,
    is_quote BOOLEAN DEFAULT FALSE
);

SELECT create_hypertable('ticks', 'timestamp', if_not_exists => TRUE);
CREATE INDEX idx_ticks_symbol_time ON ticks(symbol, timestamp DESC);

-- Market data - bars
CREATE TABLE IF NOT EXISTS bars (
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    
    -- OHLCV
    open DECIMAL(18, 8) NOT NULL,
    high DECIMAL(18, 8) NOT NULL,
    low DECIMAL(18, 8) NOT NULL,
    close DECIMAL(18, 8) NOT NULL,
    volume BIGINT NOT NULL,
    
    -- Additional
    vwap DECIMAL(18, 8),
    trade_count INTEGER,
    
    is_complete BOOLEAN DEFAULT TRUE
);

SELECT create_hypertable('bars', 'timestamp', if_not_exists => TRUE);
CREATE INDEX idx_bars_symbol_time ON bars(symbol, timeframe, timestamp DESC);

-- Risk metrics
CREATE TABLE IF NOT EXISTS risk_metrics (
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- P&L
    realized_pnl DECIMAL(18, 8) DEFAULT 0,
    unrealized_pnl DECIMAL(18, 8) DEFAULT 0,
    total_pnl DECIMAL(18, 8) DEFAULT 0,
    
    -- Exposure
    gross_exposure DECIMAL(18, 8) DEFAULT 0,
    net_exposure DECIMAL(18, 8) DEFAULT 0,
    
    -- Greeks
    delta DECIMAL(18, 8),
    gamma DECIMAL(18, 8),
    vega DECIMAL(18, 8),
    theta DECIMAL(18, 8),
    
    -- VaR
    var_1min DECIMAL(18, 8),
    var_5min DECIMAL(18, 8),
    var_30min DECIMAL(18, 8),
    var_daily DECIMAL(18, 8),
    
    -- Margin
    margin_used DECIMAL(18, 8),
    margin_available DECIMAL(18, 8),
    
    -- Attribution
    strategy_id VARCHAR(50),
    account VARCHAR(50)
);

SELECT create_hypertable('risk_metrics', 'timestamp', if_not_exists => TRUE);
CREATE INDEX idx_risk_metrics_strategy ON risk_metrics(strategy_id, timestamp DESC);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trading_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO trading_user;
