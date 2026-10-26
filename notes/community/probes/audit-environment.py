"""로컬 설정에서 비밀값을 제외한 실행 경계만 출력한다. 외부 연결 없음."""

import json
import sys
from pathlib import Path

from sqlalchemy.engine import make_url

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src/backend"))
from app.core.config.settings import SETTINGS as s  # noqa: E402

url = make_url(s.DATABASE_URL)
print(
    json.dumps(
        {
            "database_driver": url.drivername,
            "database_local": url.host in ("localhost", "127.0.0.1", "::1", None),
            "database_port": url.port,
            "app_port": s.APP_PORT,
            "login": s.LOGIN_ENABLED,
            "email": s.EMAIL_ENABLED,
            "oauth": s.OAUTH_ENABLED,
            "stripe": s.STRIPE_ENABLED,
            "redis_memory": s.REDIS_IN_MEMORY,
            "redis_port": s.REDIS_PORT,
            "redis_db": s.REDIS_DB,
            "queue_is_canvanity": s.CELERY_QUEUE.startswith("canvanity"),
            "prefix_is_canvanity": s.CELERY_KEY_PREFIX.startswith("canvanity"),
            "object_storage": s.OBJECT_STORAGE_PROVIDER,
        },
        indent=2,
    )
)
