from strands import Agent, tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from src.customer_support_agent.config import MODEL, SYS_PROMPT, GATEWAY_URL,MEMORY_ID, REGION, KB_ID
import logging, os, asyncio, argparse, json, uuid, boto3, ast
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamable_http_client
from bedrock_agentcore.memory import MemoryClient
from strands_tools.browser import AgentCoreBrowser
from bedrock_agentcore.tools.code_interpreter_client import code_session
from pydantic import BaseModel, Field, ValidationError
from typing import Literal, Dict
from strands.hooks import (
    HookProvider, AfterInvocationEvent, HookRegistry, MessageAddedEvent,
)


logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("CSAI_Agent")



# Create the BedrockAgentCoreApp instance
app = BedrockAgentCoreApp()

# Suppress interactive tool-consent prompts (required in headless deployments).
os.environ["BYPASS_TOOL_CONSENT"] = "true"




# ── TODO 4 — Namespace Helper ─────────────────────────────────────────────────

def get_namespaces(mem_client: MemoryClient, memory_id: str) -> Dict:
    """Return a dict mapping strategy type → namespace template string."""

    strategies = mem_client.get_memory_strategies(memory_id)

    return {
        strategy["type"]: strategy["namespaces"][0]
        for strategy in strategies
    }

# ── TODO 5 — Memory Hook ──────────────────────────────────────────────────────
memory_client = MemoryClient(region_name=REGION)

class MemoryHook(HookProvider):
    """Long-term memory hook for the customer support agent."""

    def __init__(self, actor_id: str, session_id: str, memory_client: MemoryClient, memory_id: str,):

        # Store actor_id, session_id, memory_id, memory_client as attributes
        self.actor_id = actor_id
        self.session_id = session_id
        self.memory_client = memory_client
        self.memory_id = memory_id

        # Call get_namespaces() and store the result as self.namespaces
        self.namespaces = get_namespaces(
            self.memory_client,
            self.memory_id,
        )


    def retrieve_customer_context(self, event: MessageAddedEvent):
        """Retrieve relevant memories and prepend them to the user message."""
        messages = event.agent.messages

        if not messages:
            return

        last_message = messages[-1]

        if not isinstance(last_message, dict):
            return

        if last_message.get("role") != "user":
            return

        content = last_message.get("content", [])

        if not content:
            return

        if "toolResult" in content[0]:
            return

        user_query = content[0].get("text")

        if not user_query:
            return
        try:
            retrieved_memories = []

            for strategy_type, namespace in self.namespaces.items():
                
                memories = self.memory_client.retrieve_memories(
                    self.memory_id,
                    namespace.format(actorId=self.actor_id),
                    user_query,
                    top_k=5
                )

                for memory in memories:
                    text = memory.get("content", {}).get("text", "").strip()
                    if text:
                        retrieved_memories.append(f"[{strategy_type}] {text}")

            # Prepend memories to the user message if any found
            if retrieved_memories:
                context_message = "\n".join(retrieved_memories)
                enriched_message = f"Customer Context:\n{context_message}\n\n{user_query}"
                event.agent.messages[-1]["content"][0]["text"] = enriched_message

            
        except Exception as e:
            print(f"Memory retrieval error: {e}")


        

    def save_support_interaction(self, event: AfterInvocationEvent):
        """Save the completed turn to memory after the agent responds."""

        messages = event.agent.messages

        user_text = None
        agent_text = None

        # Walk backwards through the messages
        for message in reversed(messages):

            if not isinstance(message, dict):
                continue

            role = message.get("role")
            content = message.get("content", [])

            if not content:
                continue

            # Get plain text content
            text = (
                content[0].get("text")
                if isinstance(content[0], dict)
                else None
            )

            if not text:
                continue

            if role == "assistant" and agent_text is None:
                agent_text = text

            elif role == "user" and user_text is None:
                user_text = text

            if user_text and agent_text:
                break

        # Save only when both sides of the interaction exist
        if not user_text or not agent_text:
            return

        try:
            self.memory_client.create_event(
                memory_id=self.memory_id,
                actor_id=self.actor_id,
                session_id=self.session_id,
                messages=[
                    (user_text, "USER"),
                    (agent_text, "ASSISTANT"),
                ],
            )

        except Exception as e:
            print(f"Memory save error: {e}")


    def register_hooks(self, registry: HookRegistry) -> None:  # type: ignore
        """Register both memory callbacks."""
        registry.add_callback(MessageAddedEvent,self.retrieve_customer_context)

        registry.add_callback(AfterInvocationEvent,self.save_support_interaction)


