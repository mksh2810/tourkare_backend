import httpx

from app.core.config import settings


UNSPLASH_SEARCH_URL = "https://api.unsplash.com/search/photos"


async def search_image(
    item_name: str,
    destination: str,
) -> str:
    """
    Search Unsplash for an image matching an itinerary item.

    Returns:
        A hotlinked Unsplash image URL, or an empty string if
        no suitable image is found.
    """

    if not settings.unsplash_access_key:
        print("❌ Unsplash API key is missing")
        return ""

    query = f"{item_name} {destination}"

    headers = {
        "Authorization": f"Client-ID {settings.unsplash_access_key}",
    }

    params = {
        "query": query,
        "per_page": 1,
        "orientation": "landscape",
    }

    print()
    print("🔎 Unsplash search")
    print("   Item:", item_name)
    print("   Query:", query)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                UNSPLASH_SEARCH_URL,
                headers=headers,
                params=params,
            )

        print("   Status:", response.status_code)

        if response.status_code != 200:
            print("❌ Unsplash request failed")
            print("   Response:", response.text)
            return ""

        data = response.json()
        results = data.get("results", [])

        if not results:
            print("⚠️ No image found")
            return ""

        photo = results[0]
        urls = photo.get("urls", {})

        image_url = urls.get("regular", "")

        if not image_url:
            print("⚠️ Image result found, but URL is missing")
            return ""

        print("✅ Image found")
        print("   URL:", image_url)

        return image_url

    except Exception as exc:
        print("❌ Unsplash image search error:", exc)
        return ""