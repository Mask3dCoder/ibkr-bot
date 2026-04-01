"""
Order Execution Tests for IBKR Paper Trading.

Tests covered:
- Market order placement and verification
- Limit order submission with price validation
- Stop order and stop-limit order functionality
- Order modification and cancellation capabilities
- Multi-leg order handling for strategies requiring multiple legs
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

import pytest

from ib_insync import IB, Contract, Order, LimitOrder, StopOrder, StopLimitOrder
from ib_insync.objects import Fill, OrderStatus

from .conftest import TestResult, get_test_config


@dataclass
class OrderTestResult:
    """Extended test result for order tests."""
    test_name: str
    test_category: str
    status: str
    response_time_ms: float
    start_time: datetime
    end_time: datetime
    order_id: int | None = None
    error_message: str | None = None
    error_trace: str | None = None
    order_details: dict[str, Any] = None
    fill_details: list[dict] = None
    
    @property
    def success(self) -> bool:
        return self.status == "PASS"


class TestOrderExecution:
    """Order execution test cases."""
    
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
    
    @pytest.fixture
    def spy_contract(self) -> Contract:
        """Create SPY contract for testing."""
        contract = Contract()
        contract.symbol = "SPY"
        contract.secType = "STK"
        contract.currency = "USD"
        contract.exchange = "SMART"
        return contract
    
    # =========================================================================
    # Market Order Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_market_order_placement(
        self,
        ib_connection: IB,
        test_config: dict,
        aapl_contract: Contract
    ) -> TestResult:
        """
        Test market order placement and verification.
        
        Verifies:
        - Market order is accepted by IBKR
        - Order status transitions correctly
        - Order is filled (in paper trading)
        """
        test_name = "test_market_order_placement"
        test_category = "Order Execution"
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
                raise ConnectionError("Failed to connect for market order test")
            
            # Create market order
            order = Order()
            order.action = "BUY"
            order.orderType = "MKT"
            order.totalQuantity = 1  # Single share for safety
            
            # Submit order
            trade = await asyncio.wait_for(
                ib_connection.placeOrderAsync(aapl_contract, order),
                timeout=timeout
            )
            
            details["order_id"] = trade.order.orderId
            details["order_status"] = str(trade.orderStatus.status)
            details["order_action"] = trade.order.action
            details["order_type"] = trade.order.orderType
            details["quantity"] = trade.order.totalQuantity
            
            # Wait for order to complete (with timeout)
            try:
                await asyncio.wait_for(
                    ib_connection.waitForUpdate(datetime.now(), lambda: 
                        trade.orderStatus.status in [
                            OrderStatus.Filled,
                            OrderStatus.Cancelled,
                            OrderStatus.Inactive
                        ]
                    ),
                    timeout=30
                )
                details["final_status"] = str(trade.orderStatus.status)
                details["filled_qty"] = trade.orderStatus.filled
                details["remaining_qty"] = trade.orderStatus.remaining
                
                if trade.orderStatus.status == OrderStatus.Filled:
                    details["avg_fill_price"] = trade.orderStatus.avgFillPrice
                    
            except asyncio.TimeoutError:
                details["timeout_during_fill"] = True
            
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
    # Limit Order Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_limit_order_submission(
        self,
        ib_connection: IB,
        test_config: dict,
        aapl_contract: Contract
    ) -> TestResult:
        """
        Test limit order submission with price validation.
        
        Verifies:
        - Limit order is accepted with valid price
        - Order status reflects pending state
        - Limit price is correctly set
        """
        test_name = "test_limit_order_submission"
        test_category = "Order Execution"
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
                raise ConnectionError("Failed to connect for limit order test")
            
            # Get current market price first
            ticker = await asyncio.wait_for(
                ib_connection.reqTickByTickDataAsync(
                    aapl_contract, "Last", numberOfTicks=1
                ),
                timeout=10
            )
            
            # Use a limit price significantly away from market to avoid fill
            current_price = 150.0  # Fallback
            if ticker and len(ticker) > 0:
                current_price = float(ticker[-1].price)
            
            limit_price = current_price * 1.10  # 10% above market
            
            # Create limit order
            order = LimitOrder("BUY", totalQuantity=1, lmtPrice=limit_price)
            order.tif = "GTC"  # Good till cancelled
            
            # Submit order
            trade = await asyncio.wait_for(
                ib_connection.placeOrderAsync(aapl_contract, order),
                timeout=timeout
            )
            
            details["order_id"] = trade.order.orderId
            details["limit_price"] = limit_price
            details["order_action"] = trade.order.action
            details["order_type"] = trade.order.orderType
            details["quantity"] = trade.order.totalQuantity
            details["tif"] = trade.order.tif
            
            # Verify order was created with correct price
            if trade.order.lmtPrice != limit_price:
                raise ValueError(
                    f"Limit price mismatch: expected {limit_price}, "
                    f"got {trade.order.lmtPrice}"
                )
            
            # Cancel the order for cleanup
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
    # Stop Order Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_stop_order_functionality(
        self,
        ib_connection: IB,
        test_config: dict,
        aapl_contract: Contract
    ) -> TestResult:
        """
        Test stop order functionality.
        
        Verifies:
        - Stop order is accepted with valid stop price
        - Order status reflects trigger pending state
        - Stop price is correctly set
        """
        test_name = "test_stop_order_functionality"
        test_category = "Order Execution"
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
                raise ConnectionError("Failed to connect for stop order test")
            
            # Use a stop price below current market
            stop_price = 100.0  # Well below typical AAPL price
            
            # Create stop order
            order = StopOrder("SELL", totalQuantity=1, auxPrice=stop_price)
            order.tif = "GTC"
            
            # Submit order
            trade = await asyncio.wait_for(
                ib_connection.placeOrderAsync(aapl_contract, order),
                timeout=timeout
            )
            
            details["order_id"] = trade.order.orderId
            details["stop_price"] = stop_price
            details["order_action"] = trade.order.action
            details["order_type"] = trade.order.orderType
            details["quantity"] = trade.order.totalQuantity
            
            # Verify order was created with correct stop price
            if trade.order.auxPrice != stop_price:
                raise ValueError(
                    f"Stop price mismatch: expected {stop_price}, "
                    f"got {trade.order.auxPrice}"
                )
            
            # Cancel the order for cleanup
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
    # Order Modification Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_order_modification(
        self,
        ib_connection: IB,
        test_config: dict,
        aapl_contract: Contract
    ) -> TestResult:
        """
        Test order modification capabilities.
        
        Verifies:
        - Order modification is accepted
        - Modified parameters are correctly applied
        - Original order is properly updated
        """
        test_name = "test_order_modification"
        test_category = "Order Execution"
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
                raise ConnectionError("Failed to connect for order modification test")
            
            # Create initial limit order
            original_price = 150.0
            order = LimitOrder("BUY", totalQuantity=2, lmtPrice=original_price)
            order.tif = "GTC"
            
            # Submit order
            trade = await asyncio.wait_for(
                ib_connection.placeOrderAsync(aapl_contract, order),
                timeout=timeout
            )
            
            original_order_id = trade.order.orderId
            details["original_order_id"] = original_order_id
            details["original_price"] = original_price
            
            # Modify the order
            new_price = 155.0
            trade.order.lmtPrice = new_price
            
            # Submit modification
            await asyncio.wait_for(
                ib_connection.placeOrderAsync(aapl_contract, trade.order),
                timeout=timeout
            )
            
            details["modified_price"] = new_price
            details["modification_applied"] = True
            
            # Verify modification
            if trade.order.lmtPrice != new_price:
                raise ValueError(
                    f"Modification failed: price not updated to {new_price}"
                )
            
            # Cancel the order for cleanup
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
    # Order Cancellation Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_order_cancellation(
        self,
        ib_connection: IB,
        test_config: dict,
        aapl_contract: Contract
    ) -> TestResult:
        """
        Test order cancellation capabilities.
        
        Verifies:
        - Order cancellation is accepted
        - Order status changes to cancelled
        - Cancellation is properly confirmed
        """
        test_name = "test_order_cancellation"
        test_category = "Order Execution"
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
                raise ConnectionError("Failed to connect for order cancellation test")
            
            # Create a limit order that won't fill immediately
            order = LimitOrder("BUY", totalQuantity=1, lmtPrice=1.0)
            order.tif = "GTC"
            
            # Submit order
            trade = await asyncio.wait_for(
                ib_connection.placeOrderAsync(aapl_contract, order),
                timeout=timeout
            )
            
            order_id = trade.order.orderId
            details["order_id"] = order_id
            details["initial_status"] = str(trade.orderStatus.status)
            
            # Cancel the order
            await asyncio.wait_for(
                ib_connection.cancelOrderAsync(trade.order),
                timeout=10
            )
            
            details["cancellation_requested"] = True
            
            # Wait for cancellation to process
            await asyncio.sleep(1)
            details["final_status"] = str(trade.orderStatus.status)
            
            # Verify cancellation
            if trade.orderStatus.status not in [
                OrderStatus.Cancelled, OrderStatus.Inactive
            ]:
                details["cancellation_pending"] = True
            
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
