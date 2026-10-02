from fastapi import HTTPException

from app.schemas.itinerary import (
    Activity,
    DayItinerary,
    Food,
    Place,
    RegenerateDayRequest,
    RegenerateItemRequest,
)
from app.services.ai_service import generate_ai_response
from app.services.prompt_service import (
    build_regenerate_day_prompt,
    build_regenerate_item_prompt,
)
from app.services.unsplash_service import search_image


def calculate_itinerary_cost(
    itinerary_data: dict[str, DayItinerary],
) -> float:
    total = 0.0

    for day in itinerary_data.values():
        for place in day.places:
            total += place.price

        for food in day.food:
            total += food.price

        for activity in day.activities:
            total += activity.price

    return round(total, 2)


def _normalize(value: str) -> str:
    return " ".join(value.lower().strip().split())


def get_existing_item_names(
    itinerary_data: dict[str, DayItinerary],
    exclude_day: int | None = None,
    exclude_item_type: str | None = None,
    exclude_item_index: int | None = None,
) -> set[str]:
    existing = set()

    for day_key, day in itinerary_data.items():
        try:
            day_number = int(day_key)
        except (TypeError, ValueError):
            day_number = None

        # We still inspect the selected day unless a specific item
        # is being excluded.
        for index, place in enumerate(day.places):
            if (
                day_number == exclude_day
                and exclude_item_type == "place"
                and exclude_item_index == index
            ):
                continue

            existing.add(_normalize(place.name))

        for index, food in enumerate(day.food):
            if (
                day_number == exclude_day
                and exclude_item_type == "food"
                and exclude_item_index == index
            ):
                continue

            existing.add(_normalize(food.restaurant))

        for index, activity in enumerate(day.activities):
            if (
                day_number == exclude_day
                and exclude_item_type == "activity"
                and exclude_item_index == index
            ):
                continue

            existing.add(_normalize(activity.name))

    return existing


async def add_day_images(
    day_data: dict,
    destination: str,
) -> dict:
    places = day_data.get("places", [])

    if isinstance(places, list):
        for place in places:
            if not isinstance(place, dict):
                continue

            name = place.get("name", "").strip()

            if name:
                place["image"] = await search_image(
                    item_name=name,
                    destination=destination,
                )

    food = day_data.get("food", [])

    if isinstance(food, list):
        for item in food:
            if not isinstance(item, dict):
                continue

            restaurant = item.get("restaurant", "").strip()

            if restaurant:
                item["image"] = await search_image(
                    item_name=restaurant,
                    destination=destination,
                )

    activities = day_data.get("activities", [])

    if isinstance(activities, list):
        for activity in activities:
            if not isinstance(activity, dict):
                continue

            name = activity.get("name", "").strip()

            if name:
                activity["image"] = await search_image(
                    item_name=name,
                    destination=destination,
                )

    return day_data


def validate_day_has_no_duplicates(
    regenerated_day: DayItinerary,
    existing_names: set[str],
) -> None:
    generated_names: list[str] = []

    for place in regenerated_day.places:
        generated_names.append(_normalize(place.name))

    for food in regenerated_day.food:
        generated_names.append(_normalize(food.restaurant))

    for activity in regenerated_day.activities:
        generated_names.append(_normalize(activity.name))

    # Check against other days.
    duplicates_with_existing = [
        name
        for name in generated_names
        if name in existing_names
    ]

    if duplicates_with_existing:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Regenerated day contains items already used elsewhere in the itinerary",
                "duplicates": duplicates_with_existing,
            },
        )

    # Check duplicates inside the newly generated day itself.
    seen = set()

    for name in generated_names:
        if name in seen:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Regenerated day contains duplicate items",
                    "duplicate": name,
                },
            )

        seen.add(name)


def validate_item_has_no_duplicate(
    item,
    existing_names: set[str],
    item_type: str,
) -> None:
    if item_type == "food":
        name = _normalize(item.restaurant)
    else:
        name = _normalize(item.name)

    if name in existing_names:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Regenerated item already exists in the itinerary",
                "duplicate": name,
            },
        )


