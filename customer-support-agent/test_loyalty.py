from strands import Agent
from src.customer_support_agent.tools import calculate_loyalty_discount
from src.customer_support_agent.config import MODEL




agent = Agent(
    model=MODEL,
    tools=[calculate_loyalty_discount]
)

response = agent(
    "I am a Gold member with 4250 points. "
    "Calculate my discount on a $150 standard order."
)

print(response)