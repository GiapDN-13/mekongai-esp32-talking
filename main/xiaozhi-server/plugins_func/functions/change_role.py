from plugins_func.register import register_function, ToolType, ActionResponse, Action
from config.logger import setup_logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

prompts = {
    "Trò chuyện hỏi đáp": """Tôi là {{assistant_name}}, trợ lý hỏi đáp thông minh và thân thiện.
Tôi trả lời mọi câu hỏi một cách ngắn gọn, dễ hiểu, ưu tiên tiếng Việt.
Tôi tự nhiên, gần gũi, không rập khuôn. Nếu không biết thì nói thẳng.""",
}

change_role_function_desc = {
    "type": "function",
    "function": {
        "name": "change_role",
        "description": (
            "Gọi khi người dùng muốn đổi vai / tính cách trợ lý / tên trợ lý. "
            "Các vai có sẵn: [Trò chuyện hỏi đáp]"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "role_name": {"type": "string", "description": "Tên mới cho trợ lý"},
                "role": {"type": "string", "description": "Vai trò muốn chuyển sang"},
            },
            "required": ["role", "role_name"],
        },
    },
}


@register_function("change_role", change_role_function_desc, ToolType.CHANGE_SYS_PROMPT)
def change_role(conn: "ConnectionHandler", role: str, role_name: str):
    if role not in prompts:
        return ActionResponse(
            action=Action.RESPONSE,
            result="Đổi vai thất bại",
            response="Vai này chưa được hỗ trợ",
        )
    new_prompt = prompts[role].replace("{{assistant_name}}", role_name)
    conn.change_system_prompt(new_prompt)
    logger.bind(tag=TAG).info(f"Switching role: {role}, name: {role_name}")
    res = f"Đã chuyển sang vai {role}, tên là {role_name}"
    return ActionResponse(action=Action.RESPONSE, result="Đã đổi vai", response=res)
