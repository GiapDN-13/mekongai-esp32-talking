import random
import requests
import json
from config.logger import setup_logging
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from markitdown import MarkItDown
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler


TAG = __name__
logger = setup_logging()

CHANNEL_MAP = {
    # Nguồn Việt Nam
    "VnExpress": "vnexpress",
    "Tuổi Trẻ": "tuoitre",
    "Thanh Niên": "thanhnien",
    "Dân Trí": "dantri",
    "VietnamNet": "vietnamnet",
    "Zing News": "zingnews",
    "Nhân Dân": "nhandan",
    "Lao Động": "laodong",
    "Báo Mới": "baomoi",
    # Nguồn quốc tế
    "Hacker News": "hackernews",
    "Product Hunt": "producthunt",
    "Github": "github-trending-today",
    # Nguồn Trung Quốc (giữ lại phòng cần)
    "澎湃新闻": "thepaper",
    "百度热搜": "baidu",
    "微博": "weibo",
    "36氪": "36kr-quick",
    "哔哩哔哩": "bilibili-hot-search",
}

DEFAULT_NEWS_SOURCES = "VnExpress;Tuổi Trẻ;Thanh Niên"


def get_news_sources_from_config(conn):
    """Lấy chuỗi nguồn tin từ config"""
    try:
        if (
            conn.config.get("plugins")
            and conn.config["plugins"].get("get_news_from_newsnow")
            and conn.config["plugins"]["get_news_from_newsnow"].get("news_sources")
        ):
            news_sources_config = conn.config["plugins"]["get_news_from_newsnow"][
                "news_sources"
            ]

            if isinstance(news_sources_config, str) and news_sources_config.strip():
                logger.bind(tag=TAG).debug(f"Using configured news sources: {news_sources_config}")
                return news_sources_config
            else:
                logger.bind(tag=TAG).warning("News source config empty or invalid; using defaults")
        else:
            logger.bind(tag=TAG).debug("No news source config; using defaults")

        return DEFAULT_NEWS_SOURCES

    except Exception as e:
        logger.bind(tag=TAG).error(f"Failed to load news source config: {e}; using defaults")
        return DEFAULT_NEWS_SOURCES


available_sources = list(CHANNEL_MAP.keys())
example_sources_str = ", ".join(available_sources)

GET_NEWS_FROM_NEWSNOW_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "get_news_from_newsnow",
        "description": (
            "Lấy tin tức mới nhất, chọn ngẫu nhiên một tin để đọc. "
            f"Người dùng có thể chọn nguồn tin: {example_sources_str}. "
            "Nếu không chỉ định, mặc định lấy từ VnExpress. "
            "Người dùng có thể yêu cầu xem chi tiết tin vừa đọc."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": f"Tên nguồn tin, ví dụ: {example_sources_str}. Không bắt buộc.",
                },
                "detail": {
                    "type": "boolean",
                    "description": "Có lấy chi tiết không, mặc định false. Nếu true, lấy nội dung chi tiết tin trước đó.",
                },
                "lang": {
                    "type": "string",
                    "description": "Mã ngôn ngữ: vi_VN, en_US, zh_CN... Mặc định vi_VN",
                },
            },
            "required": ["lang"],
        },
    },
}


def fetch_news_from_api(conn: "ConnectionHandler", source="vnexpress"):
    """Lấy danh sách tin từ API"""
    try:
        api_url = f"https://newsnow.busiyi.world/api/s?id={source}"

        news_config = conn.config.get("plugins", {}).get("get_news_from_newsnow", {})
        if news_config.get("url"):
            api_url = news_config["url"] + source

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()

        if "items" in data:
            return data["items"]
        else:
            logger.bind(tag=TAG).error(f"News API response format error: {data}")
            return []

    except Exception as e:
        logger.bind(tag=TAG).error(f"News API request failed: {e}")
        return []


def fetch_news_detail(url):
    """Lấy nội dung chi tiết tin tức"""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        md = MarkItDown(enable_plugins=False)
        result = md.convert(response)

        clean_text = result.text_content

        if not clean_text or len(clean_text.strip()) == 0:
            logger.bind(tag=TAG).warning(f"News detail empty after cleanup: {url}")
            return "Không thể phân tích nội dung tin. Có thể trang web có cấu trúc đặc biệt."

        return clean_text
    except Exception as e:
        logger.bind(tag=TAG).error(f"Failed to fetch news detail: {e}")
        return "Không thể lấy nội dung chi tiết"


