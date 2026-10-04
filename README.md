# MCP Tool Calling Agent

A hands-on AI agent project demonstrating **OpenAI + LangChain Agent + LangGraph + MCP + Tavily + Resend**.

The project exposes two tools through MCP:

1. **Weather Tool** — searches the web through Tavily for current weather information.
2. **Email Tool** — sends an email through Resend.

The OpenAI-powered agent decides whether it should answer normally or call one of the MCP tools.

---

## 1. Project Goal

The goal of this project is to understand the complete flow of **LLM tool calling with MCP**.

```text
User
  |
  v
LangChain Agent
  |
  v
OpenAI LLM
  |
  +----------------------+
  |                      |
  v                      v
get_weather           send_email
  |                      |
  v                      v
MCP Weather Server    MCP Email Server
  |                      |
  v                      v
Tavily                  Resend
  |                      |
  +----------+-----------+
             |
             v
        Tool Result
             |
             v
          OpenAI
             |
             v
        Final Answer
```

---

## 2. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Application language |
| uv | Python project/package/environment management |
| OpenAI | LLM used by the agent |
| LangChain | Agent framework |
| LangGraph | Agent execution/orchestration underneath the current LangChain agent |
| MCP | Standard protocol for exposing tools |
| FastMCP | Easy MCP server implementation |
| Tavily | Web search used by the weather tool |
| Resend | Email delivery service |
| python-dotenv | Loads environment variables |

---

## 3. Project Structure

```text
mcp-tool-calling-agent/
│
├── .env
├── .gitignore
├── README.md
├── pyproject.toml
├── uv.lock
│
├── client/
│   ├── __init__.py
│   └── agent.py
│
└── servers/
    ├── __init__.py
    ├── weather_server.py
    └── email_server.py
```

### Description

- **`.env`** — API keys and configuration.
- **`client/agent.py`** — connects to MCP servers, discovers tools, creates the agent, accepts user input, and prints the final response.
- **`servers/weather_server.py`** — exposes `get_weather(city)` and uses Tavily.
- **`servers/email_server.py`** — exposes `send_email(to, subject, body)` and uses Resend.

---

## 4. Prerequisites

Install:

- Python 3.13 or a compatible Python version
- uv
- OpenAI API key
- Tavily API key
- Resend API key

---

## 5. Create the Project

```powershell
uv init mcp-tool-calling-agent
cd mcp-tool-calling-agent
uv venv
.venv\Scripts\Activate.ps1
```

---

## 6. Install Dependencies

```powershell
uv add openai python-dotenv tavily-python resend mcp langchain-mcp-adapters langchain langchain-openai
```

Important packages:

```text
openai
python-dotenv
tavily-python
resend
mcp
langchain
langchain-openai
langchain-mcp-adapters
```

---

## 7. Environment Variables

Create `.env` in the project root:

```env
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
RESEND_API_KEY=your_resend_api_key
SENDER_EMAIL=onboarding@resend.dev
```

Never commit `.env` to Git.

Recommended `.gitignore`:

```gitignore
.env
.venv/
__pycache__/
*.pyc
```

---

## 8. Weather MCP Server

File:

```text
servers/weather_server.py
```

It exposes:

```python
@mcp.tool()
def get_weather(city: str) -> str:
```

The tool:

1. receives a city
2. creates a web-search query
3. sends it to Tavily
4. extracts search results
5. returns the information to the MCP client

Example query:

```text
current weather in Delhi today
```

### Important stdio rule

The server uses:

```python
mcp.run(transport="stdio")
```

stdout is reserved for MCP protocol communication, so debug output should go to stderr:

```python
print(f"Searching weather for: {city}", file=sys.stderr)
```

---

## 9. Email MCP Server

File:

```text
servers/email_server.py
```

It exposes:

```python
@mcp.tool()
def send_email(to: str, subject: str, body: str) -> str:
```

The tool:

1. receives recipient
2. receives subject
3. receives email body
4. sends the email through Resend
5. returns the result to the agent

---

## 10. MCP Client / Agent

File:

```text
client/agent.py
```

Example MCP configuration:

```python
client = MultiServerMCPClient({
    "weather": {
        "command": "uv",
        "args": [
            "run",
            "python",
            "servers/weather_server.py"
        ],
        "transport": "stdio"
    },
    "email": {
        "command": "uv",
        "args": [
            "run",
            "python",
            "servers/email_server.py"
        ],
        "transport": "stdio"
    }
})
```

Using `uv run` makes the MCP subprocess use the project environment and dependencies.

---

## 11. Discovering MCP Tools

The client gets tools with:

```python
tools = await client.get_tools()
```

The successful project output is:

