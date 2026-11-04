"""
priority_predictor.py
-----------------------
Predicts order priority (High/Medium/Low) using a weighted
scoring approach based on delivery date urgency, order size,
customer priority, and machine availability.
"""

import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def predict_order_priority(delivery_date: str, order_size: float,
                            customer_priority: str, machine_availability_pct: float):
    """
    delivery_date: 'YYYY-MM-DD'
    customer_priority: 'VIP' | 'Regular' | 'New'
    machine_availability_pct: 0-100
    """
    try:
        days_left = (datetime.strptime(delivery_date, "%Y-%m-%d") - datetime.now()).days
        urgency_score = max(0, 100 - days_left * 5)  # closer date -> higher urgency
        size_score = min(100, order_size / 20)  # bigger orders -> higher score
        cust_score = {"VIP": 100, "Regular": 60, "New": 40}.get(customer_priority, 50)
        machine_score = 100 - machine_availability_pct  # less machine availability -> more urgent

        total_score = (urgency_score * 0.4 + size_score * 0.25 +
                        cust_score * 0.2 + machine_score * 0.15)

        if total_score >= 65:
            priority = "High"
        elif total_score >= 40:
            priority = "Medium"
        else:
            priority = "Low"

        return {
            "priority": priority,
            "score": round(total_score, 2),
            "days_left": days_left,
            "breakdown": {
                "urgency_score": round(urgency_score, 2),
                "size_score": round(size_score, 2),
                "customer_score": cust_score,
                "machine_score": round(machine_score, 2),
            }
        }
    except Exception as e:
        logger.error(f"Error predicting order priority: {e}")
        raise
