"""
IBKR Platform - Institutional-Grade Algorithmic Trading Platform

A tier-1 production-quality algorithmic trading platform for Interactive Brokers
with sub-millisecond latency and comprehensive risk management.

⚠️  WARNING: This system trades REAL MONEY. Use with extreme caution.
"""

__version__ = "0.1.0"
__author__ = "Trading Team"

# Core components
from ibkr_platform.core.types import (
    Order,
    Position,
    Execution,
    Bar,
    Tick,
    OrderStatus,
    OrderSide,
    OrderType,
    TimeInForce,
)

__all__ = [
    "Order",
    "Position",
    "Execution",
    "Bar",
    "Tick",
    "OrderStatus",
    "OrderSide",
    "OrderType",
    "TimeInForce",
]
