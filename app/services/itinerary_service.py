from fastapi import HTTPException

from app.schemas.itinerary import DayItinerary, ItineraryResponse
from app.services.ai_service import generate_ai_response
from app.services.prompt_service import build_itinerary_prompt
from app.services.unsplash_service import search_image


async def add_images(
    itinerary_data: dict,
    destination: str,
) -> dict:
    """
    Add Unsplash images to places, food, and activities.

    If an image cannot be found, the item's image remains empty.
    """

    for day_data in itinerary_data.values():
        if not isinstance(day_data, dict):
            continue

        # -------------------------
        # Places
        # -------------------------
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

        # -------------------------
        # Food
        # -------------------------
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

        # -------------------------
        # Activities
        # -------------------------
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

    return itinerary_data


async def generate_itinerary(trip):
    prompt = build_itinerary_prompt(trip)

    # -------------------------
    # Generate itinerary using AI
    # -------------------------
    try:
        ai_response = await generate_ai_response(prompt)

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Failed to generate itinerary from AI",
        ) from exc

    # -------------------------
    # Check itineraryData
    # -------------------------
    itinerary_data = ai_response.get("itineraryData")

    if not isinstance(itinerary_data, dict):
        raise HTTPException(
            status_code=502,
            detail="AI response is missing valid itineraryData",
        )

    # -------------------------
    # Check requested days
    # -------------------------
    expected_days = {
        str(day)
        for day in range(1, trip.days + 1)
    }

    actual_days = set(itinerary_data.keys())

    if actual_days != expected_days:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "AI returned incorrect day structure",
                "expected_days": sorted(expected_days),
                "received_days": sorted(actual_days),
            },
        )

    # -------------------------
    # Validate itinerary
    # -------------------------
    validated_itinerary = {}
    estimated_cost = 0.0

    try:
        for day_number in range(1, trip.days + 1):
            day_key = str(day_number)

            # Validate the complete day's structure
            day = DayItinerary.model_validate(
                itinerary_data[day_key]
            )

            validated_itinerary[day_number] = day

            # Add place prices
            for place in day.places:
                estimated_cost += place.price

            # Add food prices
            for food in day.food:
                estimated_cost += food.price

            # Add activity prices
            for activity in day.activities:
                estimated_cost += activity.price

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="AI response does not match the expected itinerary schema",
        ) from exc

    # -------------------------
    # Calculate total cost
    # -------------------------
    estimated_cost = round(estimated_cost, 2)

    # -------------------------
    # Check budget
    # -------------------------
    if estimated_cost > trip.budget:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Generated itinerary exceeds the requested budget",
                "budget": trip.budget,
                "estimated_cost": estimated_cost,
            },
        )

    # -------------------------
    # Convert Pydantic models
    # back to dictionaries
    # -------------------------
    enriched_itinerary = {
        str(day_number): day.model_dump()
        for day_number, day in validated_itinerary.items()
    }

    # -------------------------
    # Add Unsplash images
    # -------------------------
    enriched_itinerary = await add_images(
        itinerary_data=enriched_itinerary,
        destination=trip.destination,
    )

    # -------------------------
    # Validate enriched data
    # -------------------------
    final_itinerary = {
        int(day_number): DayItinerary.model_validate(day_data)
        for day_number, day_data in enriched_itinerary.items()
    }

    # -------------------------
    # Return final response
    # -------------------------
    return ItineraryResponse(
        estimated_cost=estimated_cost,
        itineraryData=final_itinerary,
    )