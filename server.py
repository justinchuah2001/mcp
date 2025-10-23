# db_mcp_server.py

from typing import List, Optional, Dict, Literal
import datetime
import asyncio
import logging
import aiomysql
from fastmcp import FastMCP
import sys

logging.basicConfig(level=logging.INFO)
mcp = FastMCP("db_tools")

DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "root"


pool: aiomysql.Pool | None = None

async def init_db_pool():
    global pool
    pool = await aiomysql.create_pool(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        autocommit=True,
    )
    logging.info("Database pool initialized.")

async def close_pool():
    """Close the database pool gracefully."""
    global pool
    if pool:
        logging.info("Closing database pool...")
        pool.close()
        await pool.wait_closed()
        logging.info("Database pool closed.")
############------------------------Testing Tools------------------##############
@mcp.tool()
async def list_tables(schema: str) -> List[str]:
    """List tables in a given database."""
    if not schema.isidentifier():
        raise ValueError("Invalid schema name")
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = %s",
                (schema,),
            )
            return [r[0] for r in await cur.fetchall()]


@mcp.tool()
async def get_table_rows(schema: str, table: str, limit: int = 100) -> List[dict]:
    """
    Retrieve up to `limit` rows from the specified schema and table.
    """
    if not table.isidentifier() or not schema.isidentifier():
        raise ValueError("Invalid schema or table name")

    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(f"SELECT * FROM `{schema}`.`{table}` LIMIT %s", (limit,))
            return await cur.fetchall()

@mcp.tool()
async def list_databases() -> List[str]:
    """
    List all non-system databases.
    
    Returns:
        str: Concatenated database names without delimiter.
             Example: "incidentknowledge_base" represents 
             databases "incident" and "knowledge_base"
    """
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SHOW DATABASES")
            rows = [r[0] for r in await cur.fetchall()]
            return [r for r in rows if r not in ("information_schema", "mysql", "performance_schema", "sys")]

##########------------------------End Testing Tools------------------##############

