Here’s your text formatted and tidied into a clean `README.md` file — only grammatical corrections and Markdown structure applied, no content rewritten or removed:

---

# MCP Server & Client Setup Guide

## Pre-requisite

Install **uv**:
[https://docs.astral.sh/uv/getting-started/installation/#installation-methods](https://docs.astral.sh/uv/getting-started/installation/#installation-methods)

Set up your database server:
Either:

* Follow Kai's way, or
* Run `docker compose up` in the terminal where you placed the `docker-compose.yaml`.

For context, I am using:

```bash
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "root"
```

---

## Step 1: Set Up MCP Server

Create a parent directory (for example, `MCP`).
In the MCP directory, open a terminal.

Run:

```bash
uv init mcp_server
cd ./mcp_server
```

(If you want to use a virtual environment)

```bash
uv venv
uv .venv\Scripts\activate
```

(Else skip this step)

Install dependencies:

```bash
uv add fastmcp aiomysql
```

Rename your `main.py` to `server.py` and replace its content with the `server.py` I shared.
**Reminder:** My database schema might differ from yours; hence the database tools (labeled as *Main MCP Tools*) might differ from yours.

---

## Step 2: Set Up MCP Client

Go back to the parent directory:

```bash
cd ..
```

Initialize a new client project:

```bash
uv init mcp_client
cd ./mcp_fastmcp_client  # or any name you prefer
```

(If you want to use a virtual environment)

```bash
uv venv
uv .venv\Scripts\activate
```

(Else skip this step)

Install dependencies:

```bash
uv add fastmcp google-genai
```

Rename your `main.py` to `client.py` and replace its content with the `client.py` I shared.

---

## Step 3: Run the MCP Server

Open a terminal where your `server.py` is located and run:

```bash
uv run server.py
```

Once the server is running, you can leave it running in the background.

---

## Step 4: Run the MCP Client

Open a terminal where your `client.py` is located and run:

```bash
uv run client.py
```

If your connection is successful, you will see a chat-like interface appearing in your terminal.

---
