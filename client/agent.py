import asyncio

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from memory import ConversationMemory

load_dotenv()

MAX_MESSAGES = 10
SUMMARY_TRIGGER = 20


async def summarize_conversation(llm, messages, old_summary):

    conversation_text = ""

    for message in messages:

        role = message.type
        content = message.content

        if isinstance(content, str):
            conversation_text += f"{role}: {content}\n"

    prompt = f"""
        You are maintaining memory for an AI assistant.

        Existing summary:
        {old_summary}

        Older conversation:
        {conversation_text}

        Create a concise summary of the important information
        from the conversation.

        Keep:
        - Important user information
        - Important decisions
        - Important tasks
        - Important context
        - Important tool results
        - Information needed to understand future questions

        Do not include unnecessary details.

        Return only the summary.
        """

    response = await llm.ainvoke(prompt)

    return response.content

async def main():
    print("===================================")
    print("Connecting to MCP servers...")
    print("===================================")

    # ------------------------------------------------
    # MCP clients
    # ------------------------------------------------

    client = MultiServerMCPClient(
        {
            "weather":{
                "command" : "python",
                "args" : [
                    "servers/weather_server.py"
                ],
                "transport" : "stdio"

            },

            "email":{
                "command" : "python",
                "args" : [
                    "servers/email_server.py"
                ],
                "transport" : "stdio"
            }

        }
    )

    # ------------------------------------------------
    # Get tools from MCP servers
    # ------------------------------------------------

    tools = await client.get_tools()

    print("\nAvailable MCP tools:")

    for tool in tools:
        print(f"   - {tool.name}")

    # ------------------------------------------------
    # OpenAI model
    # ------------------------------------------------

    llm = ChatOpenAI(

        model = "gpt-4.1-mini",
        temperature = 0
    )

    # ------------------------------------------------
    # Create agent
    # ------------------------------------------------

    agent = create_agent(

        model=llm,
        tools=tools,
        system_prompt="""
        You are a helpful AI assistant.

        You have access to two tools:

        1. get_weather
           Use this when the user asks for current
           weather information.

        2. send_email
           Use this when the user explicitly asks
           you to send an email.

        For normal questions, answer directly without using a tool.

        Use the conversation summary and recent
        conversation messages to understand context.
        """
    )

    # --------------------------------------------------
    # 5. Conversation Memory
    # --------------------------------------------------

    memory = ConversationMemory()
    stored_memory = memory.load()
    summary = stored_memory["summary"]
    conversation = stored_memory["messages"]

    if summary:
        print("\nPrevious conversation summary loaded")

    
    if conversation:
        print("\nPrevious conversation loaded")

    print("\n======================================")
    print("       MCP AI CHATBOT STARTED")
    print("======================================")
    print("Type your question.")
    print("Press Ctrl+C to exit.\n")

    while True:
        print("Ask something:")
        user_input = input("You: ")
        if not user_input.strip():
            continue

        # add user message to conversation
        conversation.append(
            {
                "role":"user",
                "content":user_input
            }
        )


        # ------------------------------------------------
        # Build context
        # ------------------------------------------------

        context_messages = []
        if summary:

            context_messages.append(
                {
                    "role": "system",
                    "content": (
                        "Conversation summary:\n"
                        + summary
                    )
                }
            )

        context_messages.extend(
            conversation[-MAX_MESSAGES:]
        )

        #send complate conversation to agent
        response = await agent.ainvoke(
            {
                "messages":conversation
            }
        )

        #Get all messages returned by agent
        conversation= response["messages"]

         # ------------------------------------------------
        # Check whether summarization is required
        # ------------------------------------------------

        if len(conversation) >= SUMMARY_TRIGGER:

            print("\n[Memory] Summarizing older conversation...")

            old_messages = conversation[:-MAX_MESSAGES]

            summary = await summarize_conversation(
                llm,
                old_messages,
                summary
            )

            # Keep only recent messages
            conversation = conversation[-MAX_MESSAGES:]

            print("[Memory] Summary updated.")




        # ------------------------------------------------
        # Save conversation to SQLite
        # ------------------------------------------------

        memory.save(
            conversation,
            summary
        )

        #Display final response
        print("\nAI : ",conversation[-1].content)
        print()
    


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt as e:
        print("\n\nChatbot stopped")