async def regenerate_day(
    request: RegenerateDayRequest,
) -> DayItinerary:
    prompt = build_regenerate_day_prompt(request)

    try:
        ai_response = await generate_ai_response(prompt)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Failed to regenerate day using AI",
        ) from exc

    if not isinstance(ai_response, dict):
        raise HTTPException(
            status_code=502,
            detail="AI returned an invalid regeneration response",
        )

    try:
        day = DayItinerary.model_validate(ai_response)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="AI returned an invalid day structure",
        ) from exc

    # Names from every OTHER day.
    other_day_names = get_existing_item_names(
        request.itinerary_data,
        exclude_day=request.day_number,
    )

    validate_day_has_no_duplicates(
        regenerated_day=day,
        existing_names=other_day_names,
    )

    # Replace the selected day in a copy of the complete itinerary.
    updated_itinerary = dict(request.itinerary_data)

    updated_itinerary[str(request.day_number)] = day

    # Check total trip cost, not just regenerated day cost.
    total_cost = calculate_itinerary_cost(updated_itinerary)

    if total_cost > request.budget:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Regenerated itinerary exceeds the trip budget",
                "budget": request.budget,
                "estimated_cost": total_cost,
            },
        )

    day_data = day.model_dump()

    await add_day_images(
        day_data=day_data,
        destination=request.destination,
    )

    try:
        return DayItinerary.model_validate(day_data)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Regenerated day could not be validated",
        ) from exc


async def regenerate_item(
    request: RegenerateItemRequest,
):
    prompt = build_regenerate_item_prompt(request)

    try:
        ai_response = await generate_ai_response(prompt)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Failed to regenerate item using AI",
        ) from exc

    if not isinstance(ai_response, dict):
        raise HTTPException(
            status_code=502,
            detail="AI returned an invalid regeneration response",
        )

    try:
        if request.item_type == "place":
            item = Place.model_validate(ai_response)

        elif request.item_type == "food":
            item = Food.model_validate(ai_response)

        else:
            item = Activity.model_validate(ai_response)

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="AI returned an invalid item structure",
        ) from exc

    existing_names = get_existing_item_names(
        request.itinerary_data,
        exclude_day=request.day_number,
        exclude_item_type=request.item_type,
        exclude_item_index=request.item_index,
    )

    validate_item_has_no_duplicate(
        item=item,
        existing_names=existing_names,
        item_type=request.item_type,
    )

    # Replace the item in a copy of the complete itinerary.
    updated_itinerary = {
        day_number: day
        for day_number, day in request.itinerary_data.items()
    }

    selected_day_key = str(request.day_number)

    if selected_day_key not in updated_itinerary:
        raise HTTPException(
            status_code=400,
            detail="Selected day does not exist",
        )

    selected_day = updated_itinerary[selected_day_key]

    if request.item_type == "place":
        if request.item_index >= len(selected_day.places):
            raise HTTPException(
                status_code=400,
                detail="Invalid place index",
            )

        selected_day.places[request.item_index] = item

    elif request.item_type == "food":
        if request.item_index >= len(selected_day.food):
            raise HTTPException(
                status_code=400,
                detail="Invalid food index",
            )

        selected_day.food[request.item_index] = item

    else:
        if request.item_index >= len(selected_day.activities):
            raise HTTPException(
                status_code=400,
                detail="Invalid activity index",
            )

        selected_day.activities[request.item_index] = item

    total_cost = calculate_itinerary_cost(updated_itinerary)

    if total_cost > request.budget:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Regenerated item causes the itinerary to exceed the trip budget",
                "budget": request.budget,
                "estimated_cost": total_cost,
            },
        )

    item_data = item.model_dump()

    if request.item_type == "food":
        search_name = item_data.get("restaurant", "")
    else:
        search_name = item_data.get("name", "")

    if search_name:
        item_data["image"] = await search_image(
            item_name=search_name,
            destination=request.destination,
        )

    try:
        if request.item_type == "place":
            return Place.model_validate(item_data)

        if request.item_type == "food":
            return Food.model_validate(item_data)

        return Activity.model_validate(item_data)

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Regenerated item could not be validated",
        ) from exc