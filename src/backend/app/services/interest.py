from app.core.error import AuthErrorCode, AuthException
from app.models.interest import (
    InterestAdminResponse,
    InterestCatalogResponse,
    InterestCreateForm,
    InterestRepository,
    InterestUpdateForm,
)


class InterestService:
    def __init__(self) -> None:
        self.repository = InterestRepository()

    async def catalog(self) -> InterestCatalogResponse:
        return await self.repository.list_active()

    async def create(self, form: InterestCreateForm) -> InterestAdminResponse:
        return await self.repository.create(form)

    async def update(self, slug: str, form: InterestUpdateForm) -> InterestAdminResponse:
        item = await self.repository.update(slug, form)
        if item is None:
            raise AuthException(code=AuthErrorCode.INTEREST_NOT_FOUND)
        return item

    async def list_admin(self) -> list[InterestAdminResponse]:
        return await self.repository.list_admin()
