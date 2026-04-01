"""
Configuration management using Pydantic v2.

Loads configuration from YAML files with environment variable substitution
and strict validation. Follows the 12-factor app methodology.

Configuration hierarchy:
1. Default values in Pydantic models
2. YAML configuration files
3. Environment variables (highest priority)

CRITICAL: All sensitive data (passwords, API keys) must come from env vars.
"""

import os
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal, Optional

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def load_yaml_config(config_path: Path) -> dict[str, Any]:
    """
    Load YAML configuration file with environment variable substitution.
    
    Args:
        config_path: Path to YAML file
        
    Returns:
        Parsed configuration dictionary
    """
    if not config_path.exists():
        return {}
    
    with open(config_path) as f:
        content = f.read()
        # Simple environment variable substitution: ${VAR_NAME}
        import re
        def replace_env_var(match: re.Match[str]) -> str:
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))
        
        content = re.sub(r'\$\{([^}]+)\}', replace_env_var, content)
        return yaml.safe_load(content) or {}


class IBKRConfig(BaseSettings):
    """IBKR connection configuration."""

    model_config = SettingsConfigDict(env_prefix="IBKR_")

    host: str = "127.0.0.1"
    port: int = 7497  # Paper trading port
    client_id: int = 2
    account: Optional[str] = None
    readonly: bool = True  # Safety: default to read-only
    
    # Connection parameters
    timeout: int = 30
    max_reconnect_attempts: int = 10
    reconnect_delay: int = 5  # seconds
    
    # Market data
    enable_delayed_data: bool = False
    
    @field_validator("port")
    def validate_port(cls, v: int) -> int:
        """Validate IBKR port."""
        valid_ports = {4001, 4002, 7496, 7497}
        if v not in valid_ports:
            raise ValueError(
                f"Invalid IBKR port {v}. Must be one of: {valid_ports}\n"
                f"7497=TWS Paper, 7496=TWS Live, 4002=Gateway Paper, 4001=Gateway Live"
            )
        return v


