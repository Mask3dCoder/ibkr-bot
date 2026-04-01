"""
Structured logging infrastructure.

Uses structlog for high-performance structured logging with:
- JSON output for production (machine-readable)
- Pretty console output for development (human-readable)
- Correlation ID propagation
- Performance-conscious logging

CRITICAL: Logging is on the hot path - use log levels appropriately.
"""

import logging
import sys
from pathlib import Path
from typing import Any

import structlog
from structlog.types import Processor

from ibkr_platform.core.config import ObservabilityConfig


def setup_logging(config: ObservabilityConfig) -> None:
    """
    Setup structured logging for the platform.
    
    Args:
        config: Observability configuration
    """
    # Create log directory if needed
    if config.log_file:
        config.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, config.log_level.upper()),
    )
    
    # Setup file handler if configured
    if config.log_file:
        file_handler = logging.FileHandler(config.log_file)
        file_handler.setLevel(getattr(logging, config.log_level.upper()))
        logging.root.addHandler(file_handler)
    
    # Define processors based on output format
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
    ]
    
    if config.log_format == "json":
        # JSON output for production
        processors.extend([
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ])
    else:
        # Console output for development
        processors.extend([
            structlog.processors.ExceptionPrettyPrinter(),
            structlog.dev.ConsoleRenderer(colors=True),
        ])
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, config.log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)


# Context management for correlation IDs
def bind_correlation_id(correlation_id: str) -> None:
    """
    Bind correlation ID to context for all subsequent logs.
    
    Args:
        correlation_id: Correlation ID to track related operations
    """
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)


def unbind_correlation_id() -> None:
    """Remove correlation ID from context."""
    structlog.contextvars.unbind_contextvars("correlation_id")


def bind_order_id(order_id: str) -> None:
    """
    Bind order ID to context.
    
    Args:
        order_id: Order ID to track
    """
    structlog.contextvars.bind_contextvars(order_id=order_id)


def bind_strategy_id(strategy_id: str) -> None:
    """
    Bind strategy ID to context.
    
    Args:
        strategy_id: Strategy ID to track
    """
    structlog.contextvars.bind_contextvars(strategy_id=strategy_id)


def clear_context() -> None:
    """Clear all context variables."""
    structlog.contextvars.clear_contextvars()


# Convenience loggers for specific subsystems
def get_trading_logger() -> structlog.BoundLogger:
    """Get logger for trading operations."""
    return get_logger("trading")


def get_risk_logger() -> structlog.BoundLogger:
    """Get logger for risk management."""
    return get_logger("risk")


def get_execution_logger() -> structlog.BoundLogger:
    """Get logger for execution."""
    return get_logger("execution")


def get_market_data_logger() -> structlog.BoundLogger:
    """Get logger for market data."""
    return get_logger("market_data")


def get_strategy_logger() -> structlog.BoundLogger:
    """Get logger for strategies."""
    return get_logger("strategy")


# Performance logging utilities
class LogTimer:
    """
    Context manager for timing operations.
    
    Example:
        with LogTimer(logger, "expensive_operation", symbol="AAPL"):
            # ... expensive operation ...
            pass
    """

    def __init__(self, logger: structlog.BoundLogger, operation: str, **kwargs: Any):
        """
        Initialize timer.
        
        Args:
            logger: Logger instance
            operation: Operation name
            **kwargs: Additional context
        """
        self.logger = logger
        self.operation = operation
        self.context = kwargs
        self.start_ns = 0

    def __enter__(self) -> "LogTimer":
        """Start timer."""
        import time
        self.start_ns = time.perf_counter_ns()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stop timer and log duration."""
        import time
        duration_ns = time.perf_counter_ns() - self.start_ns
        duration_ms = duration_ns / 1_000_000
        
        self.logger.info(
            f"{self.operation}_completed",
            duration_ms=duration_ms,
            duration_ns=duration_ns,
            **self.context,
        )
