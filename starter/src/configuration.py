from strands.models import BedrockModel


MODEL = BedrockModel(
    model_id="global.amazon.nova-2-lite-v1:0",
    region_name="us-east-1"
    )

GATEWAY_URL = "<gateway_url>"   # TODO: Replace with your Gateway URL
KB_ID       = "<kbid>"          # TODO: Replace with your Knowledge Base ID
REGION      = "<region>"        # TODO: Replace with your AWS region
MEMORY_ID   = "<mem_id>"        # TODO: Replace with your Memory ID

sys_prompt = """
            You are an intelligent AI customer support assistant for an e-commerce platform.

            Your role is to help customers with orders, returns, products, loyalty rewards,
            and general customer support requests through a natural multi-turn conversation.

            You have access to several capabilities. Use the appropriate capability whenever
            it is required to answer the customer's request accurately.
            
            """