import asyncio

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

load_dotenv()

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

    # weather_tool = next(
    #     tool for tool in tools
    #     if tool.name == "get_weather"
    # )

    # print("\nTesting weather tool directly...")

    # result = await weather_tool.ainvoke({
    #     "city": "Delhi"
    # })

    # print("\nWEATHER TOOL RESULT:")
    # print(result)

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

        For normal questions, answer directly
        without using a tool.
        """
    )
    # ------------------------------------------------
    # User input
    # ------------------------------------------------

    user_input = input("\nAsk something: ")

    # ------------------------------------------------
    # Invoke agent
    # ------------------------------------------------

    response = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": user_input
                }
            ]
        }
    )

    # ------------------------------------------------
    # Final response
    # ------------------------------------------------

    print("\n===================================")
    print("FINAL ANSWER")
    print("===================================")

    print(
        response["messages"][-1].content
    )


if __name__ == "__main__":
    asyncio.run(main())