@register_function(
    "get_news_from_newsnow",
    GET_NEWS_FROM_NEWSNOW_FUNCTION_DESC,
    ToolType.SYSTEM_CTL,
)
def get_news_from_newsnow(
    conn: "ConnectionHandler",
    source: str = "VnExpress",
    detail: bool = False,
    lang: str = "vi_VN",
):
    """Lấy tin tức và chọn ngẫu nhiên một tin để đọc, hoặc lấy chi tiết tin trước đó"""
    try:
        news_sources = get_news_sources_from_config(conn)

        detail = str(detail).lower() == "true"
        if detail:
            if (
                not hasattr(conn, "last_newsnow_link")
                or not conn.last_newsnow_link
                or "url" not in conn.last_newsnow_link
            ):
                return ActionResponse(
                    Action.REQLLM,
                    "Chưa có tin nào được đọc trước đó. Hãy lấy tin mới trước.",
                    None,
                )

            url = conn.last_newsnow_link.get("url")
            title = conn.last_newsnow_link.get("title", "Không rõ")
            source_id = conn.last_newsnow_link.get("source_id", "vnexpress")

            if not url or url == "#":
                return ActionResponse(
                    Action.REQLLM, "Tin này không có link chi tiết.", None
                )

            logger.bind(tag=TAG).debug(
                f"Fetching news detail: {title}, URL={url}"
            )

            detail_content = fetch_news_detail(url)

            if not detail_content or detail_content == "Không thể lấy nội dung chi tiết":
                return ActionResponse(
                    Action.REQLLM,
                    f"Không thể lấy chi tiết tin «{title}». Link có thể đã hết hạn.",
                    None,
                )

            detail_report = (
                f"Dựa trên dữ liệu sau, dùng {lang} trả lời truy vấn chi tiết tin tức:\n\n"
                f"Tiêu đề: {title}\n"
                f"Nội dung: {detail_content}\n\n"
                f"(Hãy tóm tắt nội dung chính, kể lại tự nhiên như đang đọc tin cho người nghe.)"
            )

            return ActionResponse(Action.REQLLM, detail_report, None)

        news_sources_list = [
            name.strip() for name in news_sources.split(";") if name.strip()
        ]
        if source in news_sources_list:
            english_source_id = CHANNEL_MAP.get(source)
        else:
            english_source_id = CHANNEL_MAP.get(source)

        if not english_source_id:
            logger.bind(tag=TAG).warning(f"Invalid news source: {source}; falling back to vnexpress")
            english_source_id = "vnexpress"
            source = "VnExpress"

        logger.bind(tag=TAG).info(f"Fetching news: source={source} ({english_source_id})")

        news_items = fetch_news_from_api(conn, english_source_id)

        if not news_items:
            return ActionResponse(
                Action.REQLLM,
                f"Không lấy được tin từ {source}. Hãy thử lại sau hoặc chọn nguồn khác.",
                None,
            )

        selected_news = random.choice(news_items)

        if not hasattr(conn, "last_newsnow_link"):
            conn.last_newsnow_link = {}
        conn.last_newsnow_link = {
            "url": selected_news.get("url", "#"),
            "title": selected_news.get("title", "Không rõ"),
            "source_id": english_source_id,
        }

        news_report = (
            f"Dựa trên dữ liệu sau, dùng {lang} đọc tin cho người nghe:\n\n"
            f"Tiêu đề: {selected_news['title']}\n"
            f"(Đọc tiêu đề tự nhiên, gợi ý người dùng có thể yêu cầu xem chi tiết.)"
        )

        return ActionResponse(Action.REQLLM, news_report, None)

    except Exception as e:
        logger.bind(tag=TAG).error(f"News fetch error: {e}")
        return ActionResponse(
            Action.REQLLM, "Xin lỗi, có lỗi khi lấy tin tức. Hãy thử lại sau.", None
        )
