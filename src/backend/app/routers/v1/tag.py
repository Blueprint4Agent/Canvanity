from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.core.error.response_contracts import current_user_error_responses
from app.core.error.tag_exception import TagErrorCode, tag_error_responses
from app.deps import get_current_session_user
from app.models.tag import TagCatalogResponse, TagCreateForm, TagResponse, TagSearchQuery
from app.models.user import UserResponse
from app.services.tag import TagService

router = APIRouter()


@router.get(
    "", response_model=TagCatalogResponse, responses=tag_error_responses(TagErrorCode.UNAVAILABLE)
)
async def search_tags(
    query: Annotated[TagSearchQuery, Query()], service: TagService = Depends()
) -> TagCatalogResponse:
    return await service.search(query)


@router.post(
    "",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
    responses=current_user_error_responses(
        tag_error_responses(TagErrorCode.UNAVAILABLE),
        {
            status.HTTP_200_OK: {
                "model": TagResponse,
                "description": "Existing normalized tag reused.",
            }
        },
    ),
)
async def create_tag(
    form: TagCreateForm,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: TagService = Depends(),
) -> TagResponse:
    result = await service.create(user.id, form)
    response.status_code = status.HTTP_201_CREATED if result.created else status.HTTP_200_OK
    response.headers["Cache-Control"] = "private, no-store"
    return result.tag
