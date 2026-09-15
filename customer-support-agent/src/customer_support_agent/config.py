from strands.models import BedrockModel


REGION = "us-east-1"
SYS_PROMPT = """
            You are an intelligent AI customer support assistant for an e-commerce platform.

            Your role is to help customers with orders, returns, products, loyalty rewards,
            and general customer support requests through a natural multi-turn conversation.

            You have access to several capabilities. Use the appropriate capability whenever
            it is required to answer the customer's request accurately.
            
            """

GATEWAY_URL = "<gateway_url>"

#  Create the BedrockModel instance
MODEL = BedrockModel(
    model_id="global.amazon.nova-2-lite-v1:0",
    region_name=REGION
    )