# MCP Tool Calling Agent

A hands-on AI agent project demonstrating **OpenAI + LangChain Agent +
LangGraph + MCP + Tavily + Resend + persistent conversation memory**.

The project exposes two MCP tools:

1.  **Weather Tool** --- searches the web through Tavily for current
    weather information.
2.  **Email Tool** --- sends an email through Resend.

The agent can answer normal questions, select tools, call multiple tools
for one request, maintain conversation context, persist conversation
data in SQLite, and summarize older conversation when the context
becomes large.

------------------------------------------------------------------------

## 1. Project Goal

The goal is to understand the complete flow of LLM tool calling with MCP
and then build toward a stateful AI agent.

``` text
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

------------------------------------------------------------------------

## 2. Technologies Used

  Technology      Purpose
  --------------- --------------------------------------
  Python          Application language
  uv              Package/environment management
  OpenAI          LLM used by the agent
  LangChain       Agent framework
  LangGraph       Agent execution/orchestration
  MCP             Standard protocol for exposing tools
  FastMCP         MCP server implementation
  Tavily          Web search used by weather tool
  Resend          Email delivery
  SQLite          Persistent conversation storage
  python-dotenv   Environment variables

------------------------------------------------------------------------

## 3. Project Structure

``` text
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
│   ├── agent.py
│   └── memory.py
│
├── servers/
│   ├── __init__.py
│   ├── weather_server.py
│   └── email_server.py
│
└── conversation.db
```

`conversation.db` contains local conversation data and **must not be
pushed to GitHub**.

Recommended `.gitignore`:

``` gitignore
.env
.venv/
__pycache__/
*.pyc
conversation.db
*.db
```

### File descriptions

-   `.env` --- API keys/configuration.
-   `client/agent.py` --- MCP connections, tool discovery, agent
    creation, chatbot loop and memory/context handling.
-   `client/memory.py` --- SQLite conversation-memory implementation.
-   `servers/weather_server.py` --- exposes `get_weather(city)` and uses
    Tavily.
-   `servers/email_server.py` --- exposes
    `send_email(to, subject, body)` and uses Resend.
-   `conversation.db` --- local runtime conversation database.

------------------------------------------------------------------------

## 4. Prerequisites

-   Python 3.13 or compatible Python
-   uv
-   OpenAI API key
-   Tavily API key
-   Resend API key

------------------------------------------------------------------------

## 5. Create the Project

``` powershell
uv init mcp-tool-calling-agent
cd mcp-tool-calling-agent
uv venv
.venv\Scripts\Activate.ps1
```

------------------------------------------------------------------------

## 6. Install Dependencies

``` powershell
uv add openai python-dotenv tavily-python resend mcp langchain-mcp-adapters langchain langchain-openai
```

------------------------------------------------------------------------

## 7. Environment Variables

Create `.env`:

``` env
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
RESEND_API_KEY=your_resend_api_key
SENDER_EMAIL=onboarding@resend.dev
```

Never commit `.env`.

------------------------------------------------------------------------

## 8. Weather MCP Server

File:

``` text
servers/weather_server.py
```

Tool:

``` python
@mcp.tool()
def get_weather(city: str) -> str:
```

The tool receives a city, creates a weather search query, calls Tavily,
extracts search results, and returns the result to the MCP client.

Example query:

``` text
current weather in Delhi today
```

The server uses stdio:

``` python
mcp.run(transport="stdio")
```

Because stdout is reserved for MCP protocol communication, debug
messages should use stderr:

``` python
print(f"Searching weather for: {city}", file=sys.stderr)
```

------------------------------------------------------------------------

## 9. Email MCP Server

File:

``` text
servers/email_server.py
```

Tool:

``` python
@mcp.tool()
def send_email(to: str, subject: str, body: str) -> str:
```

The tool receives the recipient, subject and body, sends the message
through Resend, and returns the result.

------------------------------------------------------------------------

## 10. MCP Client

File:

``` text
client/agent.py
```

The client connects to both MCP servers:

``` python
client = MultiServerMCPClient({
    "weather": {
        "command": "uv",
        "args": ["run", "python", "servers/weather_server.py"],
        "transport": "stdio"
    },
    "email": {
        "command": "uv",
        "args": ["run", "python", "servers/email_server.py"],
        "transport": "stdio"
    }
})
```

Tools are discovered with:

``` python
tools = await client.get_tools()
```

Successful output:

``` text
Available MCP tools:
   - get_weather
   - send_email
