import requests
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from config.logger import setup_logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

GET_WEATHER_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": (
            "Lấy thông tin thời tiết tại một địa điểm. "
            "Ví dụ: 'thời tiết Hà Nội', 'Sài Gòn hôm nay thế nào'. "
            "Nếu không nêu địa điểm, dùng 'Hanoi'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "Tên thành phố (tiếng Anh hoặc Việt không dấu). Ví dụ: Hanoi, Da Nang, Ho Chi Minh",
                },
            },
            "required": [],
        },
    },
}


@register_function("get_weather", GET_WEATHER_FUNCTION_DESC, ToolType.WAIT)
def get_weather(conn: "ConnectionHandler", location: str = "Hanoi"):
    """Lấy thời tiết qua wttr.in — free, không cần API key."""
    from core.utils.cache.manager import cache_manager, CacheType

    if not location or not location.strip():
        location = "Hanoi"

    cache_key = f"weather_{location.strip().lower()}"
    cached = cache_manager.get(CacheType.WEATHER, cache_key)
    if cached:
        return ActionResponse(Action.REQLLM, cached, None)

    try:
        url = f"https://wttr.in/{location.strip()}?format=j1&lang=vi"
        resp = requests.get(url, timeout=8, headers={"Accept": "application/json"})
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.bind(tag=TAG).warning(f"wttr.in request failed: {e}")
        return ActionResponse(
            Action.REQLLM,
            f"Không thể lấy thời tiết cho {location}. Hãy trả lời dựa trên kiến thức chung.",
            None,
        )

    try:
        current = data["current_condition"][0]
        area = data.get("nearest_area", [{}])[0]
        city = area.get("areaName", [{}])[0].get("value", location)

        temp_c = current.get("temp_C", "?")
        feels_like = current.get("FeelsLikeC", "?")
        humidity = current.get("humidity", "?")
        desc_vi = current.get("lang_vi", [{}])
        desc = desc_vi[0].get("value", "") if desc_vi else current.get("weatherDesc", [{}])[0].get("value", "")
        wind_kmph = current.get("windspeedKmph", "?")

        report = (
            f"Thời tiết {city}: {desc}, "
            f"nhiệt độ {temp_c}°C (cảm giác {feels_like}°C), "
            f"độ ẩm {humidity}%, gió {wind_kmph} km/h."
        )

        forecasts = data.get("weather", [])[:3]
        if forecasts:
            report += "\nDự báo:"
            for day in forecasts:
                date = day.get("date", "")
                max_t = day.get("maxtempC", "?")
                min_t = day.get("mintempC", "?")
                hourly = day.get("hourly", [{}])
                mid = hourly[len(hourly) // 2] if hourly else {}
                day_desc_vi = mid.get("lang_vi", [{}])
                day_desc = day_desc_vi[0].get("value", "") if day_desc_vi else ""
                report += f"\n  {date}: {min_t}~{max_t}°C, {day_desc}"

        cache_manager.set(CacheType.WEATHER, cache_key, report)
        return ActionResponse(Action.REQLLM, report, None)

    except (KeyError, IndexError) as e:
        logger.bind(tag=TAG).warning(f"wttr.in parse error: {e}")
        return ActionResponse(
            Action.REQLLM,
            f"Đã lấy dữ liệu thời tiết nhưng không đọc được. Trả lời chung cho {location}.",
            None,
        )
