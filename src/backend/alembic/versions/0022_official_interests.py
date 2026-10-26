"""Separate approved interests from future free-form content tags."""

import json

import sqlalchemy as sa

from alembic import op

revision = "0022_official_interests"
down_revision = "0021_profile_identity"
branch_labels = None
depends_on = None

# Immutable initial platform catalog; aliases support search, never create new categories.
CATALOG = [
    ("development", "개발", "Development", ["프로그래밍", "코딩", "programming", "coding"]),
    ("ai", "AI", "AI", ["인공지능", "artificial intelligence", "머신러닝"]),
    ("design", "디자인", "Design", ["시각디자인", "graphic design"]),
    ("ui-ux", "UI·UX", "UI & UX", ["ui", "ux", "ui 디자인", "ux 디자인", "ui design"]),
    ("game-dev", "게임 개발", "Game development", ["게임개발", "게임제작", "gamedev"]),
    ("gaming", "게임", "Gaming", ["game", "games"]),
    ("photography", "사진", "Photography", ["photo", "촬영"]),
    ("travel", "여행", "Travel", ["여행기"]),
    ("music", "음악", "Music", ["작곡"]),
    ("daily", "일상", "Daily life", ["일상기록", "daily life"]),
    ("reading", "독서", "Reading", ["책", "books"]),
    ("film", "영화", "Film", ["movie", "movies"]),
    ("fitness", "운동", "Fitness", ["스포츠", "sports"]),
    ("cooking", "요리", "Cooking", ["음식", "food"]),
    ("art", "미술", "Art", ["예술", "그림", "drawing"]),
    ("writing", "글쓰기", "Writing", ["기록", "journaling"]),
    ("science", "과학", "Science", []),
    ("architecture", "건축", "Architecture", ["인테리어", "interior"]),
    ("technology", "기술", "Technology", ["테크", "tech"]),
    ("education", "교육", "Education", ["학습", "learning"]),
    ("business", "창업", "Business", ["비즈니스", "스타트업", "startup"]),
    ("craft", "공예", "Craft", ["수공예", "handmade"]),
    ("nature", "자연", "Nature", ["환경", "environment"]),
    ("productivity", "생산성", "Productivity", ["자기계발"]),
]


def upgrade() -> None:
    interests = op.create_table(
        "interests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(40), nullable=False, unique=True),
        sa.Column("name_ko", sa.String(40), nullable=False),
        sa.Column("name_en", sa.String(40), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    aliases = op.create_table(
        "interest_aliases",
        sa.Column("alias", sa.String(80), primary_key=True),
        sa.Column(
            "interest_id",
            sa.Integer(),
            sa.ForeignKey("interests.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    links = op.create_table(
        "user_interests",
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column(
            "interest_id",
            sa.Integer(),
            sa.ForeignKey("interests.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
    )
    op.bulk_insert(
        interests,
        [
            {"id": index, "slug": slug, "name_ko": ko, "name_en": en, "active": True}
            for index, (slug, ko, en, _) in enumerate(CATALOG, 1)
        ],
    )
    lookup = {}
    for index, (slug, ko, en, terms) in enumerate(CATALOG, 1):
        for term in [slug, ko, en, *terms]:
            lookup[term.strip().casefold()] = index
    op.bulk_insert(
        aliases,
        [{"alias": alias, "interest_id": interest_id} for alias, interest_id in lookup.items()],
    )
    # Keep the old JSON column as a rollback record; only recognized categories become links.
    for user_id, raw in op.get_bind().execute(sa.text("SELECT id, interests FROM users")):
        values = json.loads(raw) if isinstance(raw, str) else raw or []
        selected = list(
            dict.fromkeys(
                lookup[value.strip().casefold()]
                for value in values
                if isinstance(value, str) and value.strip().casefold() in lookup
            )
        )[:8]
        if selected:
            op.bulk_insert(
                links,
                [
                    {"user_id": user_id, "interest_id": value, "position": position}
                    for position, value in enumerate(selected)
                ],
            )


def downgrade() -> None:
    op.drop_table("user_interests")
    op.drop_table("interest_aliases")
    op.drop_table("interests")