```

------------------------------------------------------------------------

## 11. Creating the Agent

The project uses:

``` python
from langchain.agents import create_agent
```

Example:

``` python
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

It can also call multiple tools for one user request.

------------------------------------------------------------------------

## 12. OpenAI Model

``` python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0
)
```

The key comes from:

``` env
OPENAI_API_KEY=...
```

------------------------------------------------------------------------

## 13. Running the Project

Preferred package-style command:

``` powershell
python -m client.agent
```

or:

``` powershell
uv run python -m client.agent
```

Expected startup:

``` text
======================================
       MCP AI CHATBOT STARTED
======================================
Type your question.
Press Ctrl+C to exit.

You:
```

The application continues running until:

``` text
Ctrl+C
```

------------------------------------------------------------------------

## 14. Continuous Chatbot

The application now behaves like a normal chatbot:

``` text
while True
    |
    v
Read question
    |
    v
Agent
    |
    v
Answer
    |
    v
Read next question
    |
    v
...
```

This replaced the earlier one-question execution model.

------------------------------------------------------------------------

## 15. Conversation Memory

The agent maintains context between questions.

Example:

``` text
You: What is the weather in Delhi?

AI: Delhi is currently ...

You: Is that temperature hot?

AI: Yes, that temperature ...
```

The second question can use the previous context.

------------------------------------------------------------------------

## 16. Persistent SQLite Memory

File:

``` text
client/memory.py
```

The project creates:

``` text
conversation.db
```

automatically.

Conceptually:

``` text
Chatbot
   |
   v
Conversation
   |
   v
SQLite
   |
   v
conversation.db
```

When the application restarts, stored conversation memory can be loaded
again.

**Do not push `conversation.db` to GitHub.**

------------------------------------------------------------------------

## 17. Sliding-Window Memory

An unlimited conversation eventually becomes too large for efficient LLM
context.

Problems with sending the entire history:

-   larger context
-   higher token usage
-   slower responses
-   higher cost
-   eventual context-window limitations

Current configuration:

``` python
MAX_MESSAGES = 10
SUMMARY_TRIGGER = 20
```

The concept is:

``` text
Old conversation
       |
       v
Summary
       +
Recent messages
       |
       v
LLM
```

Only recent messages remain in the active conversation window after
summarization.

------------------------------------------------------------------------

## 18. Automatic Conversation Summarization

When the configured threshold is reached, older messages are summarized.

The application prints:

``` text
[Memory] Summarizing older conversation...
[Memory] Summary updated.
```

Flow:

``` text
Conversation
     |
     v
Threshold reached
     |
     v
Older messages
     |
     v
LLM summarization
     |
     v
Summary
     +
Recent messages
     |
     v
Agent context
```

The summary attempts to preserve:

-   important user information
-   important decisions
-   important tasks
-   important context
-   important tool results
-   information needed for future questions

This demonstrates practical context management for long-running agents.

------------------------------------------------------------------------

## 19. Memory Configuration

In `client/agent.py`:

``` python
MAX_MESSAGES = 10
SUMMARY_TRIGGER = 20
```

`MAX_MESSAGES` controls the recent-message window.

`SUMMARY_TRIGGER` controls when older messages are summarized.

A single user request involving a tool can create multiple LangChain
messages, so the threshold can be reached faster than the number of user
questions suggests.

------------------------------------------------------------------------

## 20. Test 1 --- Normal Question

``` text
What is Python?
```

Expected flow:

``` text
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

No MCP tool is required.

------------------------------------------------------------------------

## 21. Test 2 --- Weather Tool

``` text
What is the current weather in Delhi?
```

Expected flow:

``` text
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
get_weather("Delhi")
  |
  v
Weather MCP
  |
  v
Tavily
  |
  v
Weather Result
  |
  v
OpenAI
  |
  v
Final Answer
```

This test was successfully completed.

------------------------------------------------------------------------

## 22. Test 3 --- Email Tool

``` text
Send an email to delivered@resend.dev
with subject "Test Email"
and body "Hello from my MCP project."
```

Expected flow:

``` text
User
  |
  v
Agent
  |
  v
send_email(...)
  |
  v
Email MCP
  |
  v
Resend
  |
  v
Email Result
  |
  v
OpenAI
  |
  v
