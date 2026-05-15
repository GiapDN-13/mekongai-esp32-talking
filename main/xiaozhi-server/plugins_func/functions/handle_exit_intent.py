from plugins_func.register import register_function, ToolType, ActionResponse, Action
from config.logger import setup_logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

handle_exit_intent_function_desc = {
    "type": "function",
    "function": {
        "name": "handle_exit_intent",
        "description": (
            "Khi người dùng muốn kết thúc cuộc trò chuyện, tạm biệt hoặc rời đi. "
            "Ví dụ: 'tạm biệt', 'bye', 'tôi đi nhé', 'thôi không hỏi nữa'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "say_goodbye": {
                    "type": "string",
                    "description": "Câu tạm biệt thân thiện bằng tiếng Việt",
                }
            },
            "required": ["say_goodbye"],
        },
    },
}


@register_function(
    "handle_exit_intent", handle_exit_intent_function_desc, ToolType.SYSTEM_CTL
)
def handle_exit_intent(conn: "ConnectionHandler", say_goodbye: str | None = None):
    try:
        if say_goodbye is None:
            say_goodbye = "Tạm biệt quý vị, hẹn gặp lại nha!"
        conn.close_after_chat = True
        logger.bind(tag=TAG).info(f"Exit intent handled: {say_goodbye}")
        return ActionResponse(
            action=Action.RESPONSE, result="exit", response=say_goodbye
        )
    except Exception as e:
        logger.bind(tag=TAG).error(f"Exit intent error: {e}")
        return ActionResponse(
            action=Action.NONE, result="exit_failed", response=""
        )
