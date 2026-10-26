"""로컬 PostgreSQL의 고유 임시 schema에서 설계 제약/동시성을 검증한다."""

import asyncio
import json
import sys
import time
from pathlib import Path
from uuid import uuid4

import asyncpg
from sqlalchemy.engine import make_url

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src/backend"))
from app.core.config.settings import SETTINGS  # noqa: E402


async def main() -> None:
    url = make_url(SETTINGS.DATABASE_URL)
    if url.drivername != "postgresql+asyncpg" or url.host not in ("localhost", "127.0.0.1", "::1"):
        raise SystemExit("로컬 postgresql+asyncpg 설정만 허용합니다.")
    schema = "canvanity_probe_" + uuid4().hex
    connections = []
    checks = []
    created = False

    async def connect():
        conn = await asyncpg.connect(
            host=url.host,
            port=url.port or 5432,
            user=url.username,
            password=url.password,
            database=url.database,
            timeout=5,
            command_timeout=10,
        )
        connections.append(conn)
        await conn.execute(f'SET search_path TO "{schema}"')
        return conn

    async def rejects(conn, name, sql, error):
        try:
            async with conn.transaction():
                await conn.execute(sql)
        except error:
            checks.append(name)
        else:
            raise AssertionError(name)

    try:
        conn = await connect()
        version = await conn.fetchval("SHOW server_version")
        await conn.execute(f'CREATE SCHEMA "{schema}"')
        created = True
        await conn.execute("""
            CREATE TABLE boards(id int PRIMARY KEY,slug text UNIQUE NOT NULL);
            CREATE TABLE grades(id int PRIMARY KEY,board_id int REFERENCES boards,
                rank int NOT NULL CHECK(rank>=0),is_default bool NOT NULL,
                UNIQUE(board_id,id),UNIQUE(board_id,rank) DEFERRABLE INITIALLY DEFERRED);
            CREATE UNIQUE INDEX default_grade ON grades(board_id) WHERE is_default;
            CREATE TABLE members(board_id int REFERENCES boards,user_id int,grade_id int,
                role text NOT NULL,PRIMARY KEY(board_id,user_id),
                FOREIGN KEY(board_id,grade_id) REFERENCES grades(board_id,id));
            CREATE UNIQUE INDEX one_owner ON members(board_id) WHERE role='owner';
            CREATE TABLE shelves(id int PRIMARY KEY,board_id int REFERENCES boards,slug text,
                UNIQUE(board_id,id),UNIQUE(board_id,slug));
            CREATE TABLE canvases(id int PRIMARY KEY,board_id int,shelf_id int,
                FOREIGN KEY(board_id,shelf_id) REFERENCES shelves(board_id,id));
            CREATE TABLE documents(canvas_id int PRIMARY KEY REFERENCES canvases,
                document jsonb NOT NULL,revision bigint NOT NULL CHECK(revision>=0));
            CREATE TABLE publications(canvas_id int PRIMARY KEY REFERENCES canvases,
                document jsonb NOT NULL,source_revision bigint NOT NULL);
            INSERT INTO boards VALUES(1,'alpha'),(2,'beta');
            INSERT INTO grades VALUES(10,1,0,true),(11,1,10,false),(20,2,0,true);
            INSERT INTO members VALUES(1,1,10,'owner'),(1,2,10,'member');
            INSERT INTO shelves VALUES(100,1,'general'),(200,2,'general');
            INSERT INTO canvases VALUES(1000,1,100);
            INSERT INTO documents VALUES(1000,'{"schema_version":1,"nodes":[],"edges":[]}',0);
        """)
        await rejects(
            conn,
            "board_slug_unique",
            "INSERT INTO boards VALUES(3,'alpha')",
            asyncpg.UniqueViolationError,
        )
        await rejects(
            conn,
            "shelf_slug_unique",
            "INSERT INTO shelves VALUES(101,1,'general')",
            asyncpg.UniqueViolationError,
        )
        await rejects(
            conn,
            "cross_board_shelf_fk",
            "INSERT INTO canvases VALUES(2000,1,200)",
            asyncpg.ForeignKeyViolationError,
        )
        await rejects(
            conn,
            "cross_board_grade_fk",
            "INSERT INTO members VALUES(1,3,20,'member')",
            asyncpg.ForeignKeyViolationError,
        )
        await rejects(
            conn,
            "default_grade_unique",
            "INSERT INTO grades VALUES(12,1,20,true)",
            asyncpg.UniqueViolationError,
        )
        await rejects(
            conn,
            "one_owner_unique",
            "INSERT INTO members VALUES(1,3,10,'owner')",
            asyncpg.UniqueViolationError,
        )
        async with conn.transaction():
            await conn.execute(
                "UPDATE grades SET rank=CASE id WHEN 10 THEN 10 ELSE 0 END WHERE board_id=1"
            )
        assert await conn.fetchval("SELECT rank FROM grades WHERE id=10") == 10
        checks.append("deferred_grade_reorder")
        try:
            async with conn.transaction():
                await conn.execute("INSERT INTO boards VALUES(3,'rollback')")
                await conn.execute("INSERT INTO grades VALUES(30,3,0,true)")
                await conn.execute("INSERT INTO shelves VALUES(300,3,'general')")
                await conn.execute("INSERT INTO members VALUES(3,3,20,'owner')")
        except asyncpg.ForeignKeyViolationError:
            pass
        else:
            raise AssertionError("rollback failure not triggered")
        for table in ("boards", "grades", "shelves"):
            column = "id" if table == "boards" else "board_id"
            assert await conn.fetchval(f"SELECT count(*) FROM {table} WHERE {column}=3") == 0
        checks.append("board_creation_rollback")
        one, two = await connect(), await connect()

        async def save(connection, marker):
            return await connection.fetchval(
                "UPDATE documents SET revision=revision+1,document=$1::jsonb "
                "WHERE canvas_id=1000 AND revision=0 RETURNING revision",
                json.dumps({"schema_version": 1, "nodes": [], "edges": [], "marker": marker}),
            )

        winners = await asyncio.gather(save(one, "one"), save(two, "two"))
        assert sum(x == 1 for x in winners) == 1 and sum(x is None for x in winners) == 1
        checks.append("concurrent_revision_one_winner")
        await conn.execute(
            "INSERT INTO publications SELECT canvas_id,document,revision FROM documents"
        )
        await conn.execute("UPDATE documents SET document='{}',revision=revision+1")
        assert await conn.fetchval("SELECT source_revision FROM publications") == 1
        assert (
            json.loads(await conn.fetchval("SELECT document::text FROM publications"))[
                "schema_version"
            ]
            == 1
        )
        checks.append("published_snapshot_unchanged_after_draft_save")
        document = {
            "schema_version": 1,
            "nodes": [
                {"id": str(i), "type": "text", "content": {"text": "한글 문서 " * 10}}
                for i in range(1000)
            ],
            "edges": [],
        }
        serialized = json.dumps(document, ensure_ascii=False)
        samples = []
        for _ in range(10):
            start = time.perf_counter()
            await conn.execute(
                "UPDATE documents SET document=$1::jsonb,revision=revision+1", serialized
            )
            samples.append(round((time.perf_counter() - start) * 1000, 3))
        assert json.loads(await conn.fetchval("SELECT document::text FROM documents")) == document
        checks.append("jsonb_korean_1000_nodes_round_trip")
        report = {
            "postgresql": version,
            "checks": checks,
            "check_count": len(checks),
            "fixture_nodes": 1000,
            "utf8_bytes": len(serialized.encode()),
            "jsonb_update_ms": samples,
            "scope": "isolated design DDL, not product API",
        }
    finally:
        if created:
            await connections[0].execute(f'DROP SCHEMA "{schema}" CASCADE')
            assert not await connections[0].fetchval(
                "SELECT 1 FROM pg_namespace WHERE nspname=$1", schema
            )
        for connection in connections:
            await connection.close()
    report["schema_cleanup_verified"] = True
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (OSError, asyncpg.PostgresError):
        raise SystemExit(
            "PostgreSQL probe 실패: 접속/제약 오류. 인증정보는 출력하지 않습니다."
        ) from None
