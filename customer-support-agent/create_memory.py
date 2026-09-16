from bedrock_agentcore.memory import MemoryClient
from bedrock_agentcore.memory.constants import StrategyType


MEMORY_NAME = "CustomerSupportMemory"
OUTPUT_FILE = "memory_output.txt"

memory_client = MemoryClient()

strategies = [
    {
        StrategyType.SEMANTIC.value: {
            "name": "customer_facts",
            "description": (
                "Extracts factual information about customers "
                "and their support interactions"
            ),
            "namespaces": ["cs_agent/{actorId}/facts"],
        }
    },
    {
        StrategyType.USER_PREFERENCE.value: {
            "name": "customer_preferences",
            "description": (
                "Captures customer preferences for "
                "support interactions"
            ),
            "namespaces": ["cs_agent/{actorId}/preferences"],
        }
    },
]


def main():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as output:

        output.write(
            "Creating AgentCore Memory resource...\n"
        )

        response = memory_client.create_memory_and_wait(
            name=MEMORY_NAME,
            description=(
                "Memory for the e-commerce "
                "customer support agent"
            ),
            strategies=strategies,
            event_expiry_days=90,
        )

        memory_id = response["id"]

        output.write(
            "Memory resource created successfully.\n"
        )
        output.write(f"Memory ID: {memory_id}\n")
        output.write(f"Memory Name: {MEMORY_NAME}\n")
        output.write("Event expiry: 90 days\n\n")

        output.write("Strategies:\n")
        output.write("- customer_facts\n")
        output.write(
            "  Namespace: cs_agent/{actorId}/facts\n"
        )
        output.write("- customer_preferences\n")
        output.write(
            "  Namespace: cs_agent/{actorId}/preferences\n"
        )

    print(f"Memory created successfully.")
    print(f"Memory ID: {memory_id}")
    print(f"Output saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()