from fastapi import Depends

from app.models.tag import (
    TagCatalogResponse,
    TagCreateForm,
    TagCreationResult,
    TagRepository,
    TagSearchQuery,
)


class TagService:
    def __init__(self, repository: TagRepository = Depends()):
        self.repository = repository

    async def search(self, query: TagSearchQuery) -> TagCatalogResponse:
        return await self.repository.search(query)

    async def create(self, user_id: int, form: TagCreateForm) -> TagCreationResult:
        return await self.repository.get_or_create(user_id, form)
