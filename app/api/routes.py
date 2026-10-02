import logging

from fastapi import APIRouter, Depends, HTTPException

from app.core.firebase import get_current_user
from app.schemas.itinerary import (
    ItineraryResponse,
    RegenerateDayRequest,
    RegenerateItemRequest,
    TripCreate,
)
from app.services.itinerary_service import generate_itinerary
from app.services.regeneration_service import (
    regenerate_day,
    regenerate_item,
)
from app.services.unsplash_service import search_image


router = APIRouter()

logger = logging.getLogger(__name__)


@router.post(
    "/itinerary/generate",
    response_model=ItineraryResponse,
)
async def create_itinerary(
    trip: TripCreate,
    current_user: dict = Depends(get_current_user),
):
    try:
        return await generate_itinerary(trip)

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Unexpected error generating itinerary"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to generate itinerary",
        )


@router.post("/itinerary/regenerate-day")
async def regenerate_itinerary_day(
    request: RegenerateDayRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        regenerated_day = await regenerate_day(request)

        return {
            "day_number": request.day_number,
            "day": regenerated_day.model_dump(),
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Unexpected error regenerating day"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to regenerate day",
        )


@router.post("/itinerary/regenerate-item")
async def regenerate_itinerary_item(
    request: RegenerateItemRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        regenerated_item = await regenerate_item(request)

        return {
            "day_number": request.day_number,
            "item_type": request.item_type,
            "item_index": request.item_index,
            "item": regenerated_item.model_dump(),
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Unexpected error regenerating item"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to regenerate item",
        )


@router.get("/hero-image")
async def get_hero_image():
    image_url = await search_image(
        item_name="travel landscape",
        destination="world",
    )

    if not image_url:
        raise HTTPException(
            status_code=404,
            detail="Hero image not found",
        )

    return {
        "image_url": image_url,
    }