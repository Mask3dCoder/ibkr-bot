"""
IBKR API Paper Trading Test Suite Configuration.

This module provides configuration for the comprehensive test suite including:
- Test connection parameters
- Test fixtures and utilities
- Report generation settings
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import json


# ============================================================================
# Test Configuration
# ============================================================================

TEST_CONFIG = {
    # IBKR Connection Parameters
    "ibkr": {
        "host": "127.0.0.1",
        "socket_port": 7497,      # IB Gateway/TWS socket connections
        "client_port": 7496,      # API client connection
        "client_id": 2,
        "account": None,  # Will be fetched during tests
        "timeout": 30,
        "max_reconnect_attempts": 5,
        "reconnect_delay": 2,
    },
    
    # Test Settings
    "tests": {
        "connection_timeout": 15,
        "order_timeout": 30,
        "market_data_timeout": 10,
        "account_timeout": 15,
        "max_retries": 3,
        "retry_delay": 1,
    },
    
    # Report Settings
    "reports": {
        "output_dir": Path("test_reports"),
        "generate_html": True,
        "generate_json": True,
        "generate_csv": True,
        "include_tracebacks": True,
        "include_response_times": True,
    },
    
    # Test Securities (Paper trading safe securities)
    "test_securities": {
        "stocks": ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"],
        "etfs": ["SPY", "QQQ", "IWM", "VTI"],
        "forex": ["EUR.USD", "GBP.USD", "USD.JPY"],
    },
}


@dataclass
class TestResult:
    """Individual test result."""
    test_name: str
    test_category: str
    status: str  # PASS, FAIL, ERROR, SKIP
    response_time_ms: float
    start_time: datetime
    end_time: datetime
    error_message: str | None = None
    error_trace: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    
    @property
    def success(self) -> bool:
        return self.status == "PASS"


@dataclass
class TestSuiteResult:
    """Aggregate test suite results."""
    suite_name: str
    start_time: datetime
    end_time: datetime
    results: list[TestResult] = field(default_factory=list)
    
    @property
    def total_tests(self) -> int:
        return len(self.results)
    
    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.success)
    
    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.status == "FAIL")
    
    @property
    def errors(self) -> int:
        return sum(1 for r in self.results if r.status == "ERROR")
    
    @property
    def skipped(self) -> int:
        return sum(1 for r in self.results if r.status == "SKIP")
    
    @property
    def success_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return (self.passed / self.total_tests) * 100
    
    @property
    def total_duration_ms(self) -> float:
        return sum(r.response_time_ms for r in self.results)
    
    @property
    def avg_response_time_ms(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return self.total_duration_ms / self.total_tests


def get_test_config() -> dict:
    """Get test configuration."""
    return TEST_CONFIG


def validate_test_config() -> tuple[bool, list[str]]:
    """
    Validate test configuration.
    
    Returns:
        Tuple of (is_valid, list of errors)
    """
    errors = []
    
    # Validate IBKR connection parameters
    host = TEST_CONFIG["ibkr"]["host"]
    if not host:
        errors.append("IBKR host must be specified")
    
    socket_port = TEST_CONFIG["ibkr"]["socket_port"]
    client_port = TEST_CONFIG["ibkr"]["client_port"]
    valid_ports = {4001, 4002, 7496, 7497}
    
    if socket_port not in valid_ports:
        errors.append(f"Invalid socket port {socket_port}. Must be one of: {valid_ports}")
    
    if client_port not in valid_ports:
        errors.append(f"Invalid client port {client_port}. Must be one of: {valid_ports}")
    
    client_id = TEST_CONFIG["ibkr"]["client_id"]
    if not isinstance(client_id, int) or client_id < 0:
        errors.append(f"Invalid client ID {client_id}. Must be a non-negative integer")
    
    # Validate test settings
    timeout = TEST_CONFIG["tests"]["connection_timeout"]
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        errors.append(f"Invalid connection timeout {timeout}. Must be positive")
    
    return len(errors) == 0, errors