Final Answer
```

This test was successfully completed.

------------------------------------------------------------------------

## 23. Test 4 --- Multiple Tools in One Request

``` text
What is the current weather in Delhi and send
the weather information to delivered@resend.dev
with subject "Delhi Weather".
```

The agent can:

``` text
1. Call get_weather
2. Receive the weather result
3. Call send_email
4. Send the weather information
5. Return the final response
```

Flow:

``` text
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
 |     Weather Result
 |
 +----> send_email
            |
            v
          Resend
            |
            v
        Email Sent
            |
            v
        Final Answer
```

This demonstrates multi-tool orchestration.

------------------------------------------------------------------------

## 24. Test 5 --- Conversation Context

Ask:

``` text
What is the current weather in Delhi?
```

Then:

``` text
Is that temperature hot?
```

Then:

``` text
What city did we just check?
```

These test short-term conversation context.

------------------------------------------------------------------------

## 25. Test 6 --- Summarization

Ask multiple questions:

``` text
What is Python?
What is Java?
What is an API?
What is REST?
What is LangChain?
What is LangGraph?
What is MCP?
How is MCP different from tool calling?
What is RAG?
What is an AI agent?
```

Continue until you see:

``` text
[Memory] Summarizing older conversation...
[Memory] Summary updated.
```

Then ask:

``` text
What topics have we discussed so far?
```

This tests summary-based context management.

------------------------------------------------------------------------

## 26. Resend Testing

For development:

``` env
SENDER_EMAIL=onboarding@resend.dev
```

Test recipient:

``` text
delivered@resend.dev
```

For production, configure and verify a domain that you control according
to Resend's requirements.

------------------------------------------------------------------------

## 27. Tool Calling Concept

The LLM does not execute the Python function itself.

``` text
LLM
 |
 | decides a tool is needed
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

Key concept:

> The LLM decides what tool to call; the application executes the tool.

------------------------------------------------------------------------

## 28. Tool Calling vs RAG

### RAG

``` text
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

``` text
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

``` text
RAG  = Give the model relevant knowledge
Tool = Give the model a capability
```

------------------------------------------------------------------------

## 29. What MCP Adds

MCP stands for:

``` text
Model Context Protocol
```

It provides a standardized way for applications/agents to connect with
tools and capabilities.

``` text
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

------------------------------------------------------------------------

## 30. MCP vs Agent

### MCP

MCP standardizes how tools/capabilities are exposed and connected.

### Agent

The agent decides what action to take.

Example:

``` text
User:
"What is the weather in Delhi and email it to me?"
```

The agent can:

``` text
1. Call get_weather
2. Get the weather result
3. Call send_email
4. Send the result
5. Return confirmation
```

MCP provides the tools.

The agent provides decision-making/orchestration.

------------------------------------------------------------------------

## 31. LangChain vs LangGraph vs MCP

``` text
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

-   **LangChain** --- abstractions for models, tools, agents, prompts,
    retrievers, etc.
-   **LangGraph** --- graph-based execution and stateful agent
    orchestration.
-   **MCP** --- standard protocol for connecting applications/agents to
    tools and resources.

------------------------------------------------------------------------

## 32. Current Memory Architecture

``` text
                         User
                           |
                           v
                    +-------------+
                    | AI Agent    |
                    +------+------+
                           |
              +------------+------------+
              |                         |
              v                         v
      Recent Messages             Summary Memory
              |                         |
              +------------+------------+
                           |
                           v
                       LLM Context
                           |
                           v
                    Tool / Final Answer
```

For longer-running agents, a practical architecture is:

``` text
Recent conversation
        +
Compressed historical summary
        +
Retrieved long-term memories when needed
```

The current project demonstrates the first two concepts.

------------------------------------------------------------------------

## 33. Troubleshooting

### `McpError: Connection closed`

Test:

``` powershell
uv run python .\servers\weather_server.py
```

``` powershell
uv run python .\servers\email_server.py
```

A stdio server may wait without printing anything. That is normal.

### OpenAI 401

Update:

``` env
OPENAI_API_KEY=...
```

### Weather tool: `result` local variable

Use:

