import json

from app.schemas.itinerary import (
    RegenerateDayRequest,
    RegenerateItemRequest,
    TripCreate,
)

def build_itinerary_prompt(trip: TripCreate) -> str:
    interests = ", ".join(trip.interests) or "General sightseeing"

    return f"""
You are TourKare, an AI travel itinerary planner.

Create a practical, personalized {trip.days}-day itinerary for:

Destination: {trip.destination}
Budget: INR {trip.budget}
Interests: {interests}
Food preference: {trip.food_preference}

Return ONLY valid JSON. No markdown, explanations, or code fences.

Use exactly this structure:

{{
  "estimated_cost": 0,
  "itineraryData": {{
    "1": {{
      "title": "Day title",
      "places": [
        {{
          "name": "Baga Beach",
          "image": "",
          "location": "Baga, North Goa, Goa",
          "time": "10:00 AM - 12:00 PM",
          "price": 0,
          "rating": 4.5,
          "description": "Relax at the beach and explore the surrounding area."
        }}
      ],
      "food": [
        {{
          "restaurant": "Local Spice Kitchen",
          "image": "",
          "location": "Panaji, Goa, India",
          "meal": "Lunch",
          "time": "1:00 PM - 2:00 PM",
          "price": 500,
          "rating": 4.5,
          "dishes": "Dish names"
        }}
      ],
      "activities": [
        {{
          "name": "Sunset Cruise",
          "image": "",
          "location": "Mandovi River, Panaji, Goa, India",
          "time": "5:00 PM - 7:00 PM",
          "duration": "2 hours",
          "price": 1000,
          "rating": 4.5,
          "description": "Short description"
        }}
      ]
    }}
  }}
}}

ITINERARY RULES:

You MUST generate exactly {trip.days} complete days.

For this request, the required day keys are:
{", ".join(f'"{day}"' for day in range(1, trip.days + 1))}

Every required day must be present in itineraryData.
Never return only the first day.
Do not stop generating until all required days are complete.
- Each day must contain exactly: title, places, food, activities.
- Use real and relevant places and activities at the destination.
- Prioritize the user's interests throughout the trip.
- Avoid unnecessary repetition.
- Keep the itinerary practical and achievable.
- Use realistic times and durations.
- Never overlap activities.
- Include reasonable time for meals, breaks, and travel.
- Group geographically close locations together.
- Do not schedule distant locations together when travel time makes it impractical.
- Do not include transportation or accommodation.

BUDGET:

- All prices must be numeric INR values.
- Keep the total of all places, food, and activities within INR {trip.budget}.
- estimated_cost must equal the sum of every item price across all days.
- estimated_cost must be numeric.
- Ratings must be numeric from 0 to 5.
- Do not fabricate image URLs. Keep image as "".

FOOD:

- Follow the selected food preference exactly.
- Prefer well-known restaurants with strong confidence.
- Do not invent restaurants or dishes.
- For Jain or vegan food, only include a restaurant when dietary compatibility is highly confident.
- If suitable food cannot be confidently identified, return an empty food list.
- It is better to return no food recommendation than an incorrect one.

Food rules:
- veg: no meat, fish, seafood, or eggs.
- non_veg: meat, fish, seafood, and eggs are allowed.
- vegan: no meat, fish, seafood, eggs, dairy, paneer, butter, ghee, milk, or cream.
- jain: restaurant must explicitly offer Jain food; no meat, fish, seafood, eggs, onion, garlic, potatoes, carrots, radish, beetroot, or other root vegetables.
- eggetarian: vegetarian food and eggs allowed; no meat, fish, or seafood.

For Jain or vegan food, do not assume that a vegetarian restaurant provides suitable food.
If a restaurant, dish, location, operating status, or food compatibility cannot be confidently verified, DO NOT use it.

If no suitable restaurant can be confidently verified, return:
"food": []

Never fabricate a restaurant, dish, menu, price, rating, location, or dietary claim just to fill the itinerary.

LOCATION REQUIREMENTS:

For EVERY place, restaurant, and activity, provide a realistic
specific location.

The location should identify where the item is physically located.

Examples:

Place:
"location": "Baga, North Goa, Goa, India"

Restaurant:
"location": "Calangute, North Goa, Goa, India"

Activity:
"location": "Mandovi River, Panaji, Goa, India"

Do not use only the destination as the location unless the item
actually covers the entire destination.

Do not invent precise street addresses unless you are confident
they are real.

A neighborhood, area, landmark, beach, district, or known venue
is acceptable.

The location will be used to open the item in Google Maps.

OUTPUT:

- Return exactly the JSON structure above.
- Use day keys "1", "2", "3", etc.
- Do not add extra keys.
- Ensure the JSON is valid and parseable.
"""

