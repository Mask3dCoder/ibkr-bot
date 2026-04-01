"""
Core domain types for the trading platform.

These types are used throughout the system and are designed for:
- Memory efficiency (using __slots__)
- Immutability where appropriate (dataclasses with frozen=True)
- Type safety (mypy strict mode compliance)
- Zero-copy compatibility (numpy structured array compatible)

CRITICAL: These types are on the hot path - any changes must be benchmarked.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum, IntEnum
from typing import Any, Optional
from uuid import UUID, uuid4


# ============================================================================
# ENUMS
# ============================================================================


class OrderSide(str, Enum):
    """Order side enumeration."""

    BUY = "BUY"
    SELL = "SELL"

    def __str__(self) -> str:
        return self.value


class OrderType(str, Enum):
    """Order type enumeration supporting IBKR order types."""

    MARKET = "MKT"
    LIMIT = "LMT"
    STOP = "STP"
    STOP_LIMIT = "STP LMT"
    MARKET_ON_CLOSE = "MOC"
    LIMIT_ON_CLOSE = "LOC"
    PEGGED_TO_MIDPOINT = "PEG MID"
    RELATIVE = "REL"
    MARKET_IF_TOUCHED = "MIT"
    LIMIT_IF_TOUCHED = "LIT"
    TRAILING_STOP = "TRAIL"
    TRAILING_STOP_LIMIT = "TRAIL LIMIT"
    
    # Advanced types
    ICEBERG = "ICEBERG"  # Our internal iceberg
    TWAP = "TWAP"  # Our TWAP algo
    VWAP = "VWAP"  # Our VWAP algo
    POV = "POV"  # Percent of volume
    SHORTFALL = "SHORTFALL"  # Implementation shortfall

    def __str__(self) -> str:
        return self.value


class TimeInForce(str, Enum):
    """Time in force enumeration."""

    DAY = "DAY"  # Valid for the day
    GTC = "GTC"  # Good till canceled
    IOC = "IOC"  # Immediate or cancel
    GTD = "GTD"  # Good till date
    OPG = "OPG"  # At the open
    FOK = "FOK"  # Fill or kill
    DTC = "DTC"  # Day till canceled

    def __str__(self) -> str:
        return self.value


class OrderStatus(IntEnum):
    """
    Order status enumeration.
    
    Using IntEnum for efficient comparison and storage.
    Order: PENDING < SUBMITTED < PARTIAL < FILLED/CANCELLED/REJECTED
    """

    PENDING = 0  # Created but not yet submitted
    VALIDATING = 1  # Running pre-trade checks
    APPROVED = 2  # Passed pre-trade checks
    SUBMITTED = 3  # Sent to broker
    ACKNOWLEDGED = 4  # Acknowledged by broker
    PARTIAL = 5  # Partially filled
    FILLED = 6  # Fully filled
    CANCELLED = 7  # Cancelled
    REJECTED = 8  # Rejected by broker or risk checks
    EXPIRED = 9  # Expired (GTD orders)
    ERROR = 10  # Error state

    def is_terminal(self) -> bool:
        """Check if this is a terminal state (no further updates expected)."""
        return self in (
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
            OrderStatus.EXPIRED,
            OrderStatus.ERROR,
        )

    def is_active(self) -> bool:
        """Check if order is active (can receive fills)."""
        return self in (OrderStatus.SUBMITTED, OrderStatus.ACKNOWLEDGED, OrderStatus.PARTIAL)


class PositionSide(str, Enum):
    """Position side."""

    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"

    def __str__(self) -> str:
        return self.value


class AssetClass(str, Enum):
    """Asset class enumeration."""

    STOCK = "STK"
    OPTION = "OPT"
    FUTURE = "FUT"
    FOREX = "CASH"
    INDEX = "IND"
    CFD = "CFD"
    COMMODITY = "CMDTY"
    BOND = "BOND"
    FUND = "FUND"
    WARRANT = "WAR"

    def __str__(self) -> str:
        return self.value


# ============================================================================
# CORE DATA TYPES
# ============================================================================


@dataclass(frozen=True, slots=True)
class Contract:
    """
    Contract specification.
    
    Immutable contract definition matching IBKR contract spec.
    """

    symbol: str
    asset_class: AssetClass
    exchange: str = "SMART"  # Default to SMART routing
    currency: str = "USD"
    
    # Optional fields for derivatives
    expiry: Optional[str] = None  # YYYYMMDD format
    strike: Optional[Decimal] = None
    right: Optional[str] = None  # C or P for options
    multiplier: Optional[int] = None
    
    # Unique identifier
    conid: Optional[int] = None  # IBKR contract ID
    local_symbol: Optional[str] = None

    def __str__(self) -> str:
        if self.asset_class == AssetClass.STOCK:
            return f"{self.symbol} ({self.exchange})"
        elif self.asset_class == AssetClass.OPTION:
            return f"{self.symbol} {self.expiry} {self.strike}{self.right}"
        else:
            return f"{self.symbol} ({self.asset_class})"


@dataclass(slots=True)
class Order:
    """
    Order representation.
    
    Mutable to allow status updates. Uses __slots__ for memory efficiency.
    This is the core order type used throughout the system.
    
    CRITICAL: This is on the hot path - minimize allocations.
    """

    # Identifiers
    order_id: UUID = field(default_factory=uuid4)
    client_order_id: str = field(default_factory=lambda: f"ORD{uuid4().hex[:12].upper()}")
    broker_order_id: Optional[int] = None  # IBKR order ID
    
    # Parent-child relationship
    parent_order_id: Optional[UUID] = None
    child_order_ids: list[UUID] = field(default_factory=list)
    
    # Contract
    contract: Contract = field(default_factory=lambda: Contract("", AssetClass.STOCK))
    
    # Order details
    side: OrderSide = OrderSide.BUY
    order_type: OrderType = OrderType.LIMIT
    quantity: Decimal = Decimal("0")
    filled_quantity: Decimal = Decimal("0")
    remaining_quantity: Decimal = Decimal("0")
    
    # Pricing
    limit_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    avg_fill_price: Optional[Decimal] = None
    
    # Timing
    time_in_force: TimeInForce = TimeInForce.DAY
    good_till_date: Optional[datetime] = None
    
    # Status
    status: OrderStatus = OrderStatus.PENDING
    status_message: str = ""
    
    # Timestamps (use int for nanosecond precision)
    created_at_ns: int = 0
    submitted_at_ns: Optional[int] = None
    acknowledged_at_ns: Optional[int] = None
    completed_at_ns: Optional[int] = None
    
    # Strategy attribution
    strategy_id: Optional[str] = None
    account: Optional[str] = None
    
    # Advanced order parameters
    hidden: bool = False  # Don't display order size
    outside_rth: bool = False  # Allow outside regular trading hours
    all_or_none: bool = False  # All or none fill
    
    # Execution algorithm parameters
    exec_algo: Optional[str] = None  # Which algo is handling this
    exec_algo_params: dict[str, Any] = field(default_factory=dict)
    
    # Risk metadata
    approved_by_risk: bool = False
    risk_check_time_ns: Optional[int] = None
    rejection_reason: Optional[str] = None
    
    # User metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Set created timestamp if not provided."""
        if self.created_at_ns == 0:
            import time
            self.created_at_ns = time.time_ns()
        
        # Initialize remaining quantity
        if self.remaining_quantity == Decimal("0"):
            self.remaining_quantity = self.quantity

    @property
    def is_complete(self) -> bool:
        """Check if order is in terminal state."""
        return self.status.is_terminal()

    @property
    def is_active(self) -> bool:
        """Check if order can still receive fills."""
        return self.status.is_active()

    @property
    def fill_ratio(self) -> Decimal:
        """Get fill ratio (0.0 to 1.0)."""
        if self.quantity == 0:
            return Decimal("0")
        return self.filled_quantity / self.quantity

    def update_fill(self, fill_qty: Decimal, fill_price: Decimal) -> None:
        """
        Update order with new fill.
        
        Args:
            fill_qty: Quantity filled in this update
            fill_price: Price of the fill
        """
        self.filled_quantity += fill_qty
        self.remaining_quantity = self.quantity - self.filled_quantity
        
        # Update average fill price
        if self.avg_fill_price is None:
            self.avg_fill_price = fill_price
        else:
            # Weighted average
            total_filled_value = (
                self.avg_fill_price * (self.filled_quantity - fill_qty)
                + fill_price * fill_qty
            )
            self.avg_fill_price = total_filled_value / self.filled_quantity
        
        # Update status
        if self.remaining_quantity == 0:
            self.status = OrderStatus.FILLED
            import time
            self.completed_at_ns = time.time_ns()
        elif self.filled_quantity > 0:
            self.status = OrderStatus.PARTIAL


