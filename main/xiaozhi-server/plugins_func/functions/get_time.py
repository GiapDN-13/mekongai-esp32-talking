from datetime import datetime
import cnlunar
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

_WEEKDAYS_VI = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]


def _weekday_vi(dt: datetime) -> str:
    return _WEEKDAYS_VI[dt.weekday()]


get_lunar_function_desc = {
    "type": "function",
    "function": {
        "name": "get_lunar",
        "description": (
            "Tra cứu giờ hiện tại, ngày dương lịch, thứ, âm lịch, ngày tốt xấu. "
            "Gọi tool này khi người dùng hỏi: 'mấy giờ rồi', 'bây giờ mấy giờ', "
            "'hôm nay ngày mấy', 'hôm nay thứ mấy', 'hôm nay âm lịch mấy', "
            "'năm nay con giáp gì', 'ngày mai có tốt không'. "
            "Nếu không nêu ngày cụ thể, mặc định dùng ngày hiện tại."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Ngày cần tra, định dạng YYYY-MM-DD. Bỏ trống = ngày hiện tại.",
                },
                "query": {
                    "type": "string",
                    "description": "Nội dung cần tra: âm lịch, can chi, tiết khí, con giáp, ngày tốt xấu...",
                },
            },
            "required": [],
        },
    },
}


@register_function("get_lunar", get_lunar_function_desc, ToolType.WAIT)
def get_lunar(conn: "ConnectionHandler" = None, date=None, query=None):
    """Tra cứu âm lịch, can chi, tiết khí, con giáp, ngày tốt xấu."""
    from core.utils.cache.manager import cache_manager, CacheType

    if date:
        try:
            now = datetime.strptime(str(date), "%Y-%m-%d")
        except ValueError:
            return ActionResponse(
                Action.REQLLM,
                "Sai định dạng ngày. Vui lòng dùng YYYY-MM-DD, ví dụ: 2024-01-01",
                None,
            )
    else:
        now = datetime.now()

    current_date = now.strftime("%Y-%m-%d")

    if query is None:
        query = "năm can chi và ngày âm lịch"

    lunar_cache_key = f"lunar_info_{current_date}"
    cached_lunar_info = cache_manager.get(CacheType.LUNAR, lunar_cache_key)
    if cached_lunar_info:
        return ActionResponse(Action.REQLLM, cached_lunar_info, None)

    try:
        lunar = cnlunar.Lunar(now, godType="8char")
    except Exception as e:
        return ActionResponse(
            Action.REQLLM,
            f"Không thể tra cứu âm lịch cho ngày {current_date}: {e}",
            None,
        )

    holidays = ", ".join(
        filter(
            None,
            (
                lunar.get_legalHolidays(),
                lunar.get_otherHolidays(),
                lunar.get_otherLunarHolidays(),
            ),
        )
    )

    response_text = (
        f"Giờ hiện tại: {now.strftime('%H:%M')} — "
        f"{_weekday_vi(now)}, {now.strftime('%d/%m/%Y')}\n"
        f"Âm lịch: {lunar.lunarYearCn} năm {lunar.lunarMonthCn[:-1]} {lunar.lunarDayCn}\n"
        f"Can chi: năm {lunar.year8Char}, tháng {lunar.month8Char}, ngày {lunar.day8Char}\n"
        f"Con giáp: {lunar.chineseYearZodiac}\n"
        f"Bát tự: {lunar.year8Char} {lunar.month8Char} {lunar.day8Char} {lunar.twohour8Char}\n"
    )
    if holidays:
        response_text += f"Ngày lễ: {holidays}\n"
    response_text += (
        f"Tiết khí hôm nay: {lunar.todaySolarTerms}\n"
        f"Tiết khí tiếp theo: {lunar.nextSolarTerm} — {lunar.nextSolarTermYear}/{lunar.nextSolarTermDate[0]}/{lunar.nextSolarTermDate[1]}\n"
        f"Cung hoàng đạo: {lunar.starZodiac}\n"
        f"Nên: {'、'.join(lunar.goodThing[:8])}\n"
        f"Kiêng: {'、'.join(lunar.badThing[:8])}\n"
        "(Mặc định trả về can chi và âm lịch; chỉ nêu ngày tốt xấu khi người dùng hỏi)"
    )

    cache_manager.set(CacheType.LUNAR, lunar_cache_key, response_text)
    return ActionResponse(Action.REQLLM, response_text, None)
