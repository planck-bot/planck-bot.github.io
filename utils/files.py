import json
import aiofiles
import aiosqlite
from typing import Dict, Any, List, Optional

async def read_json(file_path: str) -> Optional[Dict[str, Any]]:
    try:
        async with aiofiles.open(file_path, mode='r') as f:
            contents = await f.read()
            return json.loads(contents)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

DB_PATH = f"data/database.db"

async def _ensure_table_exists(db: aiosqlite.Connection, table: str, columns: Dict[str, Any] = None):
    # First, create the table if it doesn't exist with basic structure
    await db.execute(f'''
        CREATE TABLE IF NOT EXISTS {table} (
            id INTEGER PRIMARY KEY
        )
    ''')
    
    if columns:
        # Get existing columns
        cursor = await db.execute(f"PRAGMA table_info({table})")
        existing_columns = {row[1] for row in await cursor.fetchall()}
        
        # Add missing columns
        for col_name, value in columns.items():
            if col_name not in existing_columns:
                # Infer column type from value
                if col_name == "id":
                    continue  # ID column already exists
                elif isinstance(value, int):
                    col_type = "INTEGER DEFAULT 0"
                elif isinstance(value, float):
                    col_type = "REAL DEFAULT 0.0"
                elif isinstance(value, str):
                    col_type = "TEXT DEFAULT ''"
                else:
                    col_type = "TEXT DEFAULT ''"
                
                await db.execute(f'''
                    ALTER TABLE {table} ADD COLUMN {col_name} {col_type}
                ''')

async def insert_data(table: str, data: Dict[str, Any]) -> int:
    """
    Insert or update data in a table (upsert).
    If a record with the same ID exists, it updates it. If not, it inserts a new record.
    
    Args:
        table: Table name
        data: Dictionary of column_name: value (must include "id")
        
    Returns:
        The row ID of the inserted/updated row
    """
    if "id" not in data:
        raise ValueError("Data must include an 'id' field")
    
    async with aiosqlite.connect(DB_PATH) as db:
        await _ensure_table_exists(db, table, data)
        
        cursor = await db.execute(f'SELECT id FROM {table} WHERE id = ?', (data["id"],))
        exists = await cursor.fetchone()
        
        if exists:
            update_data_dict = {k: v for k, v in data.items() if k != "id"}
            if update_data_dict:  # Only update if there's data to update
                set_clause = ", ".join([f"{col} = ?" for col in update_data_dict.keys()])
                await db.execute(f'''
                    UPDATE {table} SET {set_clause} WHERE id = ?
                ''', list(update_data_dict.values()) + [data["id"]])
            await db.commit()
            return data["id"]
        else:
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data.values()])
            
            cursor = await db.execute(f'''
                INSERT INTO {table} ({columns}) VALUES ({placeholders})
            ''', list(data.values()))
            await db.commit()
            return cursor.lastrowid

async def update_data(table: str, data: Dict[str, Any], where_column: str, where_value: Any):
    """
    Update data in a table.
    
    Args:
        table: Table name
        data: Dictionary of column_name: new_value
        where_column: Column name for WHERE clause
        where_value: Value for WHERE clause
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await _ensure_table_exists(db, table, data)
        
        set_clause = ", ".join([f"{col} = ?" for col in data.keys()])
        
        await db.execute(f'''
            UPDATE {table} SET {set_clause} WHERE {where_column} = ?
        ''', list(data.values()) + [where_value])
        await db.commit()

async def get_user_data(table: str, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a single user's data from a table.
    
    Args:
        table: Table name
        user_id: Discord user ID
        
    Returns:
        Dictionary with column names as keys and values, or None if not found
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await _ensure_table_exists(db, table)
        
        async with db.execute(f'SELECT * FROM {table} WHERE id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                column_names = [description[0] for description in cursor.description]
                return dict(zip(column_names, row))
            return None

async def get_all_data(table: str) -> List[Dict[str, Any]]:
    """
    Get all data from a table.
    
    Args:
        table: Table name
        
    Returns:
        List of dictionaries, each with column names as keys
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await _ensure_table_exists(db, table)
        
        async with db.execute(f'SELECT * FROM {table}') as cursor:
            rows = await cursor.fetchall()
            if rows:
                column_names = [description[0] for description in cursor.description]
                return [dict(zip(column_names, row)) for row in rows]
            return []

async def delete_user_data(table: str, user_id: int):
    """
    Delete a user's data from a table.
    
    Args:
        table: Table name
        user_id: Discord user ID
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await _ensure_table_exists(db, table)
        
        await db.execute(f'DELETE FROM {table} WHERE id = ?', (user_id,))
        await db.commit()

async def user_exists(table: str, user_id: int) -> bool:
    """
    Check if a user exists in a table.
    
    Args:
        table: Table name
        user_id: Discord user ID
        
    Returns:
        True if user exists, False otherwise
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await _ensure_table_exists(db, table)
        
        async with db.execute(f'SELECT 1 FROM {table} WHERE id = ? LIMIT 1', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row is not None

async def add_data(table: str, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add values to existing columns for a user. Creates user with 0 values if they don't exist.
    Mainly for incrementing/adding to currencies, scores, etc.
    
    Args:
        table: Table name
        user_id: Discord user ID
        data: Dictionary of column_name: amount_to_add
        
    Returns:
        Dictionary with the updated values
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await _ensure_table_exists(db, table, data)
        
        current_data = await get_user_data(table, user_id)
        if current_data is None:
            current_data = {"id": user_id}
            for col_name in data.keys():
                current_data[col_name] = 0
            await insert_data(table, current_data)
        
        updated_data = {"id": user_id}
        for col_name, add_amount in data.items():
            current_value = current_data.get(col_name, 0)
            updated_data[col_name] = current_value + add_amount
        
        await insert_data(table, updated_data)
        
        return updated_data