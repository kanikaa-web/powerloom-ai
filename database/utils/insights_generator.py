"""
insights_generator.py
-----------------------
Generates plain-English, rule-based business insights from
current stock, production, and cost data (Module 8).
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_insights(stock_df, avg_daily_consumption: dict,
                       machine_efficiency: float, profit_trend_pct: float,
                       waste_pct: float):
    """
    stock_df: DataFrame with columns [material_name, current_stock, safety_stock, reorder_level]
    avg_daily_consumption: dict {material_name: qty/day}
    """
    insights = []

    try:
        for _, row in stock_df.iterrows():
            name = row["material_name"]
            stock = row["current_stock"]
            reorder = row["reorder_level"]
            daily_use = avg_daily_consumption.get(name, 0)

            if daily_use > 0:
                days_left = stock / daily_use
                if days_left <= 4:
                    insights.append(
                        f"⚠️ {name} stock may run out within {int(days_left)} day(s). "
                        f"Consider purchasing at least {round(daily_use * 7, 1)} units for a week's buffer."
                    )
            if stock < reorder:
                insights.append(f"📦 {name} is below reorder level — place a purchase order soon.")

        if machine_efficiency < 80:
            insights.append(
                f"🔧 Machine efficiency is at {machine_efficiency}%, below the healthy 85% benchmark. "
                "Inspect looms for maintenance needs."
            )

        if profit_trend_pct < 0:
            insights.append(
                f"📉 Expected profit may decrease by {abs(profit_trend_pct)}% based on recent cost trends."
            )
        elif profit_trend_pct > 5:
            insights.append(f"📈 Profit trend looks strong, up {profit_trend_pct}% recently.")

        if waste_pct > 8:
            insights.append(
                f"🧵 Wastage is at {waste_pct}%, higher than target. Improving loom efficiency "
                "and operator training could reduce wastage."
            )

        if not insights:
            insights.append("✅ All key metrics look healthy. No immediate action required.")

        return insights
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        return ["Unable to generate insights due to a data error."]
