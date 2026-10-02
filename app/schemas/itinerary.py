from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TripCreate(BaseModel):
    destination: str = Field(
        min_length=2,
        max_length=100,
    )

    days: int = Field(
        gt=0,
        le=30,
    )

    budget: float = Field(
        gt=0,
        le=100_000_000,
    )

    interests: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    food_preference: Literal[
        "veg",
        "non_veg",
        "vegan",
        "jain",
        "eggetarian",
    ] = "veg"


class Place(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    image: str = ""
    location: str = ""
    time: str
    price: float = Field(ge=0)
    rating: float = Field(
        ge=0,
        le=5,
    )
    description: str


class Food(BaseModel):
    model_config = ConfigDict(extra="ignore")

    restaurant: str
    image: str = ""
    location: str = ""
    meal: str
    time: str
    price: float = Field(ge=0)
    rating: float = Field(
        ge=0,
        le=5,
    )
    dishes: str


class Activity(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    image: str = ""
    location: str = ""
    time: str
    duration: str
    price: float = Field(ge=0)
    rating: float = Field(
        ge=0,
        le=5,
    )
    description: str


class DayItinerary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str

    places: list[Place] = Field(
        default_factory=list,
    )

    food: list[Food] = Field(
        default_factory=list,
    )

    activities: list[Activity] = Field(
        default_factory=list,
    )


class ItineraryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    estimated_cost: float = Field(ge=0)

    itineraryData: dict[int, DayItinerary]


class RegenerateDayRequest(BaseModel):
    destination: str = Field(
        min_length=2,
        max_length=100,
    )

    budget: float = Field(
        gt=0,
        le=100_000_000,
    )

    interests: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    food_preference: Literal[
        "veg",
        "non_veg",
        "vegan",
        "jain",
        "eggetarian",
    ] = "veg"

    day_number: int = Field(
        gt=0,
        le=30,
    )

    current_day: DayItinerary

    itinerary_data: dict[str, DayItinerary] = Field(
        default_factory=dict,
    )


class RegenerateItemRequest(BaseModel):
    destination: str = Field(
        min_length=2,
        max_length=100,
    )

    budget: float = Field(
        gt=0,
        le=100_000_000,
    )

    interests: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    food_preference: Literal[
        "veg",
        "non_veg",
        "vegan",
        "jain",
        "eggetarian",
    ] = "veg"

    day_number: int = Field(
        gt=0,
        le=30,
    )

    item_type: Literal[
        "place",
        "food",
        "activity",
    ]

    item_index: int = Field(
        ge=0,
    )

    current_day: DayItinerary

    itinerary_data: dict[str, DayItinerary] = Field(
        default_factory=dict,
    )