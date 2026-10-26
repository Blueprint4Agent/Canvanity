"""Broaden official community interests and balance their discovery order."""

import sqlalchemy as sa

from alembic import op

revision = "0023_broaden_interest_catalog"
down_revision = "0022_official_interests"
branch_labels = None
depends_on = None

ADDITIONS = [
    ("pets", "반려동물", "Pets", ["동물", "강아지", "고양이", "dogs", "cats"]),
    ("fashion", "패션", "Fashion", ["옷", "스타일", "outfit", "style"]),
    ("beauty", "뷰티", "Beauty", ["메이크업", "화장품", "스킨케어", "makeup", "skincare"]),
    ("home", "리빙", "Home & living", ["집꾸미기", "살림", "정리", "home decor"]),
    ("gardening", "식물·가드닝", "Plants & gardening", ["식물", "원예", "plants", "garden"]),
    ("outdoors", "아웃도어", "Outdoors", ["등산", "트레킹", "hiking", "trekking"]),
    ("camping", "캠핑", "Camping", ["백패킹", "차박", "backpacking"]),
    ("running", "러닝", "Running", ["달리기", "마라톤", "marathon"]),
    ("cycling", "자전거", "Cycling", ["라이딩", "사이클", "bicycle"]),
    (
        "finance",
        "경제·재테크",
        "Economy & finance",
        ["경제", "재테크", "저축", "투자", "economics", "investing"],
    ),
    ("cars", "자동차", "Cars", ["차", "모터사이클", "automotive", "motorcycle"]),
    ("parenting", "육아·가족", "Parenting & family", ["육아", "가족", "family"]),
    ("relationships", "연애·관계", "Relationships", ["연애", "관계", "dating"]),
    (
        "comics",
        "만화·애니",
        "Comics & animation",
        ["만화", "애니", "웹툰", "anime", "manga", "webtoon"],
    ),
    ("coffee", "커피·차", "Coffee & tea", ["커피", "차문화", "홈카페", "tea", "cafe"]),
    ("sports", "스포츠", "Sports", ["축구", "야구", "농구", "football", "baseball", "basketball"]),
]
ORDER = [
    "daily",
    "travel",
    "photography",
    "gaming",
    "music",
    "film",
    "comics",
    "reading",
    "art",
    "craft",
    "writing",
    "design",
    "pets",
    "fashion",
    "beauty",
    "home",
    "cooking",
    "coffee",
    "gardening",
    "parenting",
    "relationships",
    "sports",
    "fitness",
    "running",
    "cycling",
    "outdoors",
    "camping",
    "nature",
    "science",
    "education",
    "finance",
    "business",
    "cars",
    "architecture",
    "productivity",
    "technology",
    "development",
    "ai",
    "ui-ux",
    "game-dev",
]


def upgrade() -> None:
    op.add_column(
        "interests", sa.Column("sort_order", sa.Integer(), nullable=False, server_default="1000")
    )
    db = op.get_bind()
    interests = sa.table(
        "interests",
        sa.column("id", sa.Integer()),
        sa.column("slug", sa.String()),
        sa.column("name_ko", sa.String()),
        sa.column("name_en", sa.String()),
        sa.column("active", sa.Boolean()),
        sa.column("sort_order", sa.Integer()),
    )
    aliases = sa.table(
        "interest_aliases", sa.column("alias", sa.String()), sa.column("interest_id", sa.Integer())
    )
    for slug, ko, en, terms in ADDITIONS:
        existing = db.scalar(sa.select(interests.c.id).where(interests.c.slug == slug))
        if existing is None:
            existing = (db.scalar(sa.select(sa.func.max(interests.c.id))) or 0) + 1
            db.execute(
                interests.insert().values(
                    id=existing, slug=slug, name_ko=ko, name_en=en, active=True, sort_order=1000
                )
            )
        for term in dict.fromkeys([slug, ko, en, *terms]):
            term = term.casefold()
            if db.scalar(sa.select(aliases.c.alias).where(aliases.c.alias == term)) is None:
                db.execute(aliases.insert().values(alias=term, interest_id=existing))
    if db.dialect.name == "postgresql":
        db.execute(
            sa.text(
                "SELECT setval(pg_get_serial_sequence('interests', 'id'), (SELECT max(id) FROM interests))"
            )
        )
    for position, slug in enumerate(ORDER):
        db.execute(interests.update().where(interests.c.slug == slug).values(sort_order=position))


def downgrade() -> None:
    # Keep additive vocabulary and user selections rather than deleting user-owned links.
    op.drop_column("interests", "sort_order")
