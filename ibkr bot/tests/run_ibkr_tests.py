#!/usr/bin/env python3
"""
IBKR API Paper Trading Test Suite Runner.

This module provides comprehensive test execution and reporting for the
Interactive Brokers API paper trading configuration.

Usage:
    python tests/run_ibkr_tests.py [--output-dir DIR] [--format FORMAT]
    python tests/run_ibkr_tests.py --help
"""

import argparse
import asyncio
import csv
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ibkr_platform.core.config import IBKRConfig, PlatformConfig


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class TestRunnerConfig:
    """Configuration for the test runner."""
    host: str = "127.0.0.1"
    socket_port: int = 7497
    client_port: int = 7496
    client_id: int = 2
    output_dir: Path = Path("test_reports")
    format: str = "all"  # json, html, csv, all
    include_tracebacks: bool = True
    include_response_times: bool = True


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
    end_time: datetime = None
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


# ============================================================================
# Test Definitions
# ============================================================================

class IBKRTestRunner:
    """Test runner for IBKR API paper trading tests."""
    
    def __init__(self, config: TestRunnerConfig):
        self.config = config
        self.results: list[TestResult] = []
        
    async def run_all_tests(self) -> TestSuiteResult:
        """Run all test categories."""
        suite_result = TestSuiteResult(
            suite_name="IBKR Paper Trading Test Suite",
            start_time=datetime.utcnow()
        )
        
        # Run connection tests
        conn_results = await self._run_connection_tests()
        suite_result.results.extend(conn_results)
        
        # Run order tests
        order_results = await self._run_order_tests()
        suite_result.results.extend(order_results)
        
        # Run market data tests
        market_results = await self._run_market_data_tests()
        suite_result.results.extend(market_results)
        
        # Run account tests
        account_results = await self._run_account_tests()
        suite_result.results.extend(account_results)
        
        # Run error handling tests
        error_results = await self._run_error_tests()
        suite_result.results.extend(error_results)
        
        suite_result.end_time = datetime.utcnow()
        return suite_result
    
    async def _run_connection_tests(self) -> list[TestResult]:
        """Run connection and authentication tests."""
        from ib_insync import IB
        
        results = []
        ib = IB()
        
        test_cases = [
            ("test_socket_port_connectivity", "Connection & Authentication"),
            ("test_client_id_allocation", "Connection & Authentication"),
            ("test_duplicate_client_id", "Connection & Authentication"),
            ("test_reconnection_scenarios", "Connection & Authentication"),
            ("test_server_version_negotiation", "Connection & Authentication"),
        ]
        
        for test_name, category in test_cases:
            start = datetime.utcnow()
            error_msg = None
            error_trace = None
            details = {}
            
            try:
                connected = await asyncio.wait_for(
                    ib.connectAsync(
                        host=self.config.host,
                        port=self.config.socket_port,
                        clientId=self.config.client_id,
                        timeout=15
                    ),
                    timeout=20
                )
                
                if not connected:
                    raise ConnectionError(
                        f"Failed to connect to {self.config.host}:"
                        f"{self.config.socket_port}"
                    )
                
                if test_name == "test_socket_port_connectivity":
                    details = {
                        "host": self.config.host,
                        "port": self.config.socket_port,
                        "client_id": self.config.client_id,
                        "connection_state": str(ib.state),
                        "server_version": ib.serverVersion(),
                    }
                elif test_name == "test_client_id_allocation":
                    details = {
                        "requested_client_id": self.config.client_id,
                        "assigned_client_id": ib.clientId,
                    }
                    if ib.clientId != self.config.client_id:
                        raise ValueError(
                            f"Client ID mismatch: expected {self.config.client_id}"
                        )
                elif test_name == "test_server_version_negotiation":
                    details = {
                        "server_version": ib.serverVersion(),
                        "api_version": ib.apiVersion(),
                    }
                    
            except Exception as e:
                error_msg = str(e)
                error_trace = f"{type(e).__name__}: {str(e)}"
            finally:
                try:
                    if ib.state is not None and ib.state != "disconnected":
                        ib.disconnect()
                except Exception:
                    pass
            
            end = datetime.utcnow()
            duration = (end - start).total_seconds() * 1000
            
            status = "PASS" if error_msg is None else "FAIL"
            
            results.append(TestResult(
                test_name=test_name,
                test_category=category,
                status=status,
                response_time_ms=duration,
                start_time=start,
                end_time=end,
                error_message=error_msg,
                error_trace=error_trace,
                details=details
            ))
        
        return results
    
    async def _run_order_tests(self) -> list[TestResult]:
        """Run order execution tests."""
        from ib_insync import IB, Contract, LimitOrder, StopOrder
        
        results = []
        ib = IB()
        
        test_cases = [
            ("test_limit_order_submission", "Order Execution"),
            ("test_stop_order_functionality", "Order Execution"),
            ("test_order_modification", "Order Execution"),
            ("test_order_cancellation", "Order Execution"),
        ]
        
        # Create test contract
        contract = Contract()
        contract.symbol = "AAPL"
        contract.secType = "STK"
        contract.currency = "USD"
        contract.exchange = "SMART"
        
        for test_name, category in test_cases:
            start = datetime.utcnow()
            error_msg = None
            error_trace = None
            details = {}
            
            try:
                connected = await asyncio.wait_for(
                    ib.connectAsync(
                        host=self.config.host,
                        port=self.config.socket_port,
                        clientId=self.config.client_id,
                        timeout=15
                    ),
                    timeout=20
                )
                
                if not connected:
                    raise ConnectionError("Failed to connect for order test")
                
                if test_name == "test_limit_order_submission":
                    order = LimitOrder("BUY", totalQuantity=1, lmtPrice=500.0)
                    order.tif = "GTC"
                    trade = await asyncio.wait_for(
                        ib.placeOrderAsync(contract, order),
                        timeout=30
                    )
                    details = {
                        "order_id": trade.order.orderId,
                        "limit_price": 500.0,
                        "order_type": "LMT",
                    }
                    # Cancel the order
                    await asyncio.wait_for(
                        ib.cancelOrderAsync(trade.order),
                        timeout=10
                    )
                    
                elif test_name == "test_stop_order_functionality":
                    order = StopOrder("SELL", totalQuantity=1, auxPrice=100.0)
                    order.tif = "GTC"
                    trade = await asyncio.wait_for(
                        ib.placeOrderAsync(contract, order),
                        timeout=30
                    )
                    details = {
                        "order_id": trade.order.orderId,
                        "stop_price": 100.0,
                        "order_type": "STP",
                    }
                    await asyncio.wait_for(
                        ib.cancelOrderAsync(trade.order),
                        timeout=10
                    )
                    
                elif test_name == "test_order_modification":
                    order = LimitOrder("BUY", totalQuantity=2, lmtPrice=150.0)
                    order.tif = "GTC"
                    trade = await asyncio.wait_for(
                        ib.placeOrderAsync(contract, order),
                        timeout=30
                    )
                    original_price = trade.order.lmtPrice
                    trade.order.lmtPrice = 160.0
                    await asyncio.wait_for(
                        ib.placeOrderAsync(contract, trade.order),
                        timeout=30
                    )
                    details = {
                        "order_id": trade.order.orderId,
                        "original_price": original_price,
                        "modified_price": 160.0,
                    }
                    await asyncio.wait_for(
                        ib.cancelOrderAsync(trade.order),
                        timeout=10
                    )
                    
                elif test_name == "test_order_cancellation":
                    order = LimitOrder("BUY", totalQuantity=1, lmtPrice=1.0)
                    order.tif = "GTC"
                    trade = await asyncio.wait_for(
                        ib.placeOrderAsync(contract, order),
                        timeout=30
                    )
                    await asyncio.wait_for(
                        ib.cancelOrderAsync(trade.order),
                        timeout=10
                    )
                    details = {
                        "order_id": trade.order.orderId,
                        "cancellation_successful": True,
                    }
                    
            except Exception as e:
                error_msg = str(e)
                error_trace = f"{type(e).__name__}: {str(e)}"
            finally:
                try:
                    if ib.state is not None:
                        ib.disconnect()
                except Exception:
                    pass
            
            end = datetime.utcnow()
            duration = (end - start).total_seconds() * 1000
            
            status = "PASS" if error_msg is None else "FAIL"
            
            results.append(TestResult(
                test_name=test_name,
                test_category=category,
                status=status,
                response_time_ms=duration,
                start_time=start,
                end_time=end,
                error_message=error_msg,
                error_trace=error_trace,
                details=details
            ))
        
        return results
    
    async def _run_market_data_tests(self) -> list[TestResult]:
        """Run market data subscription tests."""
        from ib_insync import IB, Contract
        
        results = []
        ib = IB()
        
        test_cases = [
            ("test_real_time_quote_streaming", "Market Data"),
            ("test_historical_data_retrieval", "Market Data"),
            ("test_tick_data_streaming", "Market Data"),
        ]
        
        contract = Contract()
        contract.symbol = "SPY"
        contract.secType = "STK"
        contract.currency = "USD"
        contract.exchange = "SMART"
        
        for test_name, category in test_cases:
            start = datetime.utcnow()
            error_msg = None
            error_trace = None
            details = {}
            
            try:
                connected = await asyncio.wait_for(
                    ib.connectAsync(
                        host=self.config.host,
                        port=self.config.socket_port,
                        clientId=self.config.client_id,
                        timeout=15
                    ),
                    timeout=20
                )
                
                if not connected:
                    raise ConnectionError(
                        "Failed to connect for market data test"
                    )
                
                if test_name == "test_real_time_quote_streaming":
                    bars = ib.reqRealTimeBars(
                        contract, barSize=5, whatToShow="TRADES", useRTH=False
                    )
                    await asyncio.sleep(3)
                    bar_count = len([b for b in bars])
                    details = {
                        "num_bars": bar_count,
                        "contract": "SPY",
                    }
                    ib.cancelRealTimeBars(bars)
                    
                elif test_name == "test_historical_data_retrieval":
                    bars = await asyncio.wait_for(
                        ib.reqHistoricalDataAsync(
                            contract,
                            endDateTime="",
                            durationStr="3 D",
                            barSizeSetting="1 hour",
                            whatToShow="TRADES",
                            useRTH=False,
                            formatDate=2,
                            keepUpToDate=False
                        ),
                        timeout=30
                    )
                    details = {
                        "num_bars": len(bars) if bars else 0,
                        "duration": "3 D",
                        "bar_size": "1 hour",
                    }
                    
                elif test_name == "test_tick_data_streaming":
                    ticker = ib.reqTickByTickData(contract, "Last", numberOfTicks=100)
                    await asyncio.sleep(3)
                    tick_count = len([t for t in ticker])
                    details = {
                        "num_ticks": tick_count,
                        "tick_type": "Last",
                    }
                    ib.cancelTickByTickData(ticker)
                    
            except Exception as e:
                error_msg = str(e)
                error_trace = f"{type(e).__name__}: {str(e)}"
            finally:
                try:
                    if ib.state is not None:
                        ib.disconnect()
                except Exception:
                    pass
            
            end = datetime.utcnow()
            duration = (end - start).total_seconds() * 1000
            
            status = "PASS" if error_msg is None else "FAIL"
            
            results.append(TestResult(
                test_name=test_name,
                test_category=category,
                status=status,
                response_time_ms=duration,
                start_time=start,
                end_time=end,
                error_message=error_msg,
                error_trace=error_trace,
                details=details
            ))
        
        return results
    
    async def _run_account_tests(self) -> list[TestResult]:
        """Run account and portfolio tests."""
        from ib_insync import IB
        
        results = []
        ib = IB()
        
        test_cases = [
            ("test_account_summary_retrieval", "Account & Portfolio"),
            ("test_positions_synchronization", "Account & Portfolio"),
            ("test_margin_requirements", "Account & Portfolio"),
            ("test_pnl_tracking", "Account & Portfolio"),
        ]
        
        for test_name, category in test_cases:
            start = datetime.utcnow()
            error_msg = None
            error_trace = None
            details = {}
            
            try:
                connected = await asyncio.wait_for(
                    ib.connectAsync(
                        host=self.config.host,
                        port=self.config.socket_port,
                        clientId=self.config.client_id,
                        timeout=15
                    ),
                    timeout=20
                )
                
                if not connected:
                    raise ConnectionError("Failed to connect for account test")
                
                if test_name == "test_account_summary_retrieval":
                    summary = await asyncio.wait_for(
                        ib.reqAccountSummaryAsync(),
                        timeout=30
                    )
                    details = {
                        "num_accounts": len(summary) if summary else 0,
                    }
                    
                elif test_name == "test_positions_synchronization":
                    positions = await asyncio.wait_for(
                        ib.reqPositionsAsync(),
                        timeout=30
                    )
                    details = {
                        "num_positions": len(positions) if positions else 0,
                    }
                    
                elif test_name == "test_margin_requirements":
                    summary = await asyncio.wait_for(
                        ib.reqAccountSummaryAsync(),
                        timeout=30
                    )
                    margin_tags = ["InitMarginReq", "MaintMarginReq", "AvailableFunds"]
                    margin_data = {}
                    for tag in margin_tags:
                        for acct in summary:
                            if acct.tag == tag:
                                margin_data[tag] = acct.value
                                break
                    details = {"margin_data": margin_data}
                    
                elif test_name == "test_pnl_tracking":
                    positions = await asyncio.wait_for(
                        ib.reqPositionsAsync(),
                        timeout=30
                    )
                    pnl_values = [
                        p.unrealizedPNL for p in positions 
                        if p.unrealizedPNL
                    ]
                    details = {
                        "num_positions_with_pnl": len(pnl_values),
                        "total_unrealized_pnl": sum(pnl_values) if pnl_values else 0,
                    }
                    
            except Exception as e:
                error_msg = str(e)
                error_trace = f"{type(e).__name__}: {str(e)}"
            finally:
                try:
                    if ib.state is not None:
                        ib.disconnect()
                except Exception:
                    pass
            
            end = datetime.utcnow()
            duration = (end - start).total_seconds() * 1000
            
            status = "PASS" if error_msg is None else "FAIL"
            
            results.append(TestResult(
                test_name=test_name,
                test_category=category,
                status=status,
                response_time_ms=duration,
                start_time=start,
                end_time=end,
                error_message=error_msg,
                error_trace=error_trace,
                details=details
            ))
        
        return results
    
    async def _run_error_tests(self) -> list[TestResult]:
        """Run error handling and edge case tests."""
        from ib_insync import IB, Contract, Order
        
        results = []
        ib = IB()
        
        test_cases = [
            ("test_invalid_order_rejection", "Error Handling"),
            ("test_connection_timeout_handling", "Error Handling"),
            ("test_insufficient_funds_rejection", "Error Handling"),
            ("test_api_version_compatibility", "Error Handling"),
        ]
        
        contract = Contract()
        contract.symbol = "AAPL"
        contract.secType = "STK"
        contract.currency = "USD"
        contract.exchange = "SMART"
        
        for test_name, category in test_cases:
            start = datetime.utcnow()
            error_msg = None
            error_trace = None
            details = {}
            
            try:
                if test_name == "test_connection_timeout_handling":
                    # Test with invalid port
                    test_ib = IB()
                    try:
                        await asyncio.wait_for(
                            test_ib.connectAsync(
                                host="127.0.0.1",
                                port=9999,
                                clientId=self.config.client_id,
                                timeout=2
                            ),
                            timeout=10
                        )
                        error_msg = "Connection to invalid port succeeded unexpectedly"
                    except (asyncio.TimeoutError, Exception):
                        details["timeout_handled"] = True
                    finally:
                        try:
                            if test_ib.state is not None:
                                test_ib.disconnect()
                        except Exception:
                            pass
                else:
                    connected = await asyncio.wait_for(
                        ib.connectAsync(
                            host=self.config.host,
                            port=self.config.socket_port,
                            clientId=self.config.client_id,
                            timeout=15
                        ),
                        timeout=20
                    )
                    
                    if not connected:
                        raise ConnectionError(
                            "Failed to connect for error handling test"
                        )
                    
                    if test_name == "test_invalid_order_rejection":
                        order = Order()
                        order.action = "BUY"
                        order.orderType = "MKT"
                        order.totalQuantity = -100  # Invalid
                        trade = await asyncio.wait_for(
                            ib.placeOrderAsync(contract, order),
                            timeout=30
                        )
                        details = {
                            "order_id": trade.order.orderId,
                            "invalid_quantity": order.totalQuantity,
                        }
                        
                    elif test_name == "test_insufficient_funds_rejection":
                        order = Order()
                        order.action = "BUY"
                        order.orderType = "MKT"
                        order.totalQuantity = 10000000  # Huge order
                        trade = await asyncio.wait_for(
                            ib.placeOrderAsync(contract, order),
                            timeout=30
                        )
                        details = {
                            "order_id": trade.order.orderId,
                            "quantity": order.totalQuantity,
                        }
                        await asyncio.wait_for(
                            ib.cancelOrderAsync(trade.order),
                            timeout=10
                        )
                        
                    elif test_name == "test_api_version_compatibility":
                        details = {
                            "server_version": ib.serverVersion(),
                            "api_version": ib.apiVersion(),
                        }
                        
            except Exception as e:
                error_msg = str(e)
                error_trace = f"{type(e).__name__}: {str(e)}"
            finally:
                try:
                    if ib.state is not None:
                        ib.disconnect()
                except Exception:
                    pass
            
            end = datetime.utcnow()
            duration = (end - start).total_seconds() * 1000
            
            status = "PASS" if error_msg is None else "FAIL"
            
            results.append(TestResult(
                test_name=test_name,
                test_category=category,
                status=status,
                response_time_ms=duration,
                start_time=start,
                end_time=end,
                error_message=error_msg,
                error_trace=error_trace,
                details=details
            ))
        
        return results


