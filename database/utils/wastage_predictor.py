"""
wastage_predictor.py
---------------------
Predicts expected material wastage percentage/quantity/cost and
generates root-cause + AI recommendations for Module 5.
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def predict_wastage(machine_efficiency: float, fabric_gsm: float,
                     machine_type: str, production_qty: float,
                     material_unit_cost: float = 165.0):
    """
    Heuristic wastage model (rule-based, tunable) driven by efficiency and GSM.
    Lower efficiency and higher GSM tend to raise wastage.
    """
    try:
        base_waste_pct = 5.5
        efficiency_penalty = max(0, (85 - machine_efficiency)) * 0.12
        gsm_penalty = max(0, (fabric_gsm - 180)) * 0.01
        machine_penalty = {"Shuttle": 1.5, "Waterjet": 0.5,
                            "Airjet": 0.2, "Rapier": 0.3, "Sulzer": 0.4}.get(machine_type, 0.5)

        waste_pct = round(min(15, base_waste_pct + efficiency_penalty + gsm_penalty + machine_penalty), 2)
        waste_qty = round(production_qty * (waste_pct / 100), 2)
        waste_cost = round(waste_qty * material_unit_cost, 2)

        root_causes = []
        if machine_efficiency < 80:
            root_causes.append("Low machine efficiency causing thread breaks and rework")
        if fabric_gsm > 220:
            root_causes.append("High GSM fabric increasing trims and edge wastage")
        if machine_type == "Shuttle":
            root_causes.append("Shuttle looms generally have higher wastage than modern looms")
        if not root_causes:
            root_causes.append("Wastage within normal operating range")

        recommendations = []
        if machine_efficiency < 80:
            recommendations.append("Schedule preventive maintenance to raise machine efficiency above 85%.")
        if fabric_gsm > 220:
            recommendations.append("Optimize cutting/trimming process for heavier GSM fabrics.")
        if machine_type == "Shuttle":
            recommendations.append("Consider migrating high-volume orders to Airjet/Rapier looms.")
        recommendations.append("Conduct operator training to reduce manual handling losses.")

        return {
            "expected_waste_pct": waste_pct,
            "waste_quantity": waste_qty,
            "waste_cost": waste_cost,
            "root_causes": root_causes,
            "recommendations": recommendations,
        }
    except Exception as e:
        logger.error(f"Error predicting wastage: {e}")
        raise
