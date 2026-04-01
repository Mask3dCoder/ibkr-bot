"""
Custom exception hierarchy for the trading platform.

Organized by subsystem with clear inheritance hierarchy.
All exceptions inherit from PlatformError for easy catching.
"""


class PlatformError(Exception):
    """Base exception for all platform errors."""

    pass


# ============================================================================
# CONNECTION ERRORS
# ============================================================================


class ConnectionError(PlatformError):
    """Base class for connection-related errors."""

    pass


class IBKRConnectionError(ConnectionError):
    """IBKR connection failed or lost."""

    pass


class IBKRAuthenticationError(ConnectionError):
    """IBKR authentication failed."""

    pass


class DatabaseConnectionError(ConnectionError):
    """Database connection failed."""

    pass


class RedisConnectionError(ConnectionError):
    """Redis connection failed."""

    pass


# ============================================================================
# CONFIGURATION ERRORS
# ============================================================================


class ConfigurationError(PlatformError):
    """Base class for configuration errors."""

    pass


class InvalidConfigurationError(ConfigurationError):
    """Configuration values are invalid."""

    pass


class MissingConfigurationError(ConfigurationError):
    """Required configuration is missing."""

    pass


# ============================================================================
# DATA ERRORS
# ============================================================================


class DataError(PlatformError):
    """Base class for data-related errors."""

    pass


class InvalidDataError(DataError):
    """Data is invalid or malformed."""

    pass


class StaleDataError(DataError):
    """Data is stale (too old)."""

    pass


class MissingDataError(DataError):
    """Required data is missing."""

    pass


class DataQualityError(DataError):
    """Data quality check failed (e.g., crossed market, negative spread)."""

    pass


# ============================================================================
# ORDER ERRORS
# ============================================================================


class OrderError(PlatformError):
    """Base class for order-related errors."""

    pass


class InvalidOrderError(OrderError):
    """Order parameters are invalid."""

    pass


class OrderNotFoundError(OrderError):
    """Order not found in system."""

    pass


class OrderStateError(OrderError):
    """Order is in wrong state for requested operation."""

    pass


class OrderRejectionError(OrderError):
    """Order was rejected (by broker or internal systems)."""

    pass


class DuplicateOrderError(OrderError):
    """Duplicate order detected."""

    pass


# ============================================================================
# RISK ERRORS
# ============================================================================


class RiskError(PlatformError):
    """Base class for risk-related errors."""

    pass


class RiskLimitViolation(RiskError):
    """Risk limit exceeded."""

    def __init__(self, message: str, limit_name: str, current_value: float, limit_value: float):
        super().__init__(message)
        self.limit_name = limit_name
        self.current_value = current_value
        self.limit_value = limit_value


class PreTradeCheckFailure(RiskError):
    """Pre-trade risk check failed."""

    def __init__(self, message: str, check_name: str, details: dict | None = None):
        super().__init__(message)
        self.check_name = check_name
        self.details = details or {}


class InsufficientMarginError(RiskError):
    """Insufficient margin for operation."""

    pass


class PositionLimitExceeded(RiskError):
    """Position limit would be exceeded."""

    pass


class CircuitBreakerTriggered(RiskError):
    """Circuit breaker has been triggered."""

    def __init__(self, message: str, breaker_name: str, threshold: float, current_value: float):
        super().__init__(message)
        self.breaker_name = breaker_name
        self.threshold = threshold
        self.current_value = current_value


class KillSwitchActive(RiskError):
    """Kill switch is active - all trading halted."""

    pass


# ============================================================================
# EXECUTION ERRORS
# ============================================================================


class ExecutionError(PlatformError):
    """Base class for execution-related errors."""

    pass


class ExecutionAlgoError(ExecutionError):
    """Execution algorithm encountered an error."""

    pass


class FillTrackingError(ExecutionError):
    """Error tracking fills."""

    pass


# ============================================================================
# STRATEGY ERRORS
# ============================================================================


class StrategyError(PlatformError):
    """Base class for strategy-related errors."""

    pass


class StrategyNotFoundError(StrategyError):
    """Strategy not found."""

    pass


class StrategyStateError(StrategyError):
    """Strategy is in wrong state."""

    pass


class StrategyConfigurationError(StrategyError):
    """Strategy configuration is invalid."""

    pass


class StrategyExecutionError(StrategyError):
    """Error during strategy execution."""

    pass


# ============================================================================
# PERSISTENCE ERRORS
# ============================================================================


class PersistenceError(PlatformError):
    """Base class for persistence-related errors."""

    pass


class DatabaseError(PersistenceError):
    """Database operation failed."""

    pass


class CacheError(PersistenceError):
    """Cache operation failed."""

    pass


class StateReconciliationError(PersistenceError):
    """State reconciliation failed."""

    pass


# ============================================================================
# VALIDATION ERRORS
# ============================================================================


class ValidationError(PlatformError):
    """Base class for validation errors."""

    pass


class ContractValidationError(ValidationError):
    """Contract validation failed."""

    pass


class ParameterValidationError(ValidationError):
    """Parameter validation failed."""

    pass


# ============================================================================
# TIMEOUT ERRORS
# ============================================================================


class TimeoutError(PlatformError):
    """Operation timed out."""

    pass


class OrderAcknowledgementTimeout(TimeoutError):
    """Order acknowledgement not received in time."""

    pass


class DataTimeout(TimeoutError):
    """Data not received in time."""

    pass


# ============================================================================
# SYSTEM ERRORS
# ============================================================================


class SystemError(PlatformError):
    """Base class for system-level errors."""

    pass


class ShutdownError(SystemError):
    """Error during shutdown."""

    pass


class StartupError(SystemError):
    """Error during startup."""

    pass


class ResourceExhaustedError(SystemError):
    """System resource exhausted (memory, connections, etc.)."""

    pass
