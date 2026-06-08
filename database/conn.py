import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
import asyncio
import mysql.connector


env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def _load_db_settings():
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url.startswith("mysql://"):
        parsed = urlparse(database_url)
        return {
            "host": parsed.hostname or "localhost",
            "user": parsed.username or "root",
            "password": parsed.password or "",
            "database": (parsed.path or "").lstrip("/") or "viboraink",
            "port": parsed.port or 3306,
        }

    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "") or "viboraink",
        "port": int(os.getenv("DB_PORT", 3306)),
    }


_db = _load_db_settings()
DB_HOST = _db["host"]
DB_USER = _db["user"]
DB_PASSWORD = _db["password"]
DB_NAME = _db["database"]
DB_PORT = _db["port"]

ADMIN_EMAIL = "admin@viboraink.com"
ADMIN_PASSWORD = "admin123"
ADMIN_TABLE = "User"

conn = None


def _column_exists(cur, table: str, column: str) -> bool:
    cur.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s
        """,
        (DB_NAME, table, column),
    )
    return cur.fetchone()[0] > 0


def _migrate_budget_tables(cur):
    if _column_exists(cur, "usuario", "cpf"):
        cur.execute("ALTER TABLE `usuario` DROP COLUMN `cpf`")
    if _column_exists(cur, "usuario", "password"):
        cur.execute("ALTER TABLE `usuario` DROP COLUMN `password`")
    if _column_exists(cur, "usuario", "senha"):
        cur.execute("ALTER TABLE `usuario` DROP COLUMN `senha`")

    if not _column_exists(cur, "tatuagem", "estilo"):
        cur.execute(
            "ALTER TABLE `tatuagem` ADD COLUMN `estilo` VARCHAR(100) NOT NULL DEFAULT ''"
        )
    if _column_exists(cur, "tatuagem", "area") and not _column_exists(
        cur, "tatuagem", "area_tatuada"
    ):
        cur.execute(
            "ALTER TABLE `tatuagem` CHANGE `area` `area_tatuada` VARCHAR(100) NOT NULL"
        )
    if not _column_exists(cur, "tatuagem", "descricao"):
        cur.execute("ALTER TABLE `tatuagem` ADD COLUMN `descricao` TEXT NULL")
        cur.execute("UPDATE `tatuagem` SET `descricao` = '' WHERE `descricao` IS NULL")
        cur.execute(
            "ALTER TABLE `tatuagem` MODIFY `descricao` TEXT NOT NULL"
        )
    if not _column_exists(cur, "tatuagem", "estimativa_valor"):
        cur.execute(
            "ALTER TABLE `tatuagem` ADD COLUMN `estimativa_valor` INT NULL"
        )
    if not _column_exists(cur, "tatuagem", "dificuldade_ia"):
        cur.execute(
            "ALTER TABLE `tatuagem` ADD COLUMN `dificuldade_ia` VARCHAR(50) NULL"
        )
    if not _column_exists(cur, "tatuagem", "justificativa_ia"):
        cur.execute("ALTER TABLE `tatuagem` ADD COLUMN `justificativa_ia` TEXT NULL")


def _bootstrap_db():
    bootstrap_conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
    )
    try:
        cur = bootstrap_conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`")
        cur.execute(f"USE `{DB_NAME}`")
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS `{ADMIN_TABLE}` (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL
            )
            """
        )
        cur.execute(
            f"SELECT id FROM `{ADMIN_TABLE}` WHERE email = %s LIMIT 1",
            (ADMIN_EMAIL,),
        )
        if cur.fetchone() is None:
            cur.execute(
                f"INSERT INTO `{ADMIN_TABLE}` (email, password) VALUES (%s, %s)",
                (ADMIN_EMAIL, ADMIN_PASSWORD),
            )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS `usuario` (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                data_nasc VARCHAR(20) NOT NULL,
                telefone VARCHAR(30) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS `tatuagem` (
                id_tatuagem INT AUTO_INCREMENT PRIMARY KEY,
                cliente VARCHAR(255) NOT NULL,
                tamanho VARCHAR(50) NOT NULL,
                sombreamento TINYINT NOT NULL,
                colorido TINYINT NOT NULL,
                estilo VARCHAR(100) NOT NULL,
                area_tatuada VARCHAR(100) NOT NULL,
                regiao_especifica VARCHAR(100) NOT NULL,
                descricao TEXT NOT NULL,
                estimativa_valor INT NULL,
                dificuldade_ia VARCHAR(50) NULL,
                justificativa_ia TEXT NULL
            )
            """
        )
        _migrate_budget_tables(cur)
        bootstrap_conn.commit()
        cur.close()
    finally:
        try:
            bootstrap_conn.close()
        except Exception:
            pass


def _connect():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
    )


async def connect_db():
    """Create a persistent DB connection on startup (runs in a thread)."""
    global conn
    if conn is not None:
        try:
            if conn.is_connected():
                return
        except Exception:
            pass

    await asyncio.to_thread(_bootstrap_db)
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
