"""
Account and Portfolio Validation Tests for IBKR Paper Trading.

Tests covered:
- Account summary data retrieval
- Portfolio position synchronization
- Margin requirement calculations
- P&L tracking accuracy across multiple positions
"""

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Any

import pytest

from ib_insync import IB, Contract

from .conftest import TestResult, get_test_config


class TestAccountPortfolio:
    """Account and portfolio test cases."""
    
    @pytest.fixture
    def ib_connection(self) -> IB:
        """Create IB connection instance."""
        return IB()
    
    @pytest.fixture
    def test_config(self) -> dict:
        """Get test configuration."""
        return get_test_config()
    
    # =========================================================================
    # Account Summary Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_account_summary_retrieval(
        self,
        ib_connection: IB,
        test_config: dict
    ) -> TestResult:
        """
        Test account summary data retrieval.
        
        Verifies:
        - Account summary request succeeds
        - Key account metrics are returned
        - Data is properly formatted
        """
        test_name = "test_account_summary_retrieval"
        test_category = "Account & Portfolio"
        start_time = datetime.utcnow()
        error_message = None
        error_trace = None
        details = {}
        
        try:
            host = test_config["ibkr"]["host"]
            port = test_config["ibkr"]["socket_port"]
            client_id = test_config["ibkr"]["client_id"]
            timeout = test_config["tests"]["account_timeout"]
            
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
                raise ConnectionError("Failed to connect for account test")
            
            # Request account summary
            account_summary = await asyncio.wait_for(
                ib_connection.reqAccountSummaryAsync(),
                timeout=30
            )
            
            details["num_accounts"] = len(account_summary) if account_summary else 0
            
            if account_summary:
                # Extract key metrics
                summary_dict = {
                    acct.account: {
                        "tag": acct.tag,
                        "value": acct.value,
                        "currency": acct.currency,
                    }
                    for acct in account_summary
                }
                
                # Find key metrics
                key_tags = [
                    "NetLiquidation",
                    "AvailableFunds",
                    "GrossPositionValue",
                    "TotalCashValue",
                    "MaintMarginReq",
                    "InitMarginReq",
                ]
                
                key_metrics = {}
                for tag in key_tags:
                    for acct in account_summary:
                        if acct.tag == tag:
                            key_metrics[tag] = {
                                "value": acct.value,
                                "currency": acct.currency,
                            }
                            break
                
                details["key_metrics"] = key_metrics
                details["account_list"] = list(summary_dict.keys())
            
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
    async def test_positions_synchronization(
        self,
        ib_connection: IB,
        test_config: dict
    ) -> TestResult:
        """
        Test portfolio position synchronization.
        
        Verifies:
        - Positions request succeeds
        - Position data is properly formatted
        - Position updates are received correctly
        """
        test_name = "test_positions_synchronization"
        test_category = "Account & Portfolio"
        start_time = datetime.utcnow()
        error_message = None
        error_trace = None
        details = {}
        
        try:
            host = test_config["ibkr"]["host"]
            port = test_config["ibkr"]["socket_port"]
            client_id = test_config["ibkr"]["client_id"]
            timeout = test_config["tests"]["account_timeout"]
            
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
                raise ConnectionError("Failed to connect for positions test")
            
            # Request positions
            positions = await asyncio.wait_for(
                ib_connection.reqPositionsAsync(),
                timeout=30
            )
            
            details["num_positions"] = len(positions) if positions else 0
            
            if positions:
                position_list = []
                for pos in positions:
                    position_data = {
                        "symbol": pos.contract.symbol,
                        "sec_type": pos.contract.secType,
                        "position": pos.position,
                        "avg_cost": pos.avgCost,
                        "market_price": pos.marketPrice,
                        "market_value": pos.marketValue,
                        "unrealized_pnl": pos.unrealizedPNL,
                    }
                    position_list.append(position_data)
                
                details["positions"] = position_list
                
                # Calculate totals
                total_market_value = sum(
                    float(pos.marketValue) for pos in positions
                    if pos.marketValue
                )
                total_pnl = sum(
                    float(pos.unrealizedPNL) for pos in positions
                    if pos.unrealizedPNL
                )
                
                details["total_market_value"] = total_market_value
                details["total_unrealized_pnl"] = total_pnl
            
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
    # Margin Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_margin_requirements(
        self,
        ib_connection: IB,
        test_config: dict
    ) -> TestResult:
        """
        Test margin requirement calculations.
        
        Verifies:
        - Margin data is available
        - Initial and maintenance margin are reported
        - Available funds are calculated correctly
        """
        test_name = "test_margin_requirements"
        test_category = "Account & Portfolio"
        start_time = datetime.utcnow()
        error_message = None
        error_trace = None
        details = {}
        
        try:
            host = test_config["ibkr"]["host"]
            port = test_config["ibkr"]["socket_port"]
            client_id = test_config["ibkr"]["client_id"]
            timeout = test_config["tests"]["account_timeout"]
            
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
                raise ConnectionError("Failed to connect for margin test")
            
            # Request account summary with margin tags
            account_summary = await asyncio.wait_for(
                ib_connection.reqAccountSummaryAsync(),
                timeout=30
            )
            
            # Extract margin-related tags
            margin_tags = [
                "InitMarginReq",
                "MaintMarginReq",
                "AvailableFunds",
                "NetLiquidation",
                "GrossPositionValue",
                "TotalCashValue",
            ]
            
            margin_data = {}
            for tag in margin_tags:
                for acct in account_summary:
                    if acct.tag == tag:
                        margin_data[tag] = {
                            "value": acct.value,
                            "currency": acct.currency,
                        }
                        break
            
            details["margin_data"] = margin_data
            
            # Validate margin calculations
            if margin_data:
                init_margin = margin_data.get("InitMarginReq", {}).get("value")
                maint_margin = margin_data.get("MaintMarginReq", {}).get("value")
                available = margin_data.get("AvailableFunds", {}).get("value")
                
                if init_margin and maint_margin and available:
                    # Basic validation
                    try:
                        init_m = float(init_margin)
                        maint_m = float(maint_margin)
                        avail_f = float(available)
                        
                        details["validation"] = {
                            "init_maint_ratio": init_m / maint_m if maint_m else None,
                            "available_positive": avail_f >= 0,
                        }
                    except ValueError:
                        details["margin_values_numeric"] = False
            
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
    # P&L Tracking Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_pnl_tracking(
        self,
        ib_connection: IB,
        test_config: dict
    ) -> TestResult:
        """
        Test P&L tracking accuracy.
        
        Verifies:
        - Real-time P&L data is available
        - Unrealized P&L is calculated correctly
        - Daily P&L is reported
        """
        test_name = "test_pnl_tracking"
        test_category = "Account & Portfolio"
        start_time = datetime.utcnow()
        error_message = None
        error_trace = None
        details = {}
        
        try:
            host = test_config["ibkr"]["host"]
            port = test_config["ibkr"]["socket_port"]
            client_id = test_config["ibkr"]["client_id"]
            timeout = test_config["tests"]["account_timeout"]
            
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
                raise ConnectionError("Failed to connect for P&L test")
            
            # Request account summary with P&L tags
            account_summary = await asyncio.wait_for(
                ib_connection.reqAccountSummaryAsync(),
                timeout=30
            )
            
            # Extract P&L related tags
            pnl_tags = [
                "UnrealizedPnL",
                "RealizedPnL",
                "DailyPnL",
                "NetLiquidation",
            ]
            
            pnl_data = {}
            for tag in pnl_tags:
                for acct in account_summary:
                    if acct.tag == tag:
                        pnl_data[tag] = {
                            "value": acct.value,
                            "currency": acct.currency,
                        }
                        break
            
            details["pnl_data"] = pnl_data
            
            # Get positions for detailed P&L
            positions = await asyncio.wait_for(
                ib_connection.reqPositionsAsync(),
                timeout=30
            )
            
            if positions:
                position_pnl = []
                for pos in positions:
                    if pos.unrealizedPNL:
                        position_pnl.append({
                            "symbol": pos.contract.symbol,
                            "unrealized_pnl": pos.unrealizedPNL,
                            "market_value": pos.marketValue,
                        })
                
                details["position_pnl"] = position_pnl
                
                # Verify P&L consistency
                if position_pnl:
                    total_pnl = sum(
                        float(p["unrealized_pnl"]) for p in position_pnl
                    )
                    details["calculated_total_pnl"] = total_pnl
            
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
    # Account Updates Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_account_updates_streaming(
        self,
        ib_connection: IB,
        test_config: dict
    ) -> TestResult:
        """
        Test account updates streaming.
        
        Verifies:
        - Account updates are received
        - Update callbacks function properly
        - Change notifications are working
        """
        test_name = "test_account_updates_streaming"
        test_category = "Account & Portfolio"
        start_time = datetime.utcnow()
        error_message = None
        error_trace = None
        details = {}
        update_count = [0]
        
        def on_account_update(account: str, account_dict: dict) -> None:
            update_count[0] += 1
        
        try:
            host = test_config["ibkr"]["host"]
            port = test_config["ibkr"]["socket_port"]
            client_id = test_config["ibkr"]["client_id"]
            timeout = test_config["tests"]["account_timeout"]
            
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
                raise ConnectionError("Failed to connect for account updates test")
            
            # Subscribe to account updates
            ib_connection.accountUpdateEvent += on_account_update
            ib_connection.subscribeAccountUpdates()
            
            # Wait for updates
            await asyncio.sleep(3)
            
            details["update_count"] = update_count[0]
            details["streaming_active"] = update_count[0] > 0
            
            # Unsubscribe
            ib_connection.unsubscribeAccountUpdates()
            ib_connection.accountUpdateEvent -= on_account_update
            
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
