from bedrock_agentcore.memory import MemoryClient
from strands.hooks import (
    HookProvider, AfterInvocationEvent, HookRegistry, MessageAddedEvent,
)
from typing import Dict
from .config import REGION


memory_client = MemoryClient(region_name=REGION)

def get_namespaces(mem_client: MemoryClient, memory_id: str) -> Dict:
    """Return a dict mapping strategy type → namespace template string."""

    strategies = mem_client.get_memory_strategies(memory_id)

    return {
        strategy["type"]: strategy["namespaces"][0]
        for strategy in strategies
    }

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
