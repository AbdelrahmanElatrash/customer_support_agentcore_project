from strands import Agent
from bedrock_agentcore.runtime import BedrockAgentCoreApp
import logging
from src.configuration import MODEL , sys_prompt, GATEWAY_URL
from src.validation.model_validation import Request ,Response
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamable_http_client
import asyncio
import json
import argparse


client = MCPClient(
    lambda: streamable_http_client(url=GATEWAY_URL)
)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("CSAI_Agent")


# create agentcore runtime app
app = BedrockAgentCoreApp()




@app.entrypoint
async def invoke(payload, context=None):
    """
    Main handler called by AgentCore for every incoming request.

    Expected payload keys:
      prompt      (str, required) — the customer's message
      customer_id (str, optional) — unique customer identifier
      session_id  (str, optional) — session identifier; generated if absent
    """
    # TODO: Implement the agent invocation
    request = Request.model_validate(payload)
    with client:
        tools = client.list_tools_sync()
        agent = Agent(model=MODEL,
                system_prompt=sys_prompt,
                tools=[]+tools)
        
        result = agent(request.message)
        response = Response(response=str(result))

        return response.model_dump()


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
    app.run()