def build_regenerate_day_prompt(
    request: RegenerateDayRequest,
) -> str:
    itinerary = {
        str(day_number): day.model_dump()
        for day_number, day in request.itinerary_data.items()
    }

    current_day = request.current_day.model_dump()

    interests = ", ".join(request.interests) or "General sightseeing"

    return f"""
You are TourKare, an AI travel itinerary planner.

The user wants to regenerate ONLY Day {request.day_number}
of an existing {len(itinerary)}-day trip.

Destination:
{request.destination}

Total trip budget:
INR {request.budget}

User interests:
{interests}

Food preference:
{request.food_preference}

CURRENT DAY BEING REPLACED:
{json.dumps(current_day, indent=2)}

FULL EXISTING ITINERARY:
{json.dumps(itinerary, indent=2)}

IMPORTANT:

You MUST generate ONLY the replacement for Day {request.day_number}.

Do NOT generate other days.

The other days are already finalized and must remain unchanged.

MOST IMPORTANT DUPLICATE RULE:

You MUST NOT reuse any place, restaurant, or activity that already
appears on ANY OTHER DAY.

Before generating the replacement day, inspect every other day in the
FULL EXISTING ITINERARY.

The following are forbidden on the regenerated day if they already
exist on another day:

- same place
- same restaurant
- same activity

Do not merely change the description or time of an existing item.
It must be a genuinely different recommendation.

Items from the OLD version of Day {request.day_number} MAY be reused
only if necessary, but prefer different items when possible.

The regenerated day must:

- fit the user's interests
- fit the destination
- follow the food preference
- have realistic timings
- avoid overlapping schedules
- account for realistic travel time
- stay within the overall trip budget
- contain only realistic places
- contain only realistic restaurants
- contain only realistic activities

For restaurants, follow the same strict restaurant verification
rules as the original itinerary generation.

Return ONLY the JSON object for Day {request.day_number}.

Do NOT return:
- estimated_cost
- itineraryData
- other days
- markdown
- explanations
- code fences

Return exactly:

{{
  "title": "...",
  "places": [],
  "food": [],
  "activities": []
}}

All image fields MUST be empty strings.

Prices must be numeric INR values.

Ratings must be numeric values between 0 and 5.

Do not include transportation costs.

Do not include accommodation costs.

LOCATION REQUIREMENT:

Every generated place, restaurant, and activity MUST include a
realistic location field.

For example:

Place:
"location": "Baga, North Goa, Goa, India"

Food:
"location": "Calangute, North Goa, Goa, India"

Activity:
"location": "Mandovi River, Panaji, Goa, India"

The location must correspond to the actual item and destination.

Do not use only the destination unless appropriate.

The location will be used for Google Maps navigation.

The output must be valid JSON.
"""

def build_regenerate_item_prompt(
    request: RegenerateItemRequest,
) -> str:
    itinerary = {
        str(day_number): day.model_dump()
        for day_number, day in request.itinerary_data.items()
    }

    current_day = request.current_day.model_dump()

    if request.item_type == "place":
        current_items = current_day.get("places", [])
    elif request.item_type == "food":
        current_items = current_day.get("food", [])
    else:
        current_items = current_day.get("activities", [])

    current_item = {}

    if (
        isinstance(current_items, list)
        and 0 <= request.item_index < len(current_items)
    ):
        current_item = current_items[request.item_index]

    interests = ", ".join(request.interests) or "General sightseeing"

    return f"""
You are TourKare, an AI travel itinerary planner.

The user wants to regenerate exactly ONE item.

Destination:
{request.destination}

Day:
{request.day_number}

Item type:
{request.item_type}

Total trip budget:
INR {request.budget}

User interests:
{interests}

Food preference:
{request.food_preference}

CURRENT ITEM:
{json.dumps(current_item, indent=2)}

CURRENT DAY:
{json.dumps(current_day, indent=2)}

FULL EXISTING ITINERARY:
{json.dumps(itinerary, indent=2)}

Generate exactly ONE replacement {request.item_type}.

IMPORTANT DUPLICATE RULE:

The replacement MUST NOT duplicate an existing item anywhere
in the itinerary.

Check all other days and the other items on the current day.

For a place:
- do not reuse an existing place.

For food:
- do not reuse an existing restaurant.

For activity:
- do not reuse an existing activity.

Do not simply rename an existing item.

The replacement must:

- match the destination
- match the user's interests
- fit the existing day's schedule
- follow the food preference
- have realistic pricing
- have a realistic rating
- be different from existing items
- be valid for the requested item type

For food, follow the strict restaurant verification rules
from the original itinerary generation prompt.

Return ONLY the replacement item.

Do NOT return:
- markdown
- explanations
- code fences
- an array
- a day object
- itineraryData
- estimated_cost

Return exactly one JSON object.

If item type is "place":

{{
  "name": "...",
  "image": "",
  "location": "...",
  "time": "...",
  "price": 0,
  "rating": 0,
  "description": "..."
}}

If item type is "food":

{{
  "restaurant": "...",
  "image": "",
  "location": "...",
  "meal": "...",
  "time": "...",
  "price": 0,
  "rating": 0,
  "dishes": "..."
}}

If item type is "activity":

{{
  "name": "...",
  "image": "",
  "location": "...",
  "time": "...",
  "duration": "...",
  "price": 0,
  "rating": 0,
  "description": "..."
}}

The JSON must be valid.
"""