from strands import tool
from bedrock_agentcore.tools.code_interpreter_client import code_session
import json

@tool
def calculate_loyalty_discount(
    loyalty_points: int,
    tier: str,
    order_total: float,
    product_category: str = "standard",
) -> str:


    """
    Calculate the loyalty discount for a customer order using the
    AgentCore Code Interpreter. Runs exact arithmetic in a secure sandbox.

    Args:
        loyalty_points:   Customer's current points balance
        tier:             Customer tier — Silver, Gold, or Platinum
        order_total:      Order total in USD
        product_category: standard, device, or fresh

    Returns:
        Full discount breakdown and final price
    """
    # TODO: Build the code string (use an f-string to inject the arguments)
    code = ""  # Replace with your code string

    try:
        # TODO: Execute the code using code_session and return the result
        pass

    except Exception as e:
        # TODO: Implement fallback calculation using tier discount only
        pass


'''
from strands import tool
from bedrock_agentcore.tools.code_interpreter_client import code_session
import json


@tool
def calculate_loyalty_discount(
    loyalty_points: int,
    tier: str,
    order_total: float,
    product_category: str = "standard",
) -> str:

    code = f"""
loyalty_points = {loyalty_points}
tier = "{tier}"
order_total = {order_total}
product_category = "{product_category}"

# loyalty calculation logic here

print(...)
"""

    try:
        with code_session("us-east-1") as code_client:
            response = code_client.invoke(
                "executeCode",
                {
                    "code": code,
                    "language": "python",
                    "clearContext": False,
                },
            )

        for event in response["stream"]:
            if "result" in event:
                return json.dumps(event["result"])

    except Exception:
        # fallback calculation
        ...
        
'''