##########- ------------------Main MCP Tools------------------##############
@mcp.tool()
async def create_incident(
    number: str,
    opened: datetime.datetime,
    short_description: str,
    description: str,
    resolution_code: str = None,
    resolution_notes: str = None,
    state: Literal['New', 'In Progress', 'Resolved', 'Closed'] = 'New',
    assigned_to: str = None
) -> str:
    """
    Creates a new incident record in the 'incident' database, 'incidents' table.
    """
    sql = """
    INSERT INTO incident.incidents 
    (number, opened, short_description, description, resolution_code, resolution_notes, state, assigned_to)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (number, opened, short_description, description, resolution_code, resolution_notes, state, assigned_to)
    
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            await conn.commit()
    
    return f"Incident {number} created successfully with state '{state}'."

@mcp.tool()
async def update_incident(
    number: str,
    short_description: str = None,
    description: str = None,
    resolution_code: str = None,
    resolution_notes: str = None,
    state: Literal['New', 'In Progress', 'Resolved', 'Closed'] = None,
    assigned_to: str = None
) -> str:
    """
    Updates an existing incident record in the 'incident' database, 'incidents' table.
    Only updates fields that are provided (not None).
    """
    # Build dynamic UPDATE query based on provided fields
    update_fields = []
    params = []
    
    if short_description is not None:
        update_fields.append("short_description = %s")
        params.append(short_description)
    if description is not None:
        update_fields.append("description = %s")
        params.append(description)
    if resolution_code is not None:
        update_fields.append("resolution_code = %s")
        params.append(resolution_code)
    if resolution_notes is not None:
        update_fields.append("resolution_notes = %s")
        params.append(resolution_notes)
    if state is not None:
        update_fields.append("state = %s")
        params.append(state)
    if assigned_to is not None:
        update_fields.append("assigned_to = %s")
        params.append(assigned_to)
    
    if not update_fields:
        return f"No fields provided to update for incident {number}."
    
    params.append(number)  # Add number for WHERE clause
    
    sql = f"""
    UPDATE incident.incidents 
    SET {', '.join(update_fields)}
    WHERE number = %s
    """
    
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            await conn.commit()
            rows_affected = cur.rowcount
    
    if rows_affected == 0:
        return f"No incident found with number {number}."
    
    return f"Incident {number} updated successfully. {rows_affected} row(s) affected."


@mcp.tool()
async def search_incidents(
    number: str = None,
    state: Literal['New', 'In Progress', 'Resolved', 'Closed'] = None,
    assigned_to: str = None,
    short_description_contains: str = None,
    limit: int = 10
) -> List[dict]:
    """
    Searches for incidents in the 'incident' database, 'incidents' table.
    Returns a list of matching incidents. All search parameters are optional.
    """
    where_clauses = []
    params = []
    
    if number is not None:
        where_clauses.append("number = %s")
        params.append(number)
    if state is not None:
        where_clauses.append("state = %s")
        params.append(state)
    if assigned_to is not None:
        where_clauses.append("assigned_to = %s")
        params.append(assigned_to)
    if short_description_contains is not None:
        where_clauses.append("short_description LIKE %s")
        params.append(f"%{short_description_contains}%")
    
    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    
    sql = f"""
    SELECT number, opened, short_description, description, 
           resolution_code, resolution_notes, state, assigned_to
    FROM incident.incidents
    {where_sql}
    ORDER BY opened DESC
    LIMIT %s
    """
    params.append(limit)
    
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            rows = await cur.fetchall()
            
            # Convert to list of dictionaries
            results = []
            for row in rows:
                results.append({
                    'number': row[0],
                    'opened': row[1].isoformat() if row[1] else None,
                    'short_description': row[2],
                    'description': row[3],
                    'resolution_code': row[4],
                    'resolution_notes': row[5],
                    'state': row[6],
                    'assigned_to': row[7]
                })
    
    return results

@mcp.tool()
async def search_kb(
    number: str = None,
    version: str = None,
    author: str = None,
    category: str = None,
    workflow: str = None,
    short_description_contains: str = None,
    limit: int = 10
) -> List[dict]:
    """
    Searches for knowledge base articles in the 'knowledge_base' database, 'kb' table.
    Returns a list of matching KB articles. All search parameters are optional.
    """
    where_clauses = []
    params = []
    
    if number is not None:
        where_clauses.append("number = %s")
        params.append(number)
    if version is not None:
        where_clauses.append("version = %s")
        params.append(version)
    if author is not None:
        where_clauses.append("author = %s")
        params.append(author)
    if category is not None:
        where_clauses.append("category = %s")
        params.append(category)
    if workflow is not None:
        where_clauses.append("workflow = %s")
        params.append(workflow)
    if short_description_contains is not None:
        where_clauses.append("short_description LIKE %s")
        params.append(f"%{short_description_contains}%")
    
    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    
    sql = f"""
    SELECT number, version, short_description, author, 
           category, workflow, updated
    FROM knowledge_base.kb
    {where_sql}
    ORDER BY updated DESC
    LIMIT %s
    """
    params.append(limit)
    
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            rows = await cur.fetchall()
            
            # Convert to list of dictionaries
            results = []
            for row in rows:
                results.append({
                    'number': row[0],
                    'version': row[1],
                    'short_description': row[2],
                    'author': row[3],
                    'category': row[4],
                    'workflow': row[5],
                    'updated': row[6].isoformat() if row[6] else None
                })
    
    return results

async def main():
    try:
        await init_db_pool()
    except Exception as e:
        print(f"DB pool init failed: {e}", file=sys.stderr)
        sys.exit(1)
    try:
       await mcp.run_async(transport="http", host="localhost", port=8000)
    finally:
        await close_pool()

if __name__ == "__main__":
    asyncio.run(main())