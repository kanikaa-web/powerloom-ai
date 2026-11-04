"""
cost_calculator.py
-------------------
Estimates production, labour, electricity, transport and total
manufacturing cost, plus expected profit and margin, for Module 4.
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Approximate industry-average rates (INR); can be tuned via admin settings later.
RATE_PRODUCTION_PER_UNIT = 10.0
RATE_ELECTRICITY_PER_UNIT = 3.3
RATE_LABOUR_PER_DAY = 1150.0
RATE_TRANSPORT_BASE = 3500.0
SELLING_PRICE_PER_UNIT = 34.0


def calculate_costs(raw_material_cost: float, production_qty: float,
                     working_days: int, distance_factor: float = 1.0):
    """
    Compute the full cost breakdown and profitability for a production run.
    """
    try:
        production_cost = production_qty * RATE_PRODUCTION_PER_UNIT
        electricity_cost = production_qty * RATE_ELECTRICITY_PER_UNIT
        labour_cost = working_days * RATE_LABOUR_PER_DAY
        transport_cost = RATE_TRANSPORT_BASE * distance_factor

        total_manufacturing_cost = (raw_material_cost + production_cost +
                                     electricity_cost + labour_cost + transport_cost)

        revenue = production_qty * SELLING_PRICE_PER_UNIT
        expected_profit = revenue - total_manufacturing_cost
        profit_margin = (expected_profit / revenue * 100) if revenue > 0 else 0

        return {
            "raw_material_cost": round(raw_material_cost, 2),
            "production_cost": round(production_cost, 2),
            "electricity_cost": round(electricity_cost, 2),
            "labour_cost": round(labour_cost, 2),
            "transport_cost": round(transport_cost, 2),
            "total_manufacturing_cost": round(total_manufacturing_cost, 2),
            "revenue": round(revenue, 2),
            "expected_profit": round(expected_profit, 2),
            "profit_margin_pct": round(profit_margin, 2),
        }
    except Exception as e:
        logger.error(f"Error calculating costs: {e}")
        raise
