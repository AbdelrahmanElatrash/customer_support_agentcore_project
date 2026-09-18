from strands import Agent
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from src.customer_support_agent.config import MODEL, SYS_PROMPT, GATEWAY_URL,MEMORY_ID, REGION
import logging, os, asyncio, argparse, json, uuid
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamable_http_client
from customer_support_agent.calculate_loyalty import calculate_loyalty_discount
from bedrock_agentcore.memory import MemoryClient
from src.customer_support_agent.memory  import MemoryHook
from src.customer_support_agent.KB import search_knowledge_base
from strands_tools.browser import AgentCoreBrowser



logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("CSAI_Agent")

# Create the BedrockAgentCoreApp instance
app = BedrockAgentCoreApp()

# Suppress interactive tool-consent prompts (required in headless deployments).
os.environ["BYPASS_TOOL_CONSENT"] = "true"


memory_client = MemoryClient(region_name=REGION)


@app.entrypoint
async def invoke(payload, context=None):
        """
        Main handler called by AgentCore for every incoming request.
    
        Expected payload keys:
          prompt      (str, required) — the customer's message
          customer_id (str, optional) — unique customer identifier
          session_id  (str, optional) — session identifier; generated if absent
        """
        # Implement the agent invocation
        
        user_message = payload.get("prompt", "Hello!")
        actor_id = payload.get("customer_id", "customer-001")
        session_id = payload.get("session_id") or str(uuid.uuid4())

        browser = AgentCoreBrowser(session_timeout=600)
        
        memory_hook = MemoryHook(
                    actor_id=actor_id,
                    session_id=session_id,
                    memory_client=memory_client,
                    memory_id=MEMORY_ID,
                        )

        
        client = MCPClient(
        lambda: streamable_http_client(url=GATEWAY_URL)
        )

        
        with client:
            tools = client.list_tools_sync()
            logger.info("Discovered %d tools from Gateway", len(tools))

            
            agent = Agent(model=MODEL,
                    system_prompt=SYS_PROMPT,
                    tools= [calculate_loyalty_discount, search_knowledge_base, browser.browser]+tools,
                    hooks=[memory_hook]
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