# ── TODO 6 — Knowledge Base Tool ─────────────────────────────────────────────
_bedrock_runtime = boto3.client("bedrock-agent-runtime", region_name=REGION)

@tool
def search_knowledge_base(query: str) -> str:
    """
    Search the Amazon product catalog and support knowledge base.
    Use this for product specifications, return policies, warranty
    information, loyalty program details, and order status definitions.

    Args:
        query: The question or topic to search for

    Returns:
        Relevant information retrieved from the knowledge base
    """

    if not KB_ID:
        return "Knowledge Base ID is not configured."
    
    # Implement the Knowledge Base search
    try:
        resp = _bedrock_runtime.retrieve(
            knowledgeBaseId=KB_ID,
            retrievalQuery={"text": query},
        )
        results = resp.get("retrievalResults", [])
        if not results:
            return f"No information found for: {query}"

        chunks = [r["content"]["text"] for r in results]
        return "\n---\n".join(chunks)
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        return "An error occurred while searching the knowledge base."

    
# ── TODO 7 — Loyalty Discount Tool (Code Interpreter) ────────────────────────
##########################################################
# Define Pydantic models for input and output validation
class LoyaltyDiscountInput(BaseModel):
    """Validated input for a loyalty discount calculation."""

    loyalty_points: int = Field(ge=0, description="Customer's current loyalty points balance")
    tier: Literal["Silver", "Gold", "Platinum"] = Field(description="Customer loyalty tier: Silver, Gold, or Platinum")
    order_total: float = Field(gt=0, description="Total order amount in USD")
    product_category: Literal["standard", "device", "fresh"] = Field(
        default="standard",
        description="Product category: standard, device, or fresh"
    )


