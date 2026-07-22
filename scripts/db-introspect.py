#!/usr/bin/env python3
"""
db-introspect.py — 数据库结构只读抽取（多数据库支持）

支持的数据库：MySQL / MariaDB / PostgreSQL / Oracle / Doris / SQL Server

用法：
  # 自动从项目代码中检测连接信息
  python db-introspect.py --auto-detect <project-dir>

  # 手动指定连接
  python db-introspect.py --type mysql --host 192.168.1.1 --user root --pass 123456 --db mydb
  python db-introspect.py --type postgres --host localhost --user postgres --db mydb
  python db-introspect.py --type sqlserver --host localhost --user sa --pass xxx --db mydb
  python db-introspect.py --type oracle --host localhost --port 1521 --user scott --pass tiger --sid ORCL
  python db-introspect.py --type doris --host localhost --port 9030 --user root --db mydb

安全保证：
  - 所有 SQL 查询均为系统 catalog / information_schema 的只读 SELECT
  - 绝不执行 INSERT / UPDATE / DELETE / DROP / CREATE / ALTER / TRUNCATE
  - 自动检测模式下仅读取配置文件，不修改任何代码
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime

# Windows: 强制 stdout/stderr 使用 UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ============================================================
# 连接信息自动检测
# ============================================================

def find_connection_info(project_dir: str) -> list[dict]:
    """
    扫描项目目录中的数据库连接信息。
    支持检测：
      - .env / .env.local / .env.development 文件
      - application.yml / application.properties (Spring)
      - database.yml / database.json / config.js / config.ts
      - Python settings.py / Django settings
      - 代码中的连接字符串常量
    """
    connections = []
    scanned_files = []

    # 要扫描的文件模式
    patterns = [
        # 环境变量文件
        "**/.env", "**/.env.*",
        # Spring Boot
        "**/application*.yml", "**/application*.yaml", "**/application*.properties",
        # Node.js / 前端
        "**/database.{yml,yaml,json,js,ts}",
        "**/config.{js,ts,json}",
        "**/knexfile.{js,ts}",
        "**/ormconfig.{js,ts,json}",
        # Python
        "**/settings.py", "**/settings/*.py",
        "**/alembic.ini",
        # Go
        "**/config.{yaml,yml,toml}",
        # 通用
        "**/db.config.*",
        "**/*database*.*",
    ]

    for pattern in patterns:
        import glob as g
        for filepath in g.glob(os.path.join(project_dir, pattern), recursive=True):
            if filepath in scanned_files:
                continue
            scanned_files.append(filepath)
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                found = _extract_from_content(content, filepath)
                connections.extend(found)
            except Exception:
                pass  # 无法读取就跳过

    # 去重
    unique = []
    seen = set()
    for c in connections:
        key = json.dumps(c, sort_keys=True, default=str)
        if key not in seen:
            seen.add(key)
            unique.append(c)

    return unique


def _extract_from_content(content: str, filepath: str) -> list[dict]:
    """从文件内容中提取数据库连接信息"""
    results = []

    # 模式 1: .env 格式 — DB_HOST=xxx, DB_PORT=xxx, 等
    env_patterns = [
        # MySQL
        (r'DB_HOST[=:]\s*["\']?([^"\'\s]+)', "host"),
        (r'MYSQL_HOST[=:]\s*["\']?([^"\'\s]+)', "host"),
        (r'DATABASE_HOST[=:]\s*["\']?([^"\'\s]+)', "host"),
        # Port
        (r'DB_PORT[=:]\s*["\']?(\d+)', "port"),
        (r'MYSQL_PORT[=:]\s*["\']?(\d+)', "port"),
        (r'DATABASE_PORT[=:]\s*["\']?(\d+)', "port"),
        # User
        (r'DB_USER(?:NAME)?[=:]\s*["\']?([^"\'\s]+)', "user"),
        (r'MYSQL_USER[=:]\s*["\']?([^"\'\s]+)', "user"),
        # Password
        (r'DB_PASS(?:WORD)?[=:]\s*["\']?([^"\'\s]+)', "password"),
        (r'MYSQL_PASSWORD[=:]\s*["\']?([^"\'\s]+)', "password"),
        (r'DBX_PASSWORD[=:]\s*["\']?([^"\'\s]+)', "password"),
        # Database name
        (r'DB_NAME[=:]\s*["\']?([^"\'\s]+)', "database"),
        (r'MYSQL_DATABASE[=:]\s*["\']?([^"\'\s]+)', "database"),
        (r'DATABASE_NAME[=:]\s*["\']?([^"\'\s]+)', "database"),
        # Type
        (r'DB_TYPE[=:]\s*["\']?([^"\'\s]+)', "db_type"),
        (r'DATABASE_TYPE[=:]\s*["\']?([^"\'\s]+)', "db_type"),
    ]

    env_data: dict[str, str] = {}
    for pattern, key in env_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match and key not in env_data:
            env_data[key] = match.group(1)

    # 模式 2: JDBC URL — jdbc:mysql://host:port/db
    jdbc_patterns = [
        (r'jdbc:mysql://([^:/]+)(?::(\d+))?/(\w+)', "mysql"),
        (r'jdbc:postgresql://([^:/]+)(?::(\d+))?/(\w+)', "postgresql"),
        (r'jdbc:oracle:thin:@(?://)?([^:/]+)(?::(\d+))?(?::|/)(\w+)', "oracle"),
        (r'jdbc:sqlserver://([^:/]+)(?::(\d+))?(?:;databaseName=(\w+))?', "sqlserver"),
    ]

    for pattern, db_type in jdbc_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            groups = match.groups()
            results.append({
                "db_type": db_type,
                "host": groups[0],
                "port": int(groups[1]) if groups[1] else _default_port(db_type),
                "database": groups[2] if len(groups) > 2 and groups[2] else "",
                "user": env_data.get("user", ""),
                "password": env_data.get("password", ""),
                "source": filepath,
            })

    # 模式 3: 通用连接字符串
    generic_patterns = [
        # mysql://user:pass@host:port/db
        (r'mysql://([^:]+):([^@]+)@([^:/]+)(?::(\d+))?/(\w+)', "mysql"),
        # postgresql://user:pass@host:port/db
        (r'postgres(?:ql)?://([^:]+):([^@]+)@([^:/]+)(?::(\d+))?/(\w+)', "postgresql"),
        # sqlite:///path/to/db
        (r'sqlite:///(.+)', "sqlite"),
    ]

    for pattern, db_type in generic_patterns:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            groups = match.groups()
            if db_type == "sqlite":
                results.append({
                    "db_type": "sqlite",
                    "sqlite_file": groups[0],
                    "source": filepath,
                })
            elif len(groups) >= 5:
                results.append({
                    "db_type": db_type,
                    "user": groups[0],
                    "password": groups[1],
                    "host": groups[2],
                    "port": int(groups[3]) if groups[3] else _default_port(db_type),
                    "database": groups[4],
                    "source": filepath,
                })

    # 模式 4: 只有 env 变量凑齐了基本要素（有 host + type），没有 JDBC URL
    if not results and env_data.get("host"):
        db_type = env_data.get("db_type", "").lower()
        # 映射常见 type 名
        type_map = {
            "mysql": "mysql", "mariadb": "mysql",
            "postgres": "postgresql", "postgresql": "postgresql", "pg": "postgresql",
            "oracle": "oracle",
            "sqlserver": "sqlserver", "mssql": "sqlserver",
            "doris": "doris",
        }
        mapped_type = type_map.get(db_type, db_type or "mysql")
        results.append({
            "db_type": mapped_type,
            "host": env_data.get("host", "localhost"),
            "port": int(env_data["port"]) if env_data.get("port") else _default_port(mapped_type),
            "user": env_data.get("user", ""),
            "password": env_data.get("password", ""),
            "database": env_data.get("database", ""),
            "source": filepath,
        })

    # 模式 5: YAML/JSON 中嵌套的 database 配置
    # 尝试匹配 spring.datasource.url / database.host 等常见层级
    yaml_db_patterns = [
        (r'url:\s*(jdbc:\S+)', "jdbc"),
        (r'"url":\s*"(jdbc:[^"]+)"', "jdbc"),
        (r'host:\s*["\']?([^"\'\s]+)', "host_yaml"),
        (r'database:\s*["\']?([^"\'\s]+)', "db_yaml"),
    ]

    # 如果 YAML/JSON 里找到了 JDBC URL，再次用 JDBC 解析
    for pattern, ptype in yaml_db_patterns:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            if ptype == "jdbc":
                url = match.group(1)
                for jpat, jtype in jdbc_patterns:
                    jm = re.search(jpat, url, re.IGNORECASE)
                    if jm:
                        groups = jm.groups()
                        results.append({
                            "db_type": jtype,
                            "host": groups[0],
                            "port": int(groups[1]) if len(groups) > 1 and groups[1] else _default_port(jtype),
                            "database": groups[2] if len(groups) > 2 and groups[2] else "",
                            "user": env_data.get("user", ""),
                            "password": env_data.get("password", ""),
                            "source": filepath,
                        })

    return results


def _default_port(db_type: str) -> int:
    ports = {
        "mysql": 3306, "mariadb": 3306,
        "postgresql": 5432, "postgres": 5432,
        "oracle": 1521,
        "sqlserver": 1433, "mssql": 1433,
        "doris": 9030,
        "sqlite": 0,
    }
    return ports.get(db_type, 3306)


# ============================================================
# 数据库连接与元数据抽取
# ============================================================

class Introspector:
    """只读元数据抽取基类"""

    def __init__(self, conn_info: dict):
        self.info = conn_info
        self.connection = None

    def connect(self) -> bool:
        raise NotImplementedError

    def disconnect(self):
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass

    def extract(self) -> dict:
        raise NotImplementedError

    def run(self) -> dict | None:
        """连接 → 抽取 → 断开，返回 schema 或 None"""
        try:
            if not self.connect():
                return None
            schema = self.extract()
            schema["extractedAt"] = datetime.now().isoformat()
            schema["connectionInfo"] = {
                "host": self.info.get("host", ""),
                "port": self.info.get("port", ""),
                "database": self.info.get("database", ""),
                "dbType": self.info.get("db_type", ""),
            }
            return schema
        except Exception as e:
            return {"error": str(e), "connectionInfo": self.info}
        finally:
            self.disconnect()


class MySQLIntrospector(Introspector):
    """MySQL / MariaDB / Doris（均使用 MySQL 协议）"""

    ALLOWED_OPERATIONS = {"SELECT", "SHOW", "DESCRIBE", "DESC", "EXPLAIN"}

    def connect(self) -> bool:
        try:
            import pymysql
            self.connection = pymysql.connect(
                host=self.info.get("host", "localhost"),
                port=int(self.info.get("port", 3306)),
                user=self.info.get("user", "root"),
                password=self.info.get("password", ""),
                database=self.info.get("database", ""),
                charset="utf8mb4",
                connect_timeout=10,
                read_timeout=30,
            )
            # 设置只读模式（MySQL 层面）
            cursor = self.connection.cursor()
            cursor.execute("SET SESSION TRANSACTION READ ONLY")
            cursor.close()
            return True
        except ImportError:
            # 如果没有 pymysql，尝试 mysql.connector
            try:
                import mysql.connector
                self.connection = mysql.connector.connect(
                    host=self.info.get("host", "localhost"),
                    port=int(self.info.get("port", 3306)),
                    user=self.info.get("user", "root"),
                    password=self.info.get("password", ""),
                    database=self.info.get("database", ""),
                    connect_timeout=10,
                )
                return True
            except ImportError:
                return False
            except Exception:
                return False
        except Exception:
            return False

    def extract(self) -> dict:
        cursor = self.connection.cursor()

        db_filter = ""
        params = []
        if self.info.get("database"):
            db_filter = "AND TABLE_SCHEMA = %s"
            params = [self.info["database"]]

        databases = []
        # 获取数据库列表
        cursor.execute(
            "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA "
            "WHERE SCHEMA_NAME NOT IN ('information_schema','mysql','performance_schema','sys') "
            + db_filter.replace("TABLE_SCHEMA", "SCHEMA_NAME"),
            params
        )
        db_rows = cursor.fetchall()

        for (db_name,) in db_rows:
            tables = []
            cursor.execute(
                "SELECT TABLE_NAME, TABLE_COMMENT, TABLE_ROWS, ENGINE "
                "FROM INFORMATION_SCHEMA.TABLES "
                "WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE' "
                "ORDER BY TABLE_NAME",
                (db_name,)
            )
            table_rows = cursor.fetchall()

            for (table_name, table_comment, table_rows_count, engine) in table_rows:
                cursor.execute(
                    "SELECT COLUMN_NAME, ORDINAL_POSITION, COLUMN_TYPE, "
                    "IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT, COLUMN_KEY, EXTRA "
                    "FROM INFORMATION_SCHEMA.COLUMNS "
                    "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s "
                    "ORDER BY ORDINAL_POSITION",
                    (db_name, table_name)
                )
                col_rows = cursor.fetchall()

                columns = []
                for (col_name, pos, col_type, nullable, default,
                     col_comment, col_key, extra) in col_rows:
                    columns.append({
                        "name": col_name,
                        "position": pos,
                        "type": col_type.decode() if isinstance(col_type, bytes) else col_type,
                        "nullable": nullable == "YES",
                        "defaultValue": str(default) if default is not None else None,
                        "comment": (col_comment.decode() if isinstance(col_comment, bytes) else col_comment) or None,
                        "isPrimaryKey": col_key == "PRI",
                        "extra": extra or None,
                    })

                tables.append({
                    "name": table_name,
                    "comment": (table_comment.decode() if isinstance(table_comment, bytes) else table_comment) or None,
                    "rowCount": table_rows_count or 0,
                    "engine": engine or None,
                    "columns": columns,
                })

            databases.append({
                "name": db_name,
                "tables": tables,
            })

        cursor.close()
        return {
            "dbType": "mysql",
            "databases": databases,
        }


class PostgresIntrospector(Introspector):
    """PostgreSQL"""

    def connect(self) -> bool:
        try:
            import psycopg2
            self.connection = psycopg2.connect(
                host=self.info.get("host", "localhost"),
                port=int(self.info.get("port", 5432)),
                user=self.info.get("user", "postgres"),
                password=self.info.get("password", ""),
                dbname=self.info.get("database", "postgres"),
                connect_timeout=10,
                options="-c default_transaction_read_only=on",
            )
            return True
        except ImportError:
            try:
                import pg8000
                self.connection = pg8000.connect(
                    host=self.info.get("host", "localhost"),
                    port=int(self.info.get("port", 5432)),
                    user=self.info.get("user", "postgres"),
                    password=self.info.get("password", ""),
                    database=self.info.get("database", "postgres"),
                    timeout=10,
                )
                return True
            except ImportError:
                return False
            except Exception:
                return False
        except Exception:
            return False

    def extract(self) -> dict:
        cursor = self.connection.cursor()

        db_filter = "true"
        params = []
        if self.info.get("database"):
            db_filter = "d.datname = %s"
            params = [self.info["database"]]

        cursor.execute(
            "SELECT d.datname FROM pg_database d "
            "WHERE NOT d.datistemplate "
            "AND d.datname NOT IN ('template0', 'template1') "
            f"AND {db_filter} "
            "ORDER BY d.datname",
            params
        )
        db_rows = cursor.fetchall()

        databases = []
        for (db_name,) in db_rows:
            cursor.execute(
                "SELECT n.nspname FROM pg_namespace n "
                "WHERE n.nspname NOT IN ('pg_catalog', 'information_schema') "
                "ORDER BY n.nspname"
            )
            schema_rows = cursor.fetchall()

            schemas = []
            for (schema_name,) in schema_rows:
                cursor.execute(
                    "SELECT c.relname, obj_description(c.oid, 'pg_class'), "
                    "c.reltuples::bigint "
                    "FROM pg_class c "
                    "JOIN pg_namespace n ON n.oid = c.relnamespace "
                    "WHERE n.nspname = %s AND c.relkind = 'r' "
                    "ORDER BY c.relname",
                    (schema_name,)
                )
                table_rows = cursor.fetchall()

                tables = []
                for (table_name, table_comment, row_est) in table_rows:
                    cursor.execute(
                        "SELECT a.attname, a.attnum, "
                        "pg_catalog.format_type(a.atttypid, a.atttypmod), "
                        "NOT a.attnotnull, pg_get_expr(d.adbin, d.adrelid), "
                        "col_description(c.oid, a.attnum), "
                        "EXISTS (SELECT 1 FROM pg_index i "
                        "WHERE i.indrelid = c.oid AND i.indisprimary "
                        "AND a.attnum = ANY(i.indkey)) "
                        "FROM pg_attribute a "
                        "LEFT JOIN pg_attrdef d ON d.adrelid = c.oid AND d.adnum = a.attnum "
                        "WHERE a.attrelid = c.oid AND a.attnum > 0 "
                        "AND NOT a.attisdropped "
                        "ORDER BY a.attnum",
                        (schema_name, table_name)
                    )
                    col_rows = cursor.fetchall()

                    columns = []
                    for (col_name, pos, col_type, nullable,
                         default, col_comment, is_pk) in col_rows:
                        columns.append({
                            "name": col_name,
                            "position": pos,
                            "type": col_type,
                            "nullable": nullable,
                            "defaultValue": default,
                            "comment": col_comment,
                            "isPrimaryKey": is_pk,
                        })

                    tables.append({
                        "name": table_name,
                        "comment": table_comment,
                        "rowEstimate": row_est or 0,
                        "columns": columns,
                    })

                schemas.append({
                    "name": schema_name,
                    "tables": tables,
                })

            databases.append({
                "name": db_name,
                "schemas": schemas,
            })

        cursor.close()
        return {
            "dbType": "postgresql",
            "databases": databases,
        }


class OracleIntrospector(Introspector):
    """Oracle Database"""

    def connect(self) -> bool:
        try:
            import oracledb
            dsn = oracledb.makedsn(
                self.info.get("host", "localhost"),
                int(self.info.get("port", 1521)),
                service_name=self.info.get("service_name") or self.info.get("database", "ORCL"),
            )
            self.connection = oracledb.connect(
                user=self.info.get("user", "system"),
                password=self.info.get("password", ""),
                dsn=dsn,
            )
            # 设置只读
            cursor = self.connection.cursor()
            cursor.execute("SET TRANSACTION READ ONLY")
            cursor.close()
            return True
        except ImportError:
            return False
        except Exception:
            return False

    def extract(self) -> dict:
        cursor = self.connection.cursor()
        user_filter = ""
        if self.info.get("user"):
            user_filter = f"AND OWNER = '{self.info['user'].upper()}'"

        cursor.execute(
            f"SELECT OWNER, TABLE_NAME, COMMENTS, NUM_ROWS "
            f"FROM ALL_TAB_COMMENTS "
            f"WHERE TABLE_TYPE = 'TABLE' {user_filter} "
            f"ORDER BY OWNER, TABLE_NAME"
        )
        table_rows = cursor.fetchall()

        schemas = {}
        for (owner, table_name, comments, num_rows) in table_rows:
            if owner not in schemas:
                schemas[owner] = []

            cursor.execute(
                "SELECT COLUMN_NAME, COLUMN_ID, DATA_TYPE, "
                "NULLABLE, DATA_DEFAULT, "
                "COMMENTS "
                "FROM ALL_COL_COMMENTS "
                "NATURAL JOIN ALL_TAB_COLUMNS "
                "WHERE OWNER = :owner AND TABLE_NAME = :table_name "
                "ORDER BY COLUMN_ID",
                owner=owner, table_name=table_name
            )
            col_rows = cursor.fetchall()

            # 获取主键
            cursor.execute(
                "SELECT COLUMN_NAME FROM ALL_CONS_COLUMNS "
                "WHERE OWNER = :owner AND TABLE_NAME = :table_name "
                "AND CONSTRAINT_NAME IN ("
                "SELECT CONSTRAINT_NAME FROM ALL_CONSTRAINTS "
                "WHERE OWNER = :owner AND TABLE_NAME = :table_name "
                "AND CONSTRAINT_TYPE = 'P')",
                owner=owner, table_name=table_name
            )
            pk_cols = {row[0] for row in cursor.fetchall()}

            columns = []
            for (col_name, col_id, data_type, nullable, default, col_comment) in col_rows:
                columns.append({
                    "name": col_name,
                    "position": col_id,
                    "type": data_type,
                    "nullable": nullable == "Y",
                    "defaultValue": default,
                    "comment": col_comment,
                    "isPrimaryKey": col_name in pk_cols,
                })

            schemas[owner].append({
                "name": table_name,
                "comment": comments,
                "rowCount": num_rows or 0,
                "columns": columns,
            })

        cursor.close()
        return {
            "dbType": "oracle",
            "databases": [
                {"name": owner, "tables": tables}
                for owner, tables in schemas.items()
            ],
        }


class SQLServerIntrospector(Introspector):
    """SQL Server"""

    def connect(self) -> bool:
        try:
            import pymssql
            self.connection = pymssql.connect(
                server=self.info.get("host", "localhost"),
                port=int(self.info.get("port", 1433)),
                user=self.info.get("user", "sa"),
                password=self.info.get("password", ""),
                database=self.info.get("database", "master"),
                timeout=10,
            )
            return True
        except ImportError:
            try:
                import pyodbc
                conn_str = (
                    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                    f"SERVER={self.info.get('host', 'localhost')},"
                    f"{self.info.get('port', 1433)};"
                    f"UID={self.info.get('user', 'sa')};"
                    f"PWD={self.info.get('password', '')};"
                    f"TrustServerCertificate=yes;"
                    f"ApplicationIntent=ReadOnly;"
                )
                self.connection = pyodbc.connect(conn_str, timeout=10)
                return True
            except ImportError:
                return False
            except Exception:
                return False
        except Exception:
            return False

    def extract(self) -> dict:
        cursor = self.connection.cursor()

        db_filter = "1=1"
        if self.info.get("database"):
            db_filter = f"d.name = '{self.info['database']}'"

        cursor.execute(
            f"SELECT d.name FROM sys.databases d "
            f"WHERE d.name NOT IN ('master','tempdb','model','msdb') "
            f"AND {db_filter} "
            f"ORDER BY d.name"
        )
        db_rows = cursor.fetchall()

        databases = []
        for (db_name,) in db_rows:
            cursor.execute(
                f"USE [{db_name}]; "
                f"SELECT t.name, COALESCE(ep.value, ''), "
                f"SUM(p.rows) "
                f"FROM [{db_name}].sys.tables t "
                f"LEFT JOIN [{db_name}].sys.extended_properties ep "
                f"ON ep.major_id = t.object_id AND ep.minor_id = 0 "
                f"AND ep.name = 'MS_Description' "
                f"LEFT JOIN [{db_name}].sys.partitions p "
                f"ON p.object_id = t.object_id AND p.index_id IN (0,1) "
                f"GROUP BY t.name, ep.value "
                f"ORDER BY t.name"
            )
            table_rows = cursor.fetchall()

            tables = []
            for (table_name, table_comment, row_count) in table_rows:
                cursor.execute(
                    f"USE [{db_name}]; "
                    f"SELECT c.name, c.column_id, "
                    f"TYPE_NAME(c.user_type_id) + "
                    f"CASE WHEN TYPE_NAME(c.user_type_id) IN ('varchar','nvarchar',"
                    f"'char','nchar') THEN '(' + CAST(c.max_length AS VARCHAR) + ')' "
                    f"ELSE '' END, "
                    f"c.is_nullable, "
                    f"OBJECT_DEFINITION(c.default_object_id), "
                    f"COALESCE(ep.value, ''), "
                    f"CASE WHEN pk.column_id IS NOT NULL THEN 1 ELSE 0 END "
                    f"FROM [{db_name}].sys.columns c "
                    f"LEFT JOIN [{db_name}].sys.extended_properties ep "
                    f"ON ep.major_id = c.object_id AND ep.minor_id = c.column_id "
                    f"AND ep.name = 'MS_Description' "
                    f"LEFT JOIN ("
                    f"SELECT ic.column_id FROM [{db_name}].sys.indexes i "
                    f"JOIN [{db_name}].sys.index_columns ic "
                    f"ON i.object_id = ic.object_id AND i.index_id = ic.index_id "
                    f"WHERE i.is_primary_key = 1 AND i.object_id = "
                    f"OBJECT_ID('{db_name}.dbo.{table_name}')"
                    f") pk ON pk.column_id = c.column_id "
                    f"WHERE c.object_id = OBJECT_ID('{db_name}.dbo.{table_name}') "
                    f"ORDER BY c.column_id"
                )
                col_rows = cursor.fetchall()

                columns = []
                for (col_name, pos, col_type, nullable, default, col_comment, is_pk) in col_rows:
                    columns.append({
                        "name": col_name,
                        "position": pos,
                        "type": col_type,
                        "nullable": bool(nullable),
                        "defaultValue": default,
                        "comment": col_comment if col_comment else None,
                        "isPrimaryKey": bool(is_pk),
                    })

                tables.append({
                    "name": table_name,
                    "comment": table_comment if table_comment else None,
                    "rowCount": row_count or 0,
                    "columns": columns,
                })

            databases.append({
                "name": db_name,
                "tables": tables,
            })

        cursor.close()
        return {
            "dbType": "sqlserver",
            "databases": databases,
        }


# ============================================================
# 主入口
# ============================================================

INTROSPECTORS = {
    "mysql": MySQLIntrospector,
    "mariadb": MySQLIntrospector,
    "doris": MySQLIntrospector,  # Doris 使用 MySQL 协议
    "postgresql": PostgresIntrospector,
    "postgres": PostgresIntrospector,
    "pg": PostgresIntrospector,
    "oracle": OracleIntrospector,
    "sqlserver": SQLServerIntrospector,
    "mssql": SQLServerIntrospector,
}


def main():
    parser = argparse.ArgumentParser(
        description="数据库结构只读抽取 — 支持 MySQL / PostgreSQL / Oracle / Doris / SQL Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 自动检测项目中的数据库连接信息
  python db-introspect.py --auto-detect /path/to/project

  # 手动指定连接
  python db-introspect.py --type mysql --host 192.168.1.1 -u root -p 123456 -d mydb
  python db-introspect.py --type postgres --host localhost -u postgres -d mydb
  python db-introspect.py --type oracle --host localhost -u scott -p tiger --sid ORCL

安全保证：所有查询均为 information_schema / system catalog 的 SELECT 查询，
绝不执行任何写入操作。
""",
    )

    parser.add_argument("--auto-detect", metavar="PROJECT_DIR",
                        help="自动从项目代码中检测数据库连接信息")

    # 手动连接参数
    parser.add_argument("--type", dest="db_type",
                        choices=["mysql", "mariadb", "postgres", "postgresql", "pg",
                                 "oracle", "sqlserver", "mssql", "doris"],
                        help="数据库类型")
    parser.add_argument("--host", default="localhost", help="主机地址（默认: localhost）")
    parser.add_argument("--port", type=int, help="端口（默认按数据库类型推断）")
    parser.add_argument("-u", "--user", help="用户名")
    parser.add_argument("-p", "--pass", dest="password", help="密码")
    parser.add_argument("-d", "--db", dest="database", help="数据库名")
    parser.add_argument("--sid", help="Oracle SID 或 Service Name")
    parser.add_argument("--service-name", help="Oracle Service Name")

    parser.add_argument("-o", "--output", default="./db-analysis",
                        help="输出目录（默认: ./db-analysis）")

    args = parser.parse_args()

    connections = []

    # 模式 1: 自动检测
    if args.auto_detect:
        project_dir = os.path.abspath(args.auto_detect)
        if not os.path.isdir(project_dir):
            print(f"[ERROR] 目录不存在: {project_dir}", file=sys.stderr)
            sys.exit(1)

        print(f"[db-introspect] 扫描项目目录: {project_dir}")
        connections = find_connection_info(project_dir)

        if not connections:
            print("[db-introspect] 未检测到数据库连接信息。")
            print("  提示：检查项目中是否有 .env / application.yml / database.json 等配置文件。")
            print("  也可以手动指定连接参数：python db-introspect.py --type mysql --host ...")
            sys.exit(0)

        print(f"[db-introspect] 检测到 {len(connections)} 个可能的数据库连接:")
        for i, c in enumerate(connections):
            print(f"  [{i+1}] {c.get('db_type')}://{c.get('user','?')}@"
                  f"{c.get('host','?')}:{c.get('port','?')}/{c.get('database','?')}"
                  f"  (来源: {c.get('source','?')})")

    # 模式 2: 手动指定
    elif args.db_type:
        conn = {
            "db_type": args.db_type,
            "host": args.host,
            "port": args.port or _default_port(args.db_type),
            "user": args.user or "",
            "password": args.password or "",
            "database": args.database or "",
            "service_name": args.service_name or args.sid or "",
        }
        connections = [conn]
    else:
        parser.print_help()
        print("\n请指定 --auto-detect <项目目录> 或 --type <数据库类型>")
        sys.exit(1)

    # 逐个尝试连接并抽取
    os.makedirs(args.output, exist_ok=True)

    success_count = 0
    for i, conn in enumerate(connections):
        db_type = conn["db_type"]
        label = f"{db_type}://{conn.get('user','?')}@{conn.get('host','?')}:" \
                f"{conn.get('port','?')}/{conn.get('database','?')}"

        print(f"\n[db-introspect] [{i+1}/{len(connections)}] 尝试连接: {label}")

        introspector_class = INTROSPECTORS.get(db_type)
        if not introspector_class:
            print(f"  [SKIP] 不支持的数据库类型: {db_type}")
            continue

        introspector = introspector_class(conn)
        schema = introspector.run()

        if schema is None:
            print(f"  [SKIP] 连接失败，跳过。")
            continue

        if "error" in schema:
            print(f"  [SKIP] 抽取失败: {schema['error']}")
            # 仍然写入错误信息
            err_file = os.path.join(args.output, f"db-{i+1}-error.json")
            with open(err_file, "w", encoding="utf-8") as f:
                json.dump(schema, f, ensure_ascii=False, indent=2)
            continue

        # 成功 → 写入
        out_file = os.path.join(args.output, f"schema-{db_type}.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(schema, f, ensure_ascii=False, indent=2, default=str)

        table_count = sum(
            len(tbl_coll.get("tables", tbl_coll.get("schemas", [])))
            if isinstance(tbl_coll, dict)
            else 0
            for db_item in schema.get("databases", [])
            for tbl_coll in [db_item]
        )
        # 用更准确的方式统计
        table_count = 0
        for db_item in schema.get("databases", []):
            if "tables" in db_item:
                table_count += len(db_item["tables"])
            elif "schemas" in db_item:
                for s in db_item["schemas"]:
                    table_count += len(s.get("tables", []))

        print(f"  [OK] 抽取成功 → {out_file}")
        print(f"       数据库: {len(schema.get('databases',[]))}, 表: {table_count}")
        success_count += 1

    print(f"\n[db-introspect] 完成。成功 {success_count}/{len(connections)}，输出目录: {args.output}")

    if success_count == 0:
        print("[db-introspect] 所有连接均失败。")
        print("  提示：")
        print("  1. 检查数据库是否在运行")
        print("  2. 检查网络连接和防火墙")
        print("  3. 确认账号密码正确")
        print("  4. 安装对应的 Python 驱动:")
        print("     MySQL/Doris:  pip install pymysql")
        print("     PostgreSQL:   pip install psycopg2-binary")
        print("     Oracle:       pip install oracledb")
        print("     SQL Server:   pip install pymssql 或 pip install pyodbc")
        sys.exit(1)


if __name__ == "__main__":
    main()