``` python
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

For development:

``` env
SENDER_EMAIL=onboarding@resend.dev
```

For production, use a verified sending domain.

### `ModuleNotFoundError: No module named 'client'`

If using:

``` python
from client.memory import ConversationMemory
```

run from the project root:

``` powershell
python -m client.agent
```

### `sqlite3.OperationalError: no such column: summary`

This means an older `conversation.db` was created before the summary
column existed.

For this learning project, if old memory is not needed:

``` powershell
Remove-Item .\conversation.db
```

Then:

``` powershell
python -m client.agent
```

### `AttributeError: 'HumanMessage' object has no attribute 'get'`

LangChain returns message objects such as:

``` text
HumanMessage
AIMessage
ToolMessage
```

They are not ordinary dictionaries.

Use:

``` python
message.type
message.content
```

instead of:

``` python
message.get("role")
message.get("content")
```

------------------------------------------------------------------------

## 34. Security

Never commit:

``` text
.env
conversation.db
*.db
```

Never hard-code API keys.

Use:

``` python
os.getenv("OPENAI_API_KEY")
os.getenv("TAVILY_API_KEY")
os.getenv("RESEND_API_KEY")
```

If a secret is accidentally committed, rotate/revoke it immediately.

Conversation data should remain outside the public Git repository.

------------------------------------------------------------------------

## 35. Git Workflow

Check:

``` powershell
git status
```

Add source changes:

``` powershell
git add client/agent.py client/memory.py
```

Commit:

``` powershell
git commit -m "Add persistent conversation memory and summarization"
```

Push:

``` powershell
git push
```

Do not add:

``` text
.env
conversation.db
```

to Git.

------------------------------------------------------------------------

## 36. Learning Points

This project demonstrates:

-   Python virtual environments
-   uv package management
-   environment variables
-   OpenAI API
-   LangChain
-   LangChain agents
-   LangGraph agent execution
-   Tool calling
-   MCP
-   FastMCP
-   MCP stdio transport
-   MCP client adapters
-   External API integration
-   Tavily web search
-   Resend email
-   Multi-tool agents
-   Agent tool selection
-   Tool execution and results
-   Continuous chatbot interaction
-   Conversation context
-   SQLite persistence
-   Sliding-window memory
-   Conversation summarization
-   Context management

------------------------------------------------------------------------

## 37. Successful Project Milestone

Completed milestones:

-   MCP Weather server
-   MCP Email server
-   MCP tool discovery
-   OpenAI tool calling
-   Multiple tools in one request
-   Continuous chatbot
-   Conversation context
-   SQLite persistence
-   Sliding-window context
-   Automatic summarization

Current architecture:

``` text
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
                           |
                           v
                  Conversation Memory
                           |
                +----------+----------+
                |                     |
                v                     v
             SQLite              Summary
```

------------------------------------------------------------------------

## 38. Recommended Next Steps

### Phase 1 --- MCP + Memory

Completed:

``` text
MCP tools
   +
Agent
   +
Continuous chatbot
   +
SQLite memory
   +
Sliding-window context
   +
Conversation summarization
```

### Phase 2 --- LangGraph

Next, rebuild the workflow using:

-   State
-   Nodes
-   Edges
-   START
-   END
-   Conditional edges
-   ToolNode
-   Agent loops
-   Memory/checkpointing

Target:

``` text
START
  |
  v
Agent Node
  |
  +------ No tool ------> END
  |
  +------ Tool needed
             |
             v
         Tool Node
             |
             v
           Agent
             |
             v
            END
```

### Phase 3 --- Agent + RAG

Combine:

``` text
RAG + Tools + Agent
```

### Phase 4 --- More MCP Tools

Possible additions:

-   database tool
-   file-system tool
-   calculator tool
-   API tool

### Phase 5 --- Production

Learn:

-   FastAPI
-   Docker
-   AWS
-   authentication
-   logging
-   monitoring
-   evaluation
-   deployment

------------------------------------------------------------------------

## 39. Final Architecture

``` text
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
                    | Memory      |
                    | Recent +    |
                    | Summary     |
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

------------------------------------------------------------------------

## Summary

``` text
LLM       = Decision maker
Agent     = Orchestrator
MCP       = Tool connectivity standard
Tool      = Capability / action
Tavily    = Web search capability
Resend    = Email capability
Memory    = Conversation state
SQLite    = Persistent local storage
Summary   = Compressed historical context
LangGraph = Agent execution / orchestration
```

This project is now a solid foundation for building a **multi-tool,
stateful AI agent** and is ready for the next major step: **LangGraph
State, Nodes, Edges and conditional agent workflows**.
