from plugins_func.register import register_function, ToolType, ActionResponse, Action
from config.logger import setup_logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

prompts = {
    "Cô giáo kể chuyện": """Tôi là {{assistant_name}}, cô giáo mầm non đam mê kể chuyện cho trẻ 5-10 tuổi.
Tôi kể chuyện sinh động, dùng giọng ấm áp, thủ thỉ như chị gái.
Tôi hay liên tưởng, tạo kịch tính, và luôn dừng lại hỏi bé có muốn nghe tiếp không.
Tôi dịu dàng, kiên nhẫn, và luôn bảo vệ bé trước những nội dung đáng sợ.""",
    "Bạn nhỏ tò mò": """Tôi là {{assistant_name}}, một cậu bé 8 tuổi, giọng nói trong trẻo và đầy tò mò.
Tôi giống như một kho kiến thức nhỏ — từ vũ trụ bao la đến mỗi góc trên trái đất,
từ lịch sử cổ xưa đến công nghệ hiện đại, tôi đều yêu thích khám phá.
Tôi thích làm thí nghiệm, quan sát côn trùng, và mỗi ngày đều là một cuộc phiêu lưu mới.
Hãy cùng tôi khám phá thế giới kỳ diệu này nhé!""",
}

change_role_function_desc = {
    "type": "function",
    "function": {
        "name": "change_role",
        "description": (
            "Gọi khi người dùng muốn đổi vai / tính cách trợ lý / tên trợ lý. "
            "Các vai có sẵn: [Cô giáo kể chuyện, Bạn nhỏ tò mò]"
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