class DatabaseConfig(BaseSettings):
    """Database configuration."""

    model_config = SettingsConfigDict(env_prefix="DB_")

    host: str = "localhost"
    port: int = 5432
    name: str = "ibkr_trading"
    user: str = "trading_user"
    password: str = Field(default="", description="Database password (from env)")
    
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    
    # TimescaleDB
    timescale_chunk_time_interval: str = "1d"
    
    @property
    def url(self) -> str:
        """Build async PostgreSQL connection URL."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class RedisConfig(BaseSettings):
    """Redis configuration."""

    model_config = SettingsConfigDict(env_prefix="REDIS_")

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 50
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    
    @property
    def url(self) -> str:
        """Build Redis connection URL."""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class ObservabilityConfig(BaseSettings):
    """Observability configuration."""

    model_config = SettingsConfigDict(env_prefix="")

    # Logging
    log_level: str = "INFO"
    log_format: Literal["json", "console"] = "json"
    log_file: Optional[Path] = Path("logs/trading.log")
    
    # Prometheus
    prometheus_port: int = 9090
    prometheus_enabled: bool = True
    
    # OpenTelemetry
    otel_enabled: bool = True
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "ibkr-trading-platform"


class RiskConfig(BaseSettings):
    """Risk management configuration."""

    model_config = SettingsConfigDict(env_prefix="")

    # Kill switches
    global_kill_switch: bool = False
    
    # P&L limits (USD)
    max_daily_loss: Decimal = Decimal("10000")
    max_daily_profit: Optional[Decimal] = None  # Optional profit target
    max_drawdown_from_high: Decimal = Decimal("20000")
    
    # Position limits (USD)
    max_position_value: Decimal = Decimal("100000")
    max_gross_exposure: Decimal = Decimal("500000")
    max_net_exposure: Decimal = Decimal("250000")
    
    # Order limits (USD)
    max_order_value: Decimal = Decimal("50000")
    max_order_quantity: int = 10000
    
    # Concentration limits (% of portfolio)
    max_symbol_concentration: Decimal = Decimal("0.20")  # 20%
    max_sector_concentration: Decimal = Decimal("0.40")  # 40%
    
    # Rate limits
    max_orders_per_second: int = 10
    max_orders_per_minute: int = 100
    
    @field_validator("global_kill_switch")
    def check_kill_switch(cls, v: bool) -> bool:
        """Log warning if kill switch is active."""
        if v:
            import logging
            logging.warning("⚠️  GLOBAL KILL SWITCH IS ACTIVE - ALL TRADING HALTED")
        return v


class ExecutionConfig(BaseSettings):
    """Execution configuration."""

    model_config = SettingsConfigDict(env_prefix="")

    enable_execution_algos: bool = True
    default_exec_algo: Literal["simple", "iceberg", "twap", "vwap", "shortfall"] = "simple"
    
    # Execution algo parameters
    iceberg_min_slice_pct: Decimal = Decimal("0.05")  # Min 5% of total order
    iceberg_max_slice_pct: Decimal = Decimal("0.30")  # Max 30% of total order
    
    twap_num_slices: int = 10
    twap_randomize_timing: bool = True
    twap_timing_jitter_pct: Decimal = Decimal("0.20")  # 20% jitter
    
    vwap_use_historical_profile: bool = True
    vwap_lookback_days: int = 20
    vwap_min_participation: Decimal = Decimal("0.05")  # 5%
    vwap_max_participation: Decimal = Decimal("0.30")  # 30%


class StrategyConfig(BaseSettings):
    """Strategy framework configuration."""

    model_config = SettingsConfigDict(env_prefix="")

    active_strategies: list[str] = Field(default_factory=list)
    enable_hot_reload: bool = False
    strategy_config_dir: Path = Path("config/strategies")
    
    # Resource limits per strategy
    max_cpu_percent: int = 50
    max_memory_mb: int = 1024


class SimulationConfig(BaseSettings):
    """Simulation configuration."""

    model_config = SettingsConfigDict(env_prefix="")

    paper_trading: bool = True  # Default to paper trading for safety
    backtest_mode: bool = False
    backtest_start_date: Optional[str] = None
    backtest_end_date: Optional[str] = None
    
    # Realistic simulation parameters
    fill_latency_ms: int = 5
    partial_fill_probability: Decimal = Decimal("0.10")
    commission_per_share: Decimal = Decimal("0.005")
    min_commission: Decimal = Decimal("1.00")


class PerformanceConfig(BaseSettings):
    """Performance tuning configuration."""

    model_config = SettingsConfigDict(env_prefix="")

    use_uvloop: bool = True
    worker_threads: int = 4
    event_queue_size: int = 10000
    
    # Memory management
    cache_size_mb: int = 512
    max_tick_buffer_size: int = 100000


class AlertConfig(BaseSettings):
    """Alert configuration."""

    model_config = SettingsConfigDict(env_prefix="ALERT_")

    # Webhook
    webhook_url: Optional[str] = None
    
    # Email
    email_enabled: bool = False
    email_from: Optional[str] = None
    email_to: Optional[str] = None
    email_smtp_host: Optional[str] = None
    email_smtp_port: int = 587


class PlatformConfig(BaseSettings):
    """
    Main platform configuration.
    
    Aggregates all subsystem configurations.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Subsystem configs
    ibkr: IBKRConfig = Field(default_factory=IBKRConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    strategy: StrategyConfig = Field(default_factory=StrategyConfig)
    simulation: SimulationConfig = Field(default_factory=SimulationConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    alert: AlertConfig = Field(default_factory=AlertConfig)

    @classmethod
    def from_yaml(cls, config_path: Path | str) -> "PlatformConfig":
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to YAML configuration file
            
        Returns:
            PlatformConfig instance
        """
        config_path = Path(config_path)
        yaml_config = load_yaml_config(config_path)
        return cls(**yaml_config)

    def validate_for_production(self) -> None:
        """
        Validate configuration for production use.
        
        Raises:
            ValueError: If configuration is unsafe for production
        """
        errors = []
        
        # Check IBKR readonly mode
        if not self.ibkr.readonly and self.simulation.paper_trading:
            errors.append(
                "⚠️  WARNING: IBKR readonly=False but paper_trading=True. "
                "This will execute real orders! Set readonly=True for safety."
            )
        
        # Check live vs paper port
        if self.ibkr.port in {4001, 7496} and self.simulation.paper_trading:
            errors.append(
                f"⚠️  WARNING: IBKR port {self.ibkr.port} is LIVE but paper_trading=True. "
                "Change to paper port (7497 or 4002) or set paper_trading=False."
            )
        
        # Check database password
        if not self.database.password:
            errors.append("⚠️  WARNING: Database password is empty.")
        
        # Check risk limits
        if self.risk.max_daily_loss <= 0:
            errors.append("⚠️  CRITICAL: max_daily_loss must be > 0")
        
        if self.risk.max_position_value <= 0:
            errors.append("⚠️  CRITICAL: max_position_value must be > 0")
        
        # Check kill switch
        if self.risk.global_kill_switch:
            errors.append("ℹ️  INFO: Global kill switch is ACTIVE - all trading halted")
        
        if errors:
            error_msg = "\n".join(errors)
            raise ValueError(f"Production configuration validation failed:\n{error_msg}")

    def validate_for_paper_trading(self) -> None:
        """
        Validate configuration for paper trading.
        
        Raises:
            ValueError: If configuration is incorrect for paper trading
        """
        errors = []
        
        # Ensure paper trading is enabled
        if not self.simulation.paper_trading:
            errors.append("⚠️  WARNING: paper_trading should be True for paper trading mode")
        
        # Check port is paper port
        if self.ibkr.port not in {4002, 7497}:
            errors.append(
                f"⚠️  WARNING: IBKR port {self.ibkr.port} is not a paper trading port. "
                "Use 7497 (TWS Paper) or 4002 (Gateway Paper)"
            )
        
        if errors:
            error_msg = "\n".join(errors)
            print(f"Paper trading configuration warnings:\n{error_msg}")


# Singleton config instance
_config: Optional[PlatformConfig] = None


def get_config() -> PlatformConfig:
    """
    Get global configuration instance.
    
    Returns:
        PlatformConfig singleton
    """
    global _config
    if _config is None:
        _config = PlatformConfig()
    return _config


def load_config(config_path: Path | str | None = None) -> PlatformConfig:
    """
    Load configuration from YAML file or environment.
    
    Args:
        config_path: Optional path to YAML config file
        
    Returns:
        PlatformConfig instance
    """
    global _config
    if config_path:
        _config = PlatformConfig.from_yaml(config_path)
    else:
        _config = PlatformConfig()
    return _config