class LoyaltyDiscountOutput(BaseModel):
    loyalty_points: int
    tier: str
    product_category: str
    order_total: float
    tier_discount_pct: float
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
        loyalty_points: Customer's current points balance
        tier: Customer tier — Silver, Gold, or Platinum
        order_total: Order total in USD
        product_category: standard, device, or fresh

    Returns:
        Full discount breakdown and final price.
    """

    # Validate input
    try:
        validated_input = LoyaltyDiscountInput(
            loyalty_points=loyalty_points,
            tier=tier,
            order_total=order_total,
            product_category=product_category,
        )

    except ValidationError as e:
        return json.dumps({
            "error": "Invalid loyalty discount input",
            "details": e.errors(),
        })

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

        # Tier discount is independent of product category
        tier_discounts = {{
            "Silver": 0.05,
            "Gold": 0.10,
            "Platinum": 0.15,
        }}

        tier_discount_pct = tier_discounts[tier]

        # Product category affects earning rate only
        earn_rate = (
            2 if product_category == "device"
            else 5 if product_category == "fresh"
            else 1
        )

        # Points can only be redeemed in multiples of 500
        floored_points = (loyalty_points // 500) * 500

        # 100 points = $1 discount
        points_discount = floored_points / 100

        # Points redemption is capped at 50% of the order total
        points_discount = min(
            points_discount,
            order_total * 0.50,
        )

        # Determine actual points redeemed
        points_redeemed = int(points_discount * 100)

        # Tier discount is applied AFTER points redemption
        subtotal_after_points = order_total - points_discount

        tier_discount = subtotal_after_points * tier_discount_pct

        final_total = subtotal_after_points - tier_discount

        remaining_points = loyalty_points - points_redeemed

        result = {{
            "loyalty_points": loyalty_points,
            "tier": tier,
            "product_category": product_category,
            "order_total": round(order_total, 2),
            "tier_discount_pct": tier_discount_pct,
            "tier_discount": round(tier_discount, 2),
            "points_redeemed": points_redeemed,
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
                text = result["content"][0]["text"]

                parsed_result = ast.literal_eval(text)

                validated_output = LoyaltyDiscountOutput(
                    **parsed_result
                )

                return validated_output.model_dump_json()

        raise RuntimeError("Code Interpreter returned no result")

    except Exception as e:
        logger.exception(
            "Code Interpreter unavailable: %s",
            e,
        )

        # Fallback calculation using the same business rules
        tier_discounts = {
            "Silver": 0.05,
            "Gold": 0.10,
            "Platinum": 0.15,
        }

        tier_discount_pct = tier_discounts[tier]

        # Product category affects earning rate only
        earn_rate = (
            2 if product_category == "device"
            else 5 if product_category == "fresh"
            else 1
        )

        # Points are redeemed in multiples of 500
        floored_points = (loyalty_points // 500) * 500

        points_discount = floored_points / 100

        # Maximum points redemption = 50% of order total
        points_discount = min(
            points_discount,
            order_total * 0.50,
        )

        points_redeemed = int(points_discount * 100)

        # Tier discount is applied after points redemption
        subtotal_after_points = order_total - points_discount

        tier_discount = (
            subtotal_after_points * tier_discount_pct
        )

        final_total = (
            subtotal_after_points - tier_discount
        )

        remaining_points = loyalty_points - points_redeemed

        fallback_output = LoyaltyDiscountOutput(
            loyalty_points=loyalty_points,
            tier=tier,
            product_category=product_category,
            order_total=round(order_total, 2),
            tier_discount_pct=tier_discount_pct,
            tier_discount=round(tier_discount, 2),
            points_redeemed=points_redeemed,
            points_discount=round(points_discount, 2),
            remaining_points=remaining_points,
            final_total=round(final_total, 2),
            calculation_method="fallback",
        )

        return fallback_output.model_dump_json()
@app.entrypoint
async def invoke(payload, context=None):

    """ Main handler called by AgentCore for every incoming request. Expected payload 
        keys: prompt (str, required) 
            — the customer's message customer_id (str, optional) 
            — unique customer identifier session_id (str, optional) 
            — session identifier; generated if absent 
    """ 
    # Implement the agent invocation
    user_message = payload.get("prompt", "Hello!")
    actor_id = payload.get("customer_id", "customer-001")
    session_id = payload.get("session_id") or str(uuid.uuid4())

    browser = AgentCoreBrowser(
        region=REGION,
        session_timeout=600,
    )

    memory_hook = MemoryHook(
        actor_id=actor_id,
        session_id=session_id,
        memory_client=memory_client,
        memory_id=MEMORY_ID,
    )

    gateway_client = MCPClient(
        lambda: streamable_http_client(url=GATEWAY_URL)
    )

    with gateway_client:
        try:
            gateway_tools = gateway_client.list_tools_sync()

            if not gateway_tools:
                logger.warning(
                    "Gateway connected but returned no tools."
                )
                return {
                    "response": (
                        "I'm sorry, but the order service is currently "
                        "unavailable. Please try again later."
                    )
                }

            logger.info(
                "Gateway connected successfully. Loaded %d tools.",
                len(gateway_tools),
            )

            logger.info(
                "Gateway tools loaded: %s",
                [tool.name for tool in gateway_tools],
            )

        except TimeoutError:
            logger.exception("Gateway tool loading timed out")
            return {
                "response": (
                    "I'm sorry, but the order service is temporarily "
                    "unavailable. Please try again later."
                )
            }

        except ConnectionError:
            logger.exception("Gateway connection failed")
            return {
                "response": (
                    "I'm sorry, but I couldn't connect to the order "
                    "service. Please try again later."
                )
            }

        except Exception as exc:
            logger.exception(
                "Gateway tool loading failed: %s",
                exc,
            )
            return {
                "response": (
                    "I'm sorry, but the order service is currently "
                    "unavailable. Please try again later."
                )
            }

        agent = Agent(
            model=MODEL,
            system_prompt=SYS_PROMPT,
            tools=[
                calculate_loyalty_discount,
                search_knowledge_base,
                browser.browser,
            ] + gateway_tools,
            hooks=[memory_hook],
        )

        response = agent(user_message)

        return {"response": str(response)}

        

# ── CLI entry point (do not modify) ──────────────────────────────────────────
def main():
    """Run one invocation from the command line for local testing."""
    parser = argparse.ArgumentParser()
    parser.add_argument("payload", type=str)
    args = parser.parse_args()
    response = asyncio.run(invoke(json.loads(args.payload)))
    print(response)

if __name__== "__main__":
    # run the app locally for testing
    app.run(port=8081)