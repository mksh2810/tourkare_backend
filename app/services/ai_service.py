
import json

import httpx
from fastapi import HTTPException

from app.core.config import settings


async def generate_ai_response(prompt: str) -> dict:
    """
    Send a prompt to OpenRouter and return
    the generated JSON response.
    """

    if not settings.ai_api_key:
        raise HTTPException(
            status_code=503,
            detail="OpenRouter API key is not configured",
        )

    if not settings.ai_model:
        raise HTTPException(
            status_code=503,
            detail="OpenRouter model is not configured",
        )

    url = (
        f"{settings.ai_base_url.rstrip('/')}"
        "/chat/completions"
    )

    headers = {
        "Authorization": f"Bearer {settings.ai_api_key}",
        "Content-Type": "application/json",
        "X-OpenRouter-Title": "TourKare",
    }

    payload = {
        "model": settings.ai_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are TourKare, a personalized "
                    "travel itinerary planner. Follow "
                    "the user's instructions and return "
                    "valid JSON only."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "response_format": {
            "type": "json_object"
        },
        "temperature": 0.7,
    }

    try:
        async with httpx.AsyncClient(
            timeout=120.0
        ) as client:
            response = await client.post(
                url,
                headers=headers,
                json=payload,
            )

            response.raise_for_status()
            data = response.json()

        choices = data.get("choices", [])

        if not choices:
            print("OpenRouter returned no choices:")
            print(data)

            raise HTTPException(
                status_code=502,
                detail={
                    "message": "OpenRouter returned no choices",
                    "response": data,
                },
            )

        choice = choices[0]
        message = choice.get("message") or {}

        content = message.get("content")
        finish_reason = choice.get("finish_reason")
        native_finish_reason = choice.get("native_finish_reason")

        if not content or not content.strip():
            print("OpenRouter returned an empty response.")
            print("Model:", data.get("model"))
            print("Finish reason:", finish_reason)
            print("Native finish reason:", native_finish_reason)
            print("Message keys:", list(message.keys()))
            print("Reasoning present:", bool(message.get("reasoning")))
            print("Tool calls:", message.get("tool_calls"))

            raise HTTPException(
                status_code=502,
                detail={
                    "message": "OpenRouter returned an empty response",
                    "model": data.get("model"),
                    "finish_reason": finish_reason,
                    "native_finish_reason": native_finish_reason,
                    "reasoning_present": bool(message.get("reasoning")),
                    "tool_calls_present": bool(message.get("tool_calls")),
                },
            )

        try:
            result = json.loads(content)

        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=502,
                detail="OpenRouter returned invalid JSON",
            ) from exc

        if not isinstance(result, dict):
            raise HTTPException(
                status_code=502,
                detail="OpenRouter response must be a JSON object",
            )

        return result

    except HTTPException:
        raise

    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code

        try:
            error_data = exc.response.json()
            error_message = error_data.get(
                "error", {}
            ).get(
                "message", "No error message provided"
            )
        except (ValueError, AttributeError):
            error_message = exc.response.text[:1000]

        # Log diagnostic information without logging credentials.
        print(f"OpenRouter HTTP error: {status_code}")
        print(f"OpenRouter details: {error_message}")

        raise HTTPException(
            status_code=502,
            detail={
                "message": "OpenRouter request failed",
                "openrouter_status": status_code,
                "openrouter_error": error_message,
            },
        ) from exc

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail="Could not connect to OpenRouter",
        ) from exc

    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Unexpected response from OpenRouter",
        ) from exc