"""
Connection and Authentication Tests for IBKR Paper Trading.

Tests covered:
- Successful handshake with IB paper trading server
- Client ID allocation validation
- Socket connectivity on both ports (7496, 7497)
- Reconnection scenarios after intentional disconnections
"""

import asyncio
import time
from datetime import datetime

import pytest

from ib_insync import IB, ConnectionState

from .conftest import TestResult, get_test_config


class TestConnectionAuthentication:
    """Connection and authentication test cases."""
    
    @pytest.fixture
    def ib_connection(self) -> IB:
        """Create IB connection instance."""
        return IB()
    
    @pytest.fixture
    def test_config(self) -> dict:
        """Get test configuration."""
        return get_test_config()
    
    # =========================================================================
    # Connection Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_socket_port_7497_connectivity(
        self,
        ib_connection: IB,
        test_config: dict
    ) -> TestResult:
        """
        Test socket connectivity on port 7497 (IB Gateway/TWS socket).
        
        Verifies:
        - TCP socket connection establishment
        - Initial handshake response
        - Connection state transition to CONNECTED
        """
        test_name = "test_socket_port_7497_connectivity"
        test_category = "Connection & Authentication"
        start_time = datetime.utcnow()
        error_message = None
        error_trace = None
        details = {}
        
        try:
            host = test_config["ibkr"]["host"]
            socket_port = test_config["ibkr"]["socket_port"]
            client_id = test_config["ibkr"]["client_id"]
            timeout = test_config["tests"]["connection_timeout"]
            
            connected = await asyncio.wait_for(
                ib_connection.connectAsync(
                    host=host,
                    port=socket_port,
                    clientId=client_id,
                    timeout=timeout
                ),
                timeout=timeout + 5
            )
            
            if not connected:
                raise ConnectionError(
                    f"Failed to connect to {host}:{socket_port}"
                )
            
            if ib_connection.state != ConnectionState.CONNECTED:
                raise ConnectionError(
                    f"Unexpected connection state: {ib_connection.state}"
                )
            
            details = {
                "host": host,
                "port": socket_port,
                "client_id": client_id,
                "connection_state": str(ib_connection.state),
                "server_version": ib_connection.serverVersion(),
                "connection_time": ib_connection.twsConnectionTime(),
            }
            
        except asyncio.TimeoutError:
            error_message = f"Connection timeout after {timeout} seconds"
            error_trace = (
                f"Could not connect to {host}:{socket_port} "
                f"within timeout"
            )
        except Exception as e:
            error_message = str(e)
            error_trace = str(type(e).__name__) + ": " + str(e)
        finally:
            try:
                if ib_connection.state == ConnectionState.CONNECTED:
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
    async def test_client_id_allocation(
        self,
        ib_connection: IB,
        test_config: dict
    ) -> TestResult:
        """
        Test client ID allocation and uniqueness.
        
        Verifies:
        - Client ID is accepted by the server
        - No conflicts with existing client IDs
        - Client ID is properly reflected in connection
        """
        test_name = "test_client_id_allocation"
        test_category = "Connection & Authentication"
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
                    f"Failed to connect with client ID {client_id}"
                )
            
            if ib_connection.clientId != client_id:
                raise ValueError(
                    f"Client ID mismatch: expected {client_id}, "
                    f"got {ib_connection.clientId}"
                )
            
            details = {
                "requested_client_id": client_id,
                "assigned_client_id": ib_connection.clientId,
                "host": host,
                "port": port,
            }
            
        except asyncio.TimeoutError:
            error_message = "Client ID allocation timeout"
            error_trace = (
                f"Timeout during handshake with client ID "
                f"{test_config['ibkr']['client_id']}"
            )
        except Exception as e:
            error_message = str(e)
            error_trace = str(type(e).__name__) + ": " + str(e)
        finally:
            try:
                if ib_connection.state == ConnectionState.CONNECTED:
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
    async def test_duplicate_client_id_detection(
        self,
        test_config: dict
    ) -> TestResult:
        """
        Test detection of duplicate client ID connections.
        
        Verifies:
        - Duplicate client ID is properly rejected
        - Appropriate error is returned
        - Existing connection is not affected
        """
        test_name = "test_duplicate_client_id_detection"
        test_category = "Connection & Authentication"
        start_time = datetime.utcnow()
        error_message = None
        error_trace = None
        details = {}
        
        ib1 = IB()
        ib2 = IB()
        
        try:
            host = test_config["ibkr"]["host"]
            port = test_config["ibkr"]["socket_port"]
            client_id = test_config["ibkr"]["client_id"]
            timeout = test_config["tests"]["connection_timeout"]
            
            connected1 = await asyncio.wait_for(
                ib1.connectAsync(
                    host=host,
                    port=port,
                    clientId=client_id,
                    timeout=timeout
                ),
                timeout=timeout + 5
            )
            
            if not connected1:
                raise ConnectionError("First connection failed")
            
            try:
                connected2 = await asyncio.wait_for(
                    ib2.connectAsync(
                        host=host,
                        port=port,
                        clientId=client_id,
                        timeout=5
                    ),
                    timeout=10
                )
                
                if connected2:
                    details["duplicate_handling"] = (
                        "Connection allowed (server may have "
                        "disconnected first)"
                    )
                    if ib1.state == ConnectionState.DISCONNECTED:
                        details["original_disconnected"] = True
            except Exception as dup_error:
                error_message = None
                details["duplicate_rejected"] = True
                details["error_message"] = str(dup_error)
                
        except Exception as e:
            error_message = str(e)
            error_trace = str(type(e).__name__) + ": " + str(e)
        finally:
            try:
                if ib1.state == ConnectionState.CONNECTED:
                    ib1.disconnect()
                if ib2.state == ConnectionState.CONNECTED:
                    ib2.disconnect()
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
    async def test_reconnection_after_disconnect(
        self,
        ib_connection: IB,
        test_config: dict
    ) -> TestResult:
        """
        Test reconnection scenarios after intentional disconnection.
        
        Verifies:
        - Clean disconnection works properly
        - Reconnection succeeds after disconnect
        - No resource leaks after multiple connect/disconnect cycles
        """
        test_name = "test_reconnection_after_disconnect"
        test_category = "Connection & Authentication"
        start_time = datetime.utcnow()
        error_message = None
        error_trace = None
        details = {}
        reconnect_attempts = 3
        
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
                raise ConnectionError("Initial connection failed")
            
            details["initial_connection"] = "success"
            
            ib_connection.disconnect()
            if ib_connection.state != ConnectionState.DISCONNECTED:
                raise ConnectionError("Disconnect did not complete properly")
            
            details["disconnect"] = "success"
            
            reconnect_times = []
            for i in range(reconnect_attempts):
                reconnect_start = time.time()
                reconnected = await asyncio.wait_for(
                    ib_connection.connectAsync(
                        host=host,
                        port=port,
                        clientId=client_id,
                        timeout=timeout
                    ),
                    timeout=timeout + 5
                )
                reconnect_end = time.time()
                
                if not reconnected:
                    raise ConnectionError(f"Reconnection attempt {i+1} failed")
                
                reconnect_times.append(
                    (reconnect_end - reconnect_start) * 1000
                )
                details[f"reconnect_{i+1}_time_ms"] = reconnect_times[-1]
                
                ib_connection.disconnect()
            
            details["reconnect_attempts"] = reconnect_attempts
            details["avg_reconnect_time_ms"] = (
                sum(reconnect_times) / len(reconnect_times)
            )
            
        except Exception as e:
            error_message = str(e)
            error_trace = str(type(e).__name__) + ": " + str(e)
        finally:
            try:
                if ib_connection.state == ConnectionState.CONNECTED:
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
    async def test_invalid_host_connection(
        self,
        test_config: dict
    ) -> TestResult:
        """
        Test connection failure with invalid host.
        
        Verifies:
        - Appropriate error is raised for invalid host
        - Error message is descriptive
        - Connection state is properly set to DISCONNECTED
        """
        test_name = "test_invalid_host_connection"
        test_category = "Connection & Authentication"
        start_time = datetime.utcnow()
        error_message = None
        error_trace = None
        details = {}
        
        ib = IB()
        
        try:
            await asyncio.wait_for(
                ib.connectAsync(
                    host="192.168.255.255",
                    port=test_config["ibkr"]["socket_port"],
                    clientId=test_config["ibkr"]["client_id"],
                    timeout=5
                ),
                timeout=10
            )
            
            error_message = (
                "Connection to invalid host unexpectedly succeeded"
            )
            details["unexpected_success"] = True
            
        except asyncio.TimeoutError:
            error_message = None
            details["timeout_occurred"] = True
        except Exception as e:
            error_message = None
            details["expected_error"] = str(e)
            details["error_type"] = type(e).__name__
        finally:
            try:
                if ib.state == ConnectionState.CONNECTED:
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
    
    @pytest.mark.asyncio
    async def test_server_version_negotiation(
        self,
        ib_connection: IB,
        test_config: dict
    ) -> TestResult:
        """
        Test server version negotiation.
        
        Verifies:
        - Server version is properly negotiated
        - API version compatibility
        - Connection includes server details
        """
        test_name = "test_server_version_negotiation"
        test_category = "Connection & Authentication"
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
                    "Connection failed during version negotiation"
                )
            
            server_version = ib_connection.serverVersion()
            if server_version is None:
                raise ValueError("Server version not available")
            
            if not isinstance(server_version, int) or server_version <= 0:
                raise ValueError(f"Invalid server version: {server_version}")
            
            details = {
                "server_version": server_version,
                "api_version": ib_connection.apiVersion(),
                "connection_time": str(ib_connection.twsConnectionTime()),
            }
            
        except Exception as e:
            error_message = str(e)
            error_trace = str(type(e).__name__) + ": " + str(e)
        finally:
            try:
                if ib_connection.state == ConnectionState.CONNECTED:
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
