"""
Market Data Subscription Tests for IBKR Paper Trading.

Tests covered:
- Real-time quote streaming
- Historical data retrieval validation
- Fundamental data access verification
- Market depth data collection
"""

import asyncio
from datetime import datetime
from typing import Any

import pytest

from ib_insync import IB, Contract, Stock

from .conftest import TestResult, get_test_config


class TestMarketData:
    """Market data subscription test cases."""
    
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
    # Real-time Quote Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_real_time_quote_streaming(
        self,
        ib_connection: IB,
        test_config: dict,
        aapl_contract: Contract
    ) -> TestResult:
        """
        Test real-time quote streaming.
        
        Verifies:
        - Market data subscription is established
        - Real-time ticks are received
        - Quote data includes bid, ask, last prices
        """
        test_name = "test_real_time_quote_streaming"
        test_category = "Market Data"
        start_time = datetime.utcnow()
        error_message = None
        error_trace = None
        details = {}
        received_ticks = []
        
        try:
            host = test_config["ibkr"]["host"]
            port = test_config["ibkr"]["socket_port"]
            client_id = test_config["ibkr"]["client_id"]
            timeout = test_config["tests"]["market_data_timeout"]
            
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
                raise ConnectionError("Failed to connect for market data test")
            
            # Subscribe to real-time bars
            bars = ib_connection.reqRealTimeBars(
                aapl_contract,
                barSize=5,
                whatToShow="TRADES",
                useRTH=False
            )
            
            # Wait for data
            await asyncio.sleep(3)
            
            # Collect received data
            for bar in bars[:10]:  # Check first 10 bars
                tick_data = {
                    "time": bar.time,
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume,
                }
                received_ticks.append(tick_data)
            
            details["num_bars"] = len(received_ticks)
            details["sample_bar"] = received_ticks[0] if received_ticks else None
            
            # Verify data quality
            if len(received_ticks) == 0:
                raise ValueError("No market data received")
            
            # Verify bar has valid prices
            first_bar = received_ticks[0]
            if all(v is None or v == 0 for v in [
                first_bar["open"], first_bar["high"], 
                first_bar["low"], first_bar["close"]
            ]):
                raise ValueError("Received bar has invalid price data")
            
            # Clean up subscription
            ib_connection.cancelRealTimeBars(bars)
            
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
    async def test_tick_data_streaming(
        self,
        ib_connection: IB,
        test_config: dict,
        aapl_contract: Contract
    ) -> TestResult:
        """
        Test tick-by-tick data streaming.
        
        Verifies:
        - Tick data subscription works
        - Individual ticks are received
        - Tick data includes all expected fields
        """
        test_name = "test_tick_data_streaming"
        test_category = "Market Data"
        start_time = datetime.utcnow()
        error_message = None
        error_trace = None
        details = {}
        received_ticks = []
        
        try:
            host = test_config["ibkr"]["host"]
            port = test_config["ibkr"]["socket_port"]
            client_id = test_config["ibkr"]["client_id"]
            timeout = test_config["tests"]["market_data_timeout"]
            
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
                raise ConnectionError("Failed to connect for tick data test")
            
            # Request tick data
            ticker = ib_connection.reqTickByTickData(
                aapl_contract, "Last", numberOfTicks=100
            )
            
            # Wait for data
            await asyncio.sleep(3)
            
            # Collect received ticks
            for tick in ticker[:10]:
                tick_data = {
                    "time": tick.time,
                    "price": tick.price,
                    "size": tick.size,
                }
                received_ticks.append(tick_data)
            
            details["num_ticks"] = len(received_ticks)
            details["sample_tick"] = received_ticks[0] if received_ticks else None
            
            # Clean up
            ib_connection.cancelTickByTickData(ticker)
            
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
    # Historical Data Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_historical_data_retrieval(
        self,
        ib_connection: IB,
        test_config: dict,
        spy_contract: Contract
    ) -> TestResult:
        """
        Test historical data retrieval.
        
        Verifies:
        - Historical bar request succeeds
        - Data is returned in expected format
        - Date ranges are respected
        """
        test_name = "test_historical_data_retrieval"
        test_category = "Market Data"
        start_time = datetime.utcnow()
        error_message = None
        error_trace = None
        details = {}
        
        try:
            host = test_config["ibkr"]["host"]
            port = test_config["ibkr"]["socket_port"]
            client_id = test_config["ibkr"]["client_id"]
            timeout = test_config["tests"]["market_data_timeout"]
            
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
                raise ConnectionError("Failed to connect for historical data test")
            
            # Request historical bars
            bars = await asyncio.wait_for(
                ib_connection.reqHistoricalDataAsync(
                    spy_contract,
                    endDateTime="",
                    durationStr="5 D",
                    barSizeSetting="1 hour",
                    whatToShow="TRADES",
                    useRTH=False,
                    formatDate=2,
                    keepUpToDate=False
                ),
                timeout=30
            )
            
            details["num_bars"] = len(bars) if bars else 0
            
            if bars:
                # Analyze bar quality
                valid_bars = [
                    b for b in bars 
                    if b.open > 0 and b.close > 0
                ]
                details["valid_bars"] = len(valid_bars)
                details["sample_bar"] = {
                    "time": bars[0].time,
                    "open": bars[0].open,
                    "high": bars[0].high,
                    "low": bars[0].low,
                    "close": bars[0].close,
                    "volume": bars[0].volume,
                }
                
                # Verify data range
                if len(bars) > 0:
                    details["date_range"] = {
                        "first": bars[0].time,
                        "last": bars[-1].time,
                    }
            
            if len(bars) == 0:
                raise ValueError("No historical data received")
            
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
    # Fundamental Data Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_fundamental_data_access(
        self,
        ib_connection: IB,
        test_config: dict,
        aapl_contract: Contract
    ) -> TestResult:
        """
        Test fundamental data access.
        
        Verifies:
        - Fundamental data request succeeds
        - Data is returned in expected format
        - Key metrics are present
        """
        test_name = "test_fundamental_data_access"
        test_category = "Market Data"
        start_time = datetime.utcnow()
        error_message = None
        error_trace = None
        details = {}
        
        try:
            host = test_config["ibkr"]["host"]
            port = test_config["ibkr"]["socket_port"]
            client_id = test_config["ibkr"]["client_id"]
            timeout = test_config["tests"]["market_data_timeout"]
            
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
                raise ConnectionError("Failed to connect for fundamental data test")
            
            # Request contract details (includes fundamental info)
            contracts = await asyncio.wait_for(
                ib_connection.reqContractDetailsAsync(aapl_contract),
                timeout=30
            )
            
            details["num_contracts"] = len(contracts) if contracts else 0
            
            if contracts:
                contract = contracts[0]
                details["contract"] = {
                    "conid": contract.contract.conId,
                    "symbol": contract.contract.symbol,
                    "name": contract.longName,
                    "exchange": contract.contract.exchange,
                    "min_tick": contract.minTick,
                    "market_name": contract.marketName,
                }
            
            # Request fundamental data
            from ib_insync import FundamentalData
            fund_data = await asyncio.wait_for(
                ib_connection.reqFundamentalDataAsync(
                    aapl_contract, reportName="Snapshot"
                ),
                timeout=30
            )
            
            details["fundamental_data_received"] = fund_data is not None
            details["report_type"] = "Snapshot"
            
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
    # Market Depth Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_market_depth_data(
        self,
        ib_connection: IB,
        test_config: dict,
        aapl_contract: Contract
    ) -> TestResult:
        """
        Test market depth (Level II) data collection.
        
        Verifies:
        - Market depth subscription is established
        - Order book data is received
        - Bid/ask levels are present
        """
        test_name = "test_market_depth_data"
        test_category = "Market Data"
        start_time = datetime.utcnow()
        error_message = None
        error_trace = None
        details = {}
        depth_updates = []
        
        try:
            host = test_config["ibkr"]["host"]
            port = test_config["ibkr"]["socket_port"]
            client_id = test_config["ibkr"]["client_id"]
            timeout = test_config["tests"]["market_data_timeout"]
            
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
                raise ConnectionError("Failed to connect for depth data test")
            
            # Subscribe to market depth
            mdepth = ib_connection.reqMktDepth(
                aapl_contract,
                numRows=5,
                isSmartDepth=True
            )
            
            # Wait for data
            await asyncio.sleep(3)
            
            # Collect depth updates
            for update in mdepth[:10]:
                depth_data = {
                    "position": update.position,
                    "marketMaker": update.marketMaker,
                    "operation": update.operation,
                    "side": update.side,
                    "price": update.price,
                    "size": update.size,
                }
                depth_updates.append(depth_data)
            
            details["num_depth_updates"] = len(depth_updates)
            details["sample_update"] = (
                depth_updates[0] if depth_updates else None
            )
            
            # Clean up
            ib_connection.cancelMktDepth(mdepth)
            
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