```text
Available MCP tools:
   - get_weather
   - send_email
```

These tools are then passed to the agent.

---

## 12. Creating the Agent

The project uses:

```python
from langchain.agents import create_agent
```

Example:

```python
agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="""
    You are a helpful AI assistant.

    You have access to:
    1. get_weather: use for current weather information.
    2. send_email: use when the user explicitly asks to send an email.

    For normal questions, answer directly without a tool.
    """
)
```

The agent decides whether a tool is required.

---

## 13. OpenAI Model

Example:

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0
)
```

The key is loaded from:

```env
OPENAI_API_KEY=...
```

---

## 14. Running the Project

From the project root:

```powershell
python .\client\agent.py
```

or:

```powershell
uv run python .\client\agent.py
```

Expected startup:

```text
===================================
Connecting to MCP servers...
===================================

Available MCP tools:
   - get_weather
   - send_email

Ask something:
```

---

## 15. Test 1 — Normal Question

Ask:

```text
What is Python?
```

No external tool is required.

```text
User
  |
  v
Agent
  |
  v
OpenAI
  |
  v
Final Answer
```

---

## 16. Test 2 — Weather Tool

Ask:

```text
What is the current weather in Delhi?
```

The agent selects `get_weather`.

```text
User
  |
  v
Agent
  |
  v
OpenAI
  |
  | tool call
  v
get_weather(city="Delhi")
  |
  v
MCP Weather Server
  |
  v
Tavily
  |
  v
Search Results
  |
  v
MCP Tool Result
  |
  v
OpenAI
  |
  v
Final Answer
```

This test was successfully completed in the project.

---

## 17. Test 3 — Email Tool

Ask:

```text
Send an email to delivered@resend.dev
with subject "Test Email"
and body "Hello from my MCP project."
```

The agent selects `send_email`.

```text
User
  |
  v
Agent
  |
  v
OpenAI
  |
  | tool call
  v
send_email(...)
  |
  v
MCP Email Server
  |
  v
Resend
  |
  v
Email delivery
  |
  v
Tool Result
  |
  v
OpenAI
  |
  v
Final Answer
```

This test was successfully completed in the project.

---

## 18. Resend Testing

For development, the project can use:

```env
SENDER_EMAIL=onboarding@resend.dev
```

and a test recipient such as:

```text
delivered@resend.dev
```

For production, configure and verify a domain that you control according to Resend's requirements.

---

## 19. Tool Calling Concept

Tool calling allows the LLM to decide that it needs an external capability.

The LLM does **not** execute the Python function itself.

Instead:

```text
LLM
 |
 | "I need get_weather"
 v
Application / Agent
 |
 | executes tool
 v
MCP Server
 |
 v
External Service
 |
 v
Tool Result
 |
 v
LLM
 |
 v
Final Answer
```

Important concept:

> The LLM decides what tool to call; the application executes the tool.

---

## 20. Tool Calling vs RAG

### RAG

RAG retrieves relevant information from a knowledge source.

```text
Question
   |
   v
Embedding
   |
   v
Vector Database
   |
   v
Relevant Documents
   |
   v
LLM
```

### Tool Calling

Tool calling performs an operation or retrieves information through a capability.

```text
Question
   |
   v
LLM
   |
   v
Tool
   |
   v
Result
   |
   v
LLM
```

Simple rule:

```text
RAG  = Give the model relevant knowledge
Tool = Give the model a capability
```

---

## 21. What MCP Adds

MCP stands for:

```text
Model Context Protocol
```

It provides a standardized way for applications/agents to connect with tools and capabilities.

In this project:

```text
LangChain Agent
       |
       v
MCP Client Adapter
       |
       +----------------+
       |                |
       v                v
Weather MCP         Email MCP
Server              Server
       |                |
       v                v
    Tavily            Resend
```

---

## 22. MCP vs Agent

### MCP

MCP standardizes how tools/capabilities are exposed and connected.

### Agent

The agent decides what action to take.

For example:

```text
User:
"What is the weather in Delhi and email it to me?"
```

The agent can decide to:

```text
1. Call get_weather
2. Get the weather result
3. Call send_email
4. Send the result
5. Return confirmation
```

MCP provides the tools.

The agent provides the decision-making/orchestration.

---

## 23. LangChain vs LangGraph vs MCP

```text
                 AI Application
                       |
                       v
                  LangChain
                       |
                       v
                    Agent
                       |
                       v
                  LangGraph
              orchestration/state
                       |
                       v
                     MCP
              tool connectivity
                  /         \
                 /           \
                v             v
         Weather Tool     Email Tool
              |                |
              v                v
            Tavily           Resend
