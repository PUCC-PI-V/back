import os
from pathlib import Path

from dotenv import load_dotenv
import asyncio
import mysql.connector


env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "")
DB_PORT = int(os.getenv("DB_PORT", 3306))
 
 
conn = None


async def connect_db():
	"""Create a persistent DB connection on startup (runs in a thread)."""
	global conn
	if conn is not None:
		try:
			if conn.is_connected():
				return
		except Exception:
			pass

	def _connect():
		print(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)
		return mysql.connector.connect(
			host=DB_HOST,
			user=DB_USER,
			password=DB_PASSWORD,
			database=DB_NAME or None,
			port=DB_PORT,
		)

	conn = await asyncio.to_thread(_connect)


async def disconnect_db():
	"""Close the persistent DB connection on shutdown (runs in a thread)."""
	global conn
	if conn is None:
		return

	def _disconnect(c):
		try:
			if c.is_connected():
				c.close()
		except Exception:
			pass

	await asyncio.to_thread(_disconnect, conn)
	conn = None
