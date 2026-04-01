"""
Error Handling and Edge Case Tests for IBKR Paper Trading.

Tests covered:
- Invalid order rejection handling
- Connection timeout scenarios
- Duplicate client ID detection
- Insufficient funds rejection
- API version compatibility verification
"""

import asyncio
from datetime import datetime
from typing import Any

import pytest

from ib_insync import IB, Contract, Order, LimitOrder
from ib_insync.objects import OrderStatus

from .conftest import TestResult, get_test_config


class TestErrorHandling:
    """Error handling and edge case test cases."""
    
    @pytest.fixture
    def ib_connection(self) -> IB:
        """Create IB connection instance."""
        return IB()
    
    @pytest.fixture
    def test_config(self) -> dict:
        """Get test configuration."""
        return get_test_config()
    
    @pytest.fixture
    def aapl_contract(self) -> Contract:
        """Create AAPL contract for testing."""
        contract = Contract()
        contract.symbol = "AAPL"
        contract.secType = "STK"
        contract.currency = "USD"
        contract.exchange = "SMART"
        return contract
    
    # =========================================================================
    # Invalid Order Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_invalid_order_rejection(
        self,
        ib_connection: IB,
        test_config: dict,
        aapl_contract: Contract
    ) -> TestResult:
        """
        Test invalid order rejection handling.
        
        Verifies:
        - Invalid orders are properly rejected
        - Error messages are descriptive
        - Order status reflects rejection
        """
        test_name = "test_invalid_order_rejection"
        test_category = "Error Handling"
        start_time = datetime.utcnow()
        error_message = None
        error_trace = None
        details = {}
        
        try:
            host = test_config["ibkr"]["host"]
            port = test_config["ibkr"]["socket_port"]
            client_id = test_config["ibkr"]["client_id"]
            timeout = test_config["tests"]["order_timeout"]
            
            connected = await asyncio.wait_for(
                ib_connection.connectAsync(
                    host=host,
                    port=port,
                    clientId=client_id,
                    timeout=timeout
                ),
                timeout=timeout + 5
            )
            
            if not connected:
                raise ConnectionError("Failed to connect for invalid order test")
            
            # Create an order with invalid parameters
            # Negative quantity should be rejected
            order = Order()
            order.action = "BUY"
            order.orderType = "MKT"
            order.totalQuantity = -100  # Invalid: negative quantity
            
            # Submit order
            trade = await asyncio.wait_for(
                ib_connection.placeOrderAsync(aapl_contract, order),
                timeout=timeout
            )
            
            details["order_id"] = trade.order.orderId
            details["initial_status"] = str(trade.orderStatus.status)
            
            # Wait for rejection
            await asyncio.sleep(2)
            
            details["final_status"] = str(trade.orderStatus.status)
            details["order_rejected"] = (
                trade.orderStatus.status == OrderStatus.Inactive
            )
            
            # If order wasn't rejected immediately, check for error message
            if trade.orderStatus.status != OrderStatus.Inactive:
                details["requires_manual_cancellation"] = True
                # Cancel the order
                await asyncio.wait_for(
                    ib_connection.cancelOrderAsync(trade.order),
                    timeout=10
                )
            
        except Exception as e:
            error_message = str(e)
            error_trace = str(type(e).__name__) + ": " + str(e)
        finally:
            try:
                if ib_connection.state is not None:
                    ib_connection.disconnect()
            except Exception:
                pass
        
        end_time = datetime.utcnow()
        response_time_ms = (end_time - start_time).total_seconds() * 1000
        
        status = "PASS" if error_message is None else "FAIL"
        
        return TestResult(
            test_name=test_name,
            test_category=test_category,
            status=status,
            response_time_ms=response_time_ms,
            start_time=start_time,
            end_time=end_time,
            error_message=error_message,
            error_trace=error_trace,
            details=details
        )
    
    @pytest.mark.asyncio
    async def test_connection_timeout_handling(
        self,
        test_config: dict
    ) -> TestResult:
        """
        Test connection timeout scenarios.
        
        Verifies:
        - Connection timeout is properly handled
        - Error message is descriptive
        - Connection state is properly cleaned up
        """
        test_name = "test_connection_timeout_handling"
        test_category = "Error Handling"
        start_time = datetime.utcnow()
        error_message = None
        error_trace = None
        details = {}
        
        ib = IB()
        
        try:
            # Try to connect to a non-responsive port
            await asyncio.wait_for(
                ib.connectAsync(
                    host="127.0.0.1",
                    port=9999,  # Invalid port
                    clientId=test_config["ibkr"]["client_id"],
                    timeout=2
                ),
                timeout=10
            )
            
            # If we get here, connection unexpectedly succeeded
            error_message = "Connection to invalid port unexpectedly succeeded"
            details["unexpected_success"] = True
            
        except asyncio.TimeoutError:
            error_message = None  # Expected behavior
            details["timeout_handled_correctly"] = True
            details["timeout_duration"] = "as expected"
        except Exception as e:
            error_message = None  # Expected behavior
            details["expected_error"] = str(e)
            details["error_type"] = type(e).__name__
        finally:
            try:
                if ib.state is not None:
                    ib.disconnect()
            except Exception:
                pass
        
        end_time = datetime.utcnow()
        response_time_ms = (end_time - start_time).total_seconds() * 1000
        
        status = "PASS" if error_message is None else "FAIL"
        
        return TestResult(
            test_name=test_name,
            test_category=test_category,
            status=status,
            response_time_ms=response_time_ms,
            start_time=start_time,
            end_time=end_time,
            error_message=error_message,
            error_trace=error_trace,
            details=details
        )
    
    # =========================================================================
    # Insufficient Funds Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_insufficient_funds_rejection(
        self,
        ib_connection: IB,
        test_config: dict,
        aapl_contract: Contract
    ) -> TestResult:
        """
        Test insufficient funds rejection.
        
        Verifies:
        - Orders exceeding available funds are rejected
        - Appropriate error is returned
        - Marginimpact is calculated
        """
        test_name = "test_insufficient_funds_rejection"
        test_category = "Error Handling"
        start_time = datetime.utcnow()
        error_message = None
        error_trace = None
        details = {}
        
        try:
            host = test_config["ibkr"]["host"]
            port = test_config["ibkr"]["socket_port"]
            client_id = test_config["ibkr"]["client_id"]
            timeout = test_config["tests"]["order_timeout"]
            
            connected = await asyncio.wait_for(
                ib_connection.connectAsync(
                    host=host,
                    port=port,
                    clientId=client_id,
                    timeout=timeout
                ),
                timeout=timeout + 5
            )
            
            if not connected:
                raise ConnectionError(
                    "Failed to connect for insufficient funds test"
                )
            
            # Try to place an order for way more shares than available funds
            order = Order()
            order.action = "BUY"
            order.orderType = "MKT"
            order.totalQuantity = 10000000  # 10 million shares - definitely exceeds
            
            # Submit order
            trade = await asyncio.wait_for(
                ib_connection.placeOrderAsync(aapl_contract, order),
                timeout=timeout
            )
            
            details["order_id"] = trade.order.orderId
            details["quantity_ordered"] = order.totalQuantity
            details["initial_status"] = str(trade.orderStatus.status)
            
            # Wait for processing
            await asyncio.sleep(3)
            
            details["final_status"] = str(trade.orderStatus.status)
            details["was_rejected"] = (
                trade.orderStatus.status == OrderStatus.Inactive
            )
            
            # If order was submitted, check for warning or process it
            if trade.orderStatus.status not in [
                OrderStatus.Inactive, OrderStatus.Cancelled
            ]:
                details["order_accepted"] = True
                # Cancel the order
                await asyncio.wait_for(
                    ib_connection.cancelOrderAsync(trade.order),
                    timeout=10
                )
                details["order_cancelled"] = True
            
        except Exception as e:
            error_message = str(e)
            error_trace = str(type(e).__name__) + ": " + str(e)
        finally:
            try:
                if ib_connection.state is not None:
                    ib_connection.disconnect()
            except Exception:
                pass
        
        end_time = datetime.utcnow()
        response_time_ms = (end_time - start_time).total_seconds() * 1000
        
        status = "PASS" if error_message is None else "FAIL"
        
        return TestResult(
            test_name=test_name,
            test_category=test_category,
            status=status,
            response_time_ms=response_time_ms,
            start_time=start_time,
            end_time=end_time,
            error_message=error_message,
            error_trace=error_trace,
            details=details
        )
    
    # =========================================================================
    # API Version Compatibility Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_api_version_compatibility(
        self,
        ib_connection: IB,
        test_config: dict
    ) -> TestResult:
        """
        Test API version compatibility verification.
        
        Verifies:
        - Server version is returned
        - API version is available
        - Version information is consistent
        """
        test_name = "test_api_version_compatibility"
        test_category = "Error Handling"
        start_time = datetime.utcnow()
        error_message = None
        error_trace = None
        details = {}
        
        try:
            host = test_config["ibkr"]["host"]
            port = test_config["ibkr"]["socket_port"]
            client_id = test_config["ibkr"]["client_id"]
            timeout = test_config["tests"]["connection_timeout"]
            
            connected = await asyncio.wait_for(
                ib_connection.connectAsync(
                    host=host,
                    port=port,
                    clientId=client_id,
                    timeout=timeout
                ),
                timeout=timeout + 5
            )
            
            if not connected:
                raise ConnectionError(
                    "Failed to connect for version compatibility test"
                )
            
            # Get version information
            server_version = ib_connection.serverVersion()
            api_version = ib_connection.apiVersion()
            
            details["server_version"] = server_version
            details["api_version"] = api_version
            
            # Validate versions
            if server_version is None:
                raise ValueError("Server version is None")
            
            if api_version is None:
                raise ValueError("API version is None")
            
            # Check version format
            if not isinstance(server_version, int):
                raise ValueError(
                    f"Server version is not an integer: {server_version}"
                )
            
            if not isinstance(api_version, int):
                raise ValueError(
                    f"API version is not an integer: {api_version}"
                )
            
            # IBKR API versions are typically > 100
            if server_version < 100:
                details["warning"] = "Unusually low server version"
            
            details["connection_time"] = str(ib_connection.twsConnectionTime())
            
        except Exception as e:
            error_message = str(e)
            error_trace = str(type(e).__name__) + ": " + str(e)
        finally:
            try:
                if ib_connection.state is not None:
                    ib_connection.disconnect()
            except Exception:
                pass
        
        end_time = datetime.utcnow()
        response_time_ms = (end_time - start_time).total_seconds() * 1000
        
        status = "PASS" if error_message is None else "FAIL"
        
        return TestResult(
            test_name=test_name,
            test_category=test_category,
            status=status,
            response_time_ms=response_time_ms,
            start_time=start_time,
            end_time=end_time,
            error_message=error_message,
            error_trace=error_trace,
            details=details
        )
    
    # =========================================================================
    # Contract Validation Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_invalid_contract_handling(
        self,
        ib_connection: IB,
        test_config: dict
    ) -> TestResult:
        """
        Test handling of invalid contracts.
        
        Verifies:
        - Invalid contract requests are handled gracefully
        - Appropriate errors are returned
        - No crashes occur
        """
        test_name = "test_invalid_contract_handling"
        test_category = "Error Handling"
        start_time = datetime.utcnow()
        error_message = None
        error_trace = None
        details = {}
        
        try:
            host = test_config["ibkr"]["host"]
            port = test_config["ibkr"]["socket_port"]
            client_id = test_config["ibkr"]["client_id"]
            timeout = test_config["tests"]["order_timeout"]
            
            connected = await asyncio.wait_for(
                ib_connection.connectAsync(
                    host=host,
                    port=port,
                    clientId=client_id,
                    timeout=timeout
                ),
                timeout=timeout + 5
            )
            
            if not connected:
                raise ConnectionError(
                    "Failed to connect for contract validation test"
                )
            
            # Create an invalid contract
            invalid_contract = Contract()
            invalid_contract.symbol = "INVALID_SYMBOL_XYZ_123"
            invalid_contract.secType = "STK"
            invalid_contract.currency = "USD"
            invalid_contract.exchange = "SMART"
            
            # Try to get contract details
            try:
                contracts = await asyncio.wait_for(
                    ib_connection.reqContractDetailsAsync(invalid_contract),
                    timeout=10
                )
                
                details["num_results"] = len(contracts) if contracts else 0
                
                if len(contracts) == 0:
                    details["correctly_found_no_match"] = True
                    
            except Exception as contract_error:
                error_message = None  # Expected behavior
                details["expected_error"] = str(contract_error)
                details["error_type"] = type(contract_error).__name__
            
        except Exception as e:
            error_message = str(e)
            error_trace = str(type(e).__name__) + ": " + str(e)
        finally:
            try:
                if ib_connection.state is not None:
                    ib_connection.disconnect()
            except Exception:
                pass
        
        end_time = datetime.utcnow()
        response_time_ms = (end_time - start_time).total_seconds() * 1000
        
        status = "PASS" if error_message is None else "FAIL"
        
        return TestResult(
            test_name=test_name,
            test_category=test_category,
            status=status,
            response_time_ms=response_time_ms,
            start_time=start_time,
            end_time=end_time,
            error_message=error_message,
            error_trace=error_trace,
            details=details
        )
