from fastapi import APIRouter, Depends

from app.core.error.auth_exception import AuthErrorCode, auth_error_responses
from app.core.error.response_contracts import current_user_error_responses
from app.deps import get_current_admin_user
from app.models.interest import (
    InterestAdminResponse,
    InterestCatalogResponse,
    InterestCreateForm,
    InterestUpdateForm,
)
from app.models.user import UserResponse
from app.services.interest import InterestService

router = APIRouter()


@router.get("", response_model=InterestCatalogResponse)
async def catalog(service: InterestService = Depends()) -> InterestCatalogResponse:
    return await service.catalog()


@router.get(
    "/admin",
    response_model=list[InterestAdminResponse],
    responses=current_user_error_responses(auth_error_responses(AuthErrorCode.INSUFFICIENT_ROLE)),
)
async def list_admin(
    _user: UserResponse = Depends(get_current_admin_user), service: InterestService = Depends()
) -> list[InterestAdminResponse]:
    return await service.list_admin()


@router.post(
    "/admin",
    response_model=InterestAdminResponse,
    status_code=201,
    responses=current_user_error_responses(
        auth_error_responses(AuthErrorCode.INSUFFICIENT_ROLE, AuthErrorCode.INTEREST_ALREADY_EXISTS)
    ),
)
async def create(
    form: InterestCreateForm,
    _user: UserResponse = Depends(get_current_admin_user),
    service: InterestService = Depends(),
) -> InterestAdminResponse:
    return await service.create(form)


@router.patch(
    "/admin/{interest_id}",
    response_model=InterestAdminResponse,
    responses=current_user_error_responses(
        auth_error_responses(
            AuthErrorCode.INSUFFICIENT_ROLE,
            AuthErrorCode.INTEREST_ALREADY_EXISTS,
            AuthErrorCode.INTEREST_NOT_FOUND,
        )
    ),
)
async def update(
    interest_id: str,
    form: InterestUpdateForm,
    _user: UserResponse = Depends(get_current_admin_user),
    service: InterestService = Depends(),
) -> InterestAdminResponse:
    return await service.update(interest_id, form)