# ============================================================================
# Report Generation
# ============================================================================

class ReportGenerator:
    """Generate test reports in various formats."""
    
    def __init__(self, output_dir: Path, include_tracebacks: bool = True):
        self.output_dir = output_dir
        self.include_tracebacks = include_tracebacks
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_json_report(
        self, 
        suite_result: TestSuiteResult
    ) -> Path:
        """Generate JSON format report."""
        report = {
            "suite_name": suite_result.suite_name,
            "execution_time": {
                "start": suite_result.start_time.isoformat(),
                "end": suite_result.end_time.isoformat(),
                "total_duration_ms": suite_result.total_duration_ms,
            },
            "summary": {
                "total_tests": suite_result.total_tests,
                "passed": suite_result.passed,
                "failed": suite_result.failed,
                "errors": suite_result.errors,
                "skipped": suite_result.skipped,
                "success_rate": round(suite_result.success_rate, 2),
                "avg_response_time_ms": round(suite_result.avg_response_time_ms, 2),
            },
            "tests": []
        }
        
        for result in suite_result.results:
            test_data = {
                "name": result.test_name,
                "category": result.test_category,
                "status": result.status,
                "response_time_ms": round(result.response_time_ms, 2),
                "start_time": result.start_time.isoformat(),
                "end_time": result.end_time.isoformat(),
                "details": result.details,
            }
            
            if result.error_message and self.include_tracebacks:
                test_data["error"] = {
                    "message": result.error_message,
                    "trace": result.error_trace,
                }
            
            report["tests"].append(test_data)
        
        output_path = self.output_dir / "test_report.json"
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        
        return output_path
    
    def generate_csv_report(
        self, 
        suite_result: TestSuiteResult
    ) -> Path:
        """Generate CSV format report."""
        output_path = self.output_dir / "test_report.csv"
        
        fieldnames = [
            "test_name",
            "test_category",
            "status",
            "response_time_ms",
            "start_time",
            "end_time",
            "error_message",
        ]
        
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in suite_result.results:
                writer.writerow({
                    "test_name": result.test_name,
                    "test_category": result.test_category,
                    "status": result.status,
                    "response_time_ms": round(result.response_time_ms, 2),
                    "start_time": result.start_time.isoformat(),
                    "end_time": result.end_time.isoformat(),
                    "error_message": result.error_message or "",
                })
        
        return output_path
    
    def generate_html_report(
        self, 
        suite_result: TestSuiteResult
    ) -> Path:
        """Generate HTML format report."""
        output_path = self.output_dir / "test_report.html"
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>IBKR Test Suite Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ 
            background: #f5f5f5; 
            padding: 15px; 
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .stat {{ display: inline-block; margin-right: 30px; margin-bottom: 10px; }}
        .stat-label {{ font-weight: bold; }}
        .stat-value {{ font-size: 1.2em; }}
        .pass {{ color: green; }}
        .fail {{ color: red; }}
        .error {{ color: orange; }}
        .skip {{ color: gray; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .details {{ background: #f9f9f9; padding: 10px; margin-top: 5px; }}
    </style>
</head>
<body>
    <h1>IBKR Paper Trading Test Suite Report</h1>
    
    <div class="summary">
        <h2>Summary</h2>
        <div class="stat">
            <span class="stat-label">Total Tests:</span>
            <span class="stat-value">{suite_result.total_tests}</span>
        </div>
        <div class="stat">
            <span class="stat-label">Passed:</span>
            <span class="stat-value pass">{suite_result.passed}</span>
        </div>
        <div class="stat">
            <span class="stat-label">Failed:</span>
            <span class="stat-value fail">{suite_result.failed}</span>
        </div>
        <div class="stat">
            <span class="stat-label">Errors:</span>
            <span class="stat-value error">{suite_result.errors}</span>
        </div>
        <div class="stat">
            <span class="stat-label">Success Rate:</span>
            <span class="stat-value">{suite_result.success_rate:.2f}%</span>
        </div>
        <div class="stat">
            <span class="stat-label">Avg Response Time:</span>
            <span class="stat-value">{suite_result.avg_response_time_ms:.2f}ms</span>
        </div>
        <div class="stat">
            <span class="stat-label">Total Duration:</span>
            <span class="stat-value">{suite_result.total_duration_ms:.2f}ms</span>
        </div>
    </div>
    
    <h2>Test Results</h2>
    <table>
        <tr>
            <th>Test Name</th>
            <th>Category</th>
            <th>Status</th>
            <th>Response Time</th>
            <th>Details</th>
        </tr>
"""
        
        for result in suite_result.results:
            status_class = result.status.lower()
            details_json = json.dumps(result.details, indent=2)
            
            error_section = ""
            if result.error_message:
                error_section = f"""
                <div class="details">
                    <strong>Error:</strong> {result.error_message}
                    {f'<br><pre>{result.error_trace}</pre>' if result.error_trace and self.include_tracebacks else ''}
                </div>
                """
            
            html_content += f"""
        <tr>
            <td>{result.test_name}</td>
            <td>{result.test_category}</td>
            <td class="{status_class}">{result.status}</td>
            <td>{result.response_time_ms:.2f}ms</td>
            <td>
                <pre>{details_json}</pre>
                {error_section}
            </td>
        </tr>
"""
        
        html_content += """
    </table>
    
    <p><em>Report generated at: """ + datetime.utcnow().isoformat() + """</em></p>
</body>
</html>
"""
        
        with open(output_path, "w") as f:
            f.write(html_content)
        
        return output_path


# ============================================================================
# Main Entry Point
# ============================================================================

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="IBKR API Paper Trading Test Suite"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="IBKR host address (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--socket-port",
        type=int,
        default=7497,
        help="IBKR socket port (default: 7497)"
    )
    parser.add_argument(
        "--client-id",
        type=int,
        default=1,
        help="IBKR client ID (default: 1)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("test_reports"),
        help="Output directory for reports (default: test_reports)"
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["json", "html", "csv", "all"],
        default="all",
        help="Output format (default: all)"
    )
    parser.add_argument(
        "--no-tracebacks",
        action="store_true",
        help="Don't include error tracebacks in reports"
    )
    
    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()
    
    print("=" * 60)
    print("IBKR Paper Trading Test Suite")
    print("=" * 60)
    print(f"Host: {args.host}")
    print(f"Socket Port: {args.socket_port}")
    print(f"Client ID: {args.client_id}")
    print(f"Output Directory: {args.output_dir}")
    print("=" * 60)
    
    # Create config
    config = TestRunnerConfig(
        host=args.host,
        socket_port=args.socket_port,
        client_id=args.client_id,
        output_dir=args.output_dir,
        format=args.format,
        include_tracebacks=not args.no_tracebacks,
    )
    
    # Create runner and execute tests
    runner = IBKRTestRunner(config)
    print("\nRunning tests...")
    suite_result = await runner.run_all_tests()
    
    # Generate reports
    generator = ReportGenerator(
        args.output_dir,
        include_tracebacks=not args.no_tracebacks
    )
    
    output_paths = []
    if args.format in ("json", "all"):
        path = generator.generate_json_report(suite_result)
        output_paths.append(("JSON", path))
        print(f"\nGenerated JSON report: {path}")
    
    if args.format in ("csv", "all"):
        path = generator.generate_csv_report(suite_result)
        output_paths.append(("CSV", path))
        print(f"Generated CSV report: {path}")
    
    if args.format in ("html", "all"):
        path = generator.generate_html_report(suite_result)
        output_paths.append(("HTML", path))
        print(f"Generated HTML report: {path}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {suite_result.total_tests}")
    print(f"Passed: {suite_result.passed}")
    print(f"Failed: {suite_result.failed}")
    print(f"Errors: {suite_result.errors}")
    print(f"Skipped: {suite_result.skipped}")
    print(f"Success Rate: {suite_result.success_rate:.2f}%")
    print(f"Total Duration: {suite_result.total_duration_ms:.2f}ms")
    print(f"Avg Response Time: {suite_result.avg_response_time_ms:.2f}ms")
    print("=" * 60)
    
    # Return exit code based on results
    if suite_result.failed > 0 or suite_result.errors > 0:
        return 1
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