@dataclass(frozen=True, slots=True)
class Execution:
    """
    Execution (fill) representation.
    
    Immutable record of an execution. One order can have multiple executions.
    """

    execution_id: str
    order_id: UUID
    broker_order_id: int
    
    contract: Contract
    side: OrderSide
    
    quantity: Decimal
    price: Decimal
    
    timestamp_ns: int
    exchange: str
    
    commission: Decimal = Decimal("0")
    realized_pnl: Optional[Decimal] = None
    
    # Metadata
    account: Optional[str] = None
    strategy_id: Optional[str] = None

    @property
    def notional_value(self) -> Decimal:
        """Calculate notional value of execution."""
        return abs(self.quantity * self.price)


@dataclass(slots=True)
class Position:
    """
    Position representation.
    
    Mutable as position changes with fills and market moves.
    """

    contract: Contract
    account: str
    
    # Position size
    quantity: Decimal = Decimal("0")
    
    # Cost basis
    avg_cost: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
    
    # Market data
    last_price: Optional[Decimal] = None
    market_value: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    
    # Strategy attribution
    strategy_id: Optional[str] = None
    
    # Timestamps
    opened_at_ns: Optional[int] = None
    last_updated_ns: int = 0
    
    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Set timestamp if not provided."""
        if self.last_updated_ns == 0:
            import time
            self.last_updated_ns = time.time_ns()

    @property
    def side(self) -> PositionSide:
        """Get position side."""
        if self.quantity > 0:
            return PositionSide.LONG
        elif self.quantity < 0:
            return PositionSide.SHORT
        else:
            return PositionSide.FLAT

    @property
    def notional_value(self) -> Decimal:
        """Calculate notional value of position."""
        if self.market_value is not None:
            return abs(self.market_value)
        return Decimal("0")

    def update_market_data(self, last_price: Decimal) -> None:
        """
        Update position with new market data.
        
        Args:
            last_price: Current market price
        """
        self.last_price = last_price
        self.market_value = self.quantity * last_price
        self.unrealized_pnl = self.market_value - (self.quantity * self.avg_cost)
        
        import time
        self.last_updated_ns = time.time_ns()


@dataclass(frozen=True, slots=True)
class Tick:
    """
    Tick data representation.
    
    Immutable tick data. Optimized for high-frequency updates.
    """

    contract: Contract
    timestamp_ns: int
    
    # Price data
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    last: Optional[Decimal] = None
    
    # Size data
    bid_size: Optional[int] = None
    ask_size: Optional[int] = None
    last_size: Optional[int] = None
    volume: Optional[int] = None
    
    # Flags
    is_trade: bool = False
    is_quote: bool = False

    @property
    def mid(self) -> Optional[Decimal]:
        """Calculate mid-price."""
        if self.bid is not None and self.ask is not None:
            return (self.bid + self.ask) / Decimal("2")
        return None

    @property
    def spread(self) -> Optional[Decimal]:
        """Calculate bid-ask spread."""
        if self.bid is not None and self.ask is not None:
            return self.ask - self.bid
        return None


@dataclass(frozen=True, slots=True)
class Bar:
    """
    OHLCV bar representation.
    
    Immutable bar data for various timeframes.
    """

    contract: Contract
    timestamp_ns: int  # Bar start time
    timeframe: str  # e.g., "1min", "5min", "1hour"
    
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    
    # Additional fields
    vwap: Optional[Decimal] = None  # Volume-weighted average price
    trade_count: Optional[int] = None
    
    # Flags
    is_complete: bool = True  # False for in-progress bars

    @property
    def typical_price(self) -> Decimal:
        """Calculate typical price (HLC/3)."""
        return (self.high + self.low + self.close) / Decimal("3")

    @property
    def range(self) -> Decimal:
        """Calculate bar range (high - low)."""
        return self.high - self.low


# ============================================================================
# RISK TYPES
# ============================================================================


@dataclass(frozen=True, slots=True)
class RiskLimit:
    """
    Risk limit specification.
    
    Used for position limits, order size limits, etc.
    """

    name: str
    limit_type: str  # "position", "order_size", "notional", "concentration"
    
    # Limit values
    max_value: Optional[Decimal] = None
    min_value: Optional[Decimal] = None
    
    # Scope
    symbol: Optional[str] = None
    strategy_id: Optional[str] = None
    account: Optional[str] = None
    
    # Soft vs hard limit
    is_hard_limit: bool = True  # Hard limits block, soft limits alert


@dataclass(slots=True)
class RiskMetrics:
    """
    Risk metrics snapshot.
    
    Calculated risk metrics for portfolio or position.
    """

    timestamp_ns: int
    
    # P&L
    realized_pnl: Decimal = Decimal("0")
    unrealized_pnl: Decimal = Decimal("0")
    total_pnl: Decimal = Decimal("0")
    
    # Position metrics
    gross_exposure: Decimal = Decimal("0")
    net_exposure: Decimal = Decimal("0")
    
    # Greeks (for options)
    delta: Optional[Decimal] = None
    gamma: Optional[Decimal] = None
    vega: Optional[Decimal] = None
    theta: Optional[Decimal] = None
    
    # VaR
    var_1min: Optional[Decimal] = None
    var_5min: Optional[Decimal] = None
    var_30min: Optional[Decimal] = None
    var_daily: Optional[Decimal] = None
    
    # Margin
    margin_used: Optional[Decimal] = None
    margin_available: Optional[Decimal] = None
    margin_utilization: Optional[Decimal] = None


# ============================================================================
# EVENT TYPES
# ============================================================================


@dataclass(frozen=True, slots=True)
class Event:
    """
    Base event type for event bus.
    
    All events inherit from this.
    """

    event_id: UUID = field(default_factory=uuid4)
    event_type: str = "base"
    timestamp_ns: int = 0
    source: str = "unknown"
    
    # For correlation/tracing
    correlation_id: Optional[UUID] = None
    trace_id: Optional[str] = None

    def __post_init__(self) -> None:
        """Set timestamp if not provided."""
        if self.timestamp_ns == 0:
            import time
            object.__setattr__(self, "timestamp_ns", time.time_ns())
