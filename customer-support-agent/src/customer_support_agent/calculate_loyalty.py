from strands import tool
from bedrock_agentcore.tools.code_interpreter_client import code_session
from pydantic import BaseModel, Field
from typing import Literal
from .config import REGION
import json


class LoyaltyDiscountInput(BaseModel):
    loyalty_points: int = Field(ge=0)
    tier: Literal["Silver", "Gold", "Platinum"]
    order_total: float = Field(gt=0)
    product_category: Literal["standard", "device", "fresh"] = "standard"


class LoyaltyDiscountOutput(BaseModel):
    loyalty_points: int
    tier: str
    product_category: str
    order_total: float
    tier_discount_rate: float
    tier_discount: float
    points_redeemed: int
    points_discount: float
    remaining_points: int
    final_total: float
    calculation_method: str = "code_interpreter"
    

@tool
def calculate_loyalty_discount(
    loyalty_points: int,
    tier: str,
    order_total: float,
    product_category: str = "standard",
) -> str:
    """
    Calculate the loyalty discount for a customer order.

    Uses Amazon Bedrock AgentCore Code Interpreter for the calculation
    and validates the result with Pydantic.

    Args:
            loyalty_points:   Customer's current points balance
            tier:             Customer tier — Silver, Gold, or Platinum
            order_total:      Order total in USD
            product_category: standard, device, or fresh

    Returns:
        Full discount breakdown and final price 
    """

    # Validate input
    try:
        validated_input = LoyaltyDiscountInput(
            loyalty_points=loyalty_points,
            tier=tier,
            order_total=order_total,
            product_category=product_category,
        )
    except Exception as e:
        return json.dumps({
            "error": "Invalid loyalty discount input",
            "details": str(e),
        })

    # Use validated values
    loyalty_points = validated_input.loyalty_points
    tier = validated_input.tier
    order_total = validated_input.order_total
    product_category = validated_input.product_category

    # Code executed inside AgentCore Code Interpreter
    code = f"""
loyalty_points = {loyalty_points}
tier = "{tier}"
order_total = {order_total}
product_category = "{product_category}"

tier_discounts = {{
    "Silver": 0.00,
    "Gold": 0.10,
    "Platinum": 0.15,
}}

tier_discount_rate = tier_discounts.get(tier, 0.00)
tier_discount = order_total * tier_discount_rate

redeemable_points = (loyalty_points // 100) * 100

if redeemable_points >= 500:
    points_discount = redeemable_points / 100
else:
    redeemable_points = 0
    points_discount = 0.0

points_discount = min(
    points_discount,
    order_total - tier_discount
)

final_total = order_total - tier_discount - points_discount
remaining_points = loyalty_points - redeemable_points

result = {{
    "loyalty_points": loyalty_points,
    "tier": tier,
    "product_category": product_category,
    "order_total": round(order_total, 2),
    "tier_discount_rate": tier_discount_rate,
    "tier_discount": round(tier_discount, 2),
    "points_redeemed": redeemable_points,
    "points_discount": round(points_discount, 2),
    "remaining_points": remaining_points,
    "final_total": round(final_total, 2),
}}

print(result)
"""

    try:
        with code_session(REGION) as code_client:
            response = code_client.invoke(
                "executeCode",
                {
                    "code": code,
                    "language": "python",
                    "clearContext": True,
                },
            )

        for event in response["stream"]:
            if "result" in event:

                result = event["result"]

                # Validate Code Interpreter output
                validated_output = LoyaltyDiscountOutput(
                    **result
                )

                return validated_output.model_dump_json()

        raise RuntimeError("Code Interpreter returned no result")

    except Exception as e:
        print(f"Code Interpreter unavailable: {e}")

        # Fallback calculation
        tier_discounts = {
            "Silver": 0.00,
            "Gold": 0.10,
            "Platinum": 0.15,
        }

        tier_discount_rate = tier_discounts[tier]
        tier_discount = order_total * tier_discount_rate

        redeemable_points = (loyalty_points // 100) * 100

        if redeemable_points >= 500:
            points_discount = redeemable_points / 100
        else:
            redeemable_points = 0
            points_discount = 0.0

        points_discount = min(
            points_discount,
            order_total - tier_discount,
        )

        final_total = order_total - tier_discount - points_discount
        remaining_points = loyalty_points - redeemable_points

        fallback_output = LoyaltyDiscountOutput(
            loyalty_points=loyalty_points,
            tier=tier,
            product_category=product_category,
            order_total=round(order_total, 2),
            tier_discount_rate=tier_discount_rate,
            tier_discount=round(tier_discount, 2),
            points_redeemed=redeemable_points,
            points_discount=round(points_discount, 2),
            remaining_points=remaining_points,
            final_total=round(final_total, 2),
            calculation_method="fallback",
        )

        return fallback_output.model_dump_json()