```

- **LangChain** — abstractions for models, tools, agents, prompts, retrievers, etc.
- **LangGraph** — graph-based execution and stateful agent orchestration.
- **MCP** — standard protocol for connecting applications/agents to tools and resources.

---

## 24. Troubleshooting

### `McpError: Connection closed`

The MCP subprocess may have exited before completing the MCP handshake.

Test each server:

```powershell
uv run python .\servers\weather_server.py
```

```powershell
uv run python .\servers\email_server.py
```

A stdio server may simply wait without printing anything. That is normal.

### OpenAI 401

If you see:

```text
Your API key has expired.
```

create a new key and update:

```env
OPENAI_API_KEY=...
```

### Weather tool: `result` local variable

Use:

```python
try:
    result = tavily_client.search(
        query=query,
        max_results=3
    )
except Exception as e:
    return f"Weather search failed for {city}: {e}"

results = result.get("results", [])
```

### Resend domain not verified

Do not use an arbitrary Gmail address as the sender.

For development:

```env
SENDER_EMAIL=onboarding@resend.dev
```

For production, use a verified sending domain.

---

## 25. Security

Never commit:

```text
.env
```

Never hard-code:

```python
OPENAI_API_KEY = "..."
TAVILY_API_KEY = "..."
RESEND_API_KEY = "..."
```

Use environment variables:

```python
os.getenv("OPENAI_API_KEY")
os.getenv("TAVILY_API_KEY")
os.getenv("RESEND_API_KEY")
```

If a secret is accidentally committed, rotate/revoke it immediately.

---

## 26. Learning Points

This project demonstrates:

- Python virtual environments
- uv package management
- environment variables
- OpenAI API
- LangChain
- LangChain agents
- LangGraph agent execution
- Tool calling
- MCP
- FastMCP
- MCP stdio transport
- MCP client adapters
- External API integration
- Tavily web search
- Resend email
- Multi-tool agents
- Agent tool selection
- Tool execution and tool results

---

## 27. Successful Project Milestone

The project has successfully demonstrated both tools:

```text
                  MCP TOOL-CALLING AGENT
                           |
             +-------------+-------------+
             |                           |
             v                           v
       WEATHER TOOL                 EMAIL TOOL
             |                           |
             v                           v
       MCP Server                    MCP Server
             |                           |
             v                           v
          Tavily                       Resend
             |                           |
             +-------------+-------------+
                           |
                           v
                      AI Agent
                           |
                           v
                      OpenAI LLM
```

Both tools have been successfully connected and tested.

---

## 28. Recommended Next Steps

### Phase 1 — Multi-tool Agent

Support requests such as:

```text
Get the weather in Delhi and send the result to my email.
```

Expected flow:

```text
User
 |
 v
Agent
 |
 +----> get_weather
 |          |
 |          v
 |        Tavily
 |          |
 |          v
 |       weather
 |
 +----> send_email
            |
            v
          Resend
            |
            v
        Email sent
```

### Phase 2 — LangGraph

Build the workflow manually using LangGraph nodes, edges, and state.

### Phase 3 — Agent + RAG

Combine:

```text
RAG + Tools + Agent
```

### Phase 4 — More MCP Tools

Add:

- database tool
- file-system tool
- calculator tool
- API tool

### Phase 5 — Production

Learn:

- FastAPI
- Docker
- AWS
- authentication
- logging
- monitoring
- evaluation
- deployment

---

## 29. Final Architecture

```text
                         USER
                           |
                           v
                    +-------------+
                    | LangChain   |
                    | Agent       |
                    +------+------+
                           |
                           v
                    +-------------+
                    | OpenAI LLM  |
                    +------+------+
                           |
                    Tool decision
                           |
              +------------+------------+
              |                         |
              v                         v
       get_weather                send_email
              |                         |
              v                         v
      Weather MCP Server         Email MCP Server
              |                         |
              v                         v
           Tavily                    Resend
              |                         |
              +------------+------------+
                           |
                           v
                      Tool Result
                           |
                           v
                       OpenAI LLM
                           |
                           v
                     FINAL ANSWER
```

---

## Summary

This project demonstrates how to build an AI agent that can:

- understand a user's request
- decide whether a tool is required
- select an appropriate tool
- call an MCP tool
- receive the tool result
- use external services through MCP
- return a natural-language response

The key mental model is:

```text
LLM       = Decision maker
Agent     = Orchestrator
MCP       = Tool connectivity standard
Tool      = Capability / action
Tavily    = Web search capability
Resend    = Email capability
LangGraph = Agent execution / orchestration
```

This project is now a solid foundation for building a more advanced **multi-tool AI agent**.
