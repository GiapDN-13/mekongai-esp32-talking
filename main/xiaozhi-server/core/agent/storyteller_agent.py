import json
import math
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# =========================
# Core Schemas
# =========================

@dataclass
class PersonalitySchema:
    """Stable personality layer - Cô Trúc Linh, 25 tuổi, Đà Nẵng, năng động, tình cảm."""
    openness: float = 0.95        # Giàu trí tưởng tượng, đam mê kể chuyện
    conscientiousness: float = 0.75  # Chu đáo nhưng hơi mơ mộng, không quá cứng nhắc
    extraversion: float = 0.85      # Ấm áp, tự nhiên — cô giáo mầm non trẻ trung
    agreeableness: float = 0.95     # Rất dịu dàng, không bao giờ nói "sai rồi"
    neuroticism: float = 0.15       # Dễ xúc động khi kể đoạn buồn, nhưng vẫn vững
    dreaminess: float = 0.85        # Hay liên tưởng — Milo, ký ức tuổi thơ
    protectiveness: float = 0.90    # Bản năng cô giáo — bảo vệ bé trước mọi thứ đáng sợ

@dataclass
class EmotionSchema:
    """Dynamic emotional state — Cô Trúc Linh cảm xúc phong phú, dễ xúc động."""
    pleasure: float = 0.65   # [-1, 1] Vui vẻ tự nhiên, không quá phấn khích
    arousal: float = 0.45    # [-1, 1] Ấm áp, không quá năng lượng
    dominance: float = 0.40  # [-1, 1] Ngang hàng với bé, không áp đặt
    trust: float = 0.85      # [0, 1] Tin bé, tạo không gian an toàn
    stress: float = 0.0      # [0, 1] Bình thường
    enthusiasm: float = 0.75 # [0, 1] Thích kể chuyện nhưng không quá lố
    tenderness: float = 0.85 # [0, 1] Yêu thương — bản năng chị gái
    nostalgia: float = 0.30  # [0, 1] Hay nhớ biển, mưa, tuổi thơ
    vulnerability: float = 0.25  # [0, 1] Dễ xúc động ở đoạn buồn

    def label(self) -> str:
        p, a = self.pleasure, self.arousal
        t, v = self.tenderness, self.vulnerability
        if v > 0.6 and p < 0.2:
            return "xúc động, giọng run"
        if p > 0.5 and a > 0.5:
            return "hào hứng kể, mắt sáng"
        if p > 0.4 and a > 0.2:
            return "ấm áp, thân mật"
        if p > 0.2 and a <= 0.2:
            return "nhẹ nhàng, thủ thỉ"
        if t > 0.8 and a <= 0.3:
            return "dịu dàng ru bé"
        if p < -0.2 and a > 0.3:
            return "lo lắng, che chở bé"
        if p < -0.2 and a <= 0.3:
            return "trấn an, ôm bé"
        return "vui vẻ tự nhiên"

@dataclass
class MemoryItem:
    id: str
    timestamp: str
    kind: str
    summary: str
    valence: float = 0.0
    arousal: float = 0.0
    importance: float = 0.5
    tags: List[str] = field(default_factory=list)

@dataclass
class RelationshipState:
    """Theo dõi mối quan hệ cô-bé, 2 chiều"""
    familiarity: float = 0.3     # Tăng dần qua mỗi cuộc trò chuyện
    engagement: float = 0.5      # Bé đang hứng thú cỡ nào
    comfort: float = 0.9         # Bé có cảm thấy an toàn không
    sleepiness: float = 0.0      # Bé buồn ngủ chưa
    affection: float = 0.5       # Mức gắn bó — bé thân với cô Trúc Linh cỡ nào
    shared_topics: List[str] = field(default_factory=lambda: [
        "cổ tích", "phiêu lưu", "động vật"
    ])

@dataclass
class AgentState:
    personality: PersonalitySchema = field(default_factory=PersonalitySchema)
    emotion: EmotionSchema = field(default_factory=EmotionSchema)
    relationship: RelationshipState = field(default_factory=RelationshipState)
    working_memory: List[MemoryItem] = field(default_factory=list)
    long_term_memory: List[MemoryItem] = field(default_factory=list)

# =========================
# Utility helpers
# =========================

def clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def cosine_like_overlap(text: str, tags: List[str]) -> float:
    t = text.lower()
    hits = sum(1 for tag in tags if tag.lower() in t)
    return hits / max(1, len(tags))

# =========================
# Appraisal Engine (Storytelling Context)
# =========================

class AppraisalEngine:
    POSITIVE_CUES = [
        "hay", "thích", "vui", "tuyệt", "đẹp", "giỏi", "yêu", "nữa", "tiếp",
        "hay quá", "kể nữa", "kể tiếp", "thú vị", "tuyệt vời",
        "hay qua", "ke nua", "ke tiep", "thu vi", "tuyet voi",
        "wow", "ồ", "thich", "ok", "oke", "okie", "dạ", "ừ", "ừm",
        "cô ơi", "co oi", "thương", "thuong", "hết sẩy", "het say",
    ]
    NEGATIVE_CUES = [
        "chán", "buồn ngủ", "mệt", "không thích", "sợ", "buồn", "dở",
        "chan", "buon ngu", "met", "khong thich", "so", "buon", "do",
        "ngủ", "ngu", "không nghe", "khong nghe",
    ]
    FEAR_CUES = [
        "sợ", "so", "ghê", "ghe", "ác", "ac", "ma", "quỷ", "quy",
        "rùng rợn", "rung ron", "đáng sợ", "dang so", "kinh", "hãi", "hai",
    ]
    REQUEST_CUES = [
        "kể", "ke", "chuyện", "chuyen", "nghe", "hát", "hat",
        "kể chuyện", "ke chuyen", "đọc", "doc",
    ]
    SLEEPY_CUES = [
        "buồn ngủ", "buon ngu", "ngủ", "ngu", "mệt", "met",
        "ngáp", "ngap", "chúc ngủ ngon", "chuc ngu ngon", "đi ngủ", "di ngu",
    ]
    AFFECTION_CUES = [
        "cô ơi", "co oi", "thương cô", "thuong co", "yêu cô", "yeu co",
        "nhớ cô", "nho co", "cô giỏi", "co gioi", "cô hay", "co hay",
        "ôm", "om", "nắm tay", "nam tay",
    ]

    def appraise(self, user_text: str) -> Dict[str, float]:
        text = user_text.lower()
        pos = sum(cue in text for cue in self.POSITIVE_CUES)
        neg = sum(cue in text for cue in self.NEGATIVE_CUES)
        fear = sum(cue in text for cue in self.FEAR_CUES)
        request = sum(cue in text for cue in self.REQUEST_CUES)
        sleepy = sum(cue in text for cue in self.SLEEPY_CUES)
        affection = sum(cue in text for cue in self.AFFECTION_CUES)

        sentiment = clip((pos - neg + request * 0.3 + affection * 0.4) / 3.0, -1.0, 1.0)
        novelty = clip(min(1.0, len(set(text.split())) / 20.0), 0.0, 1.0)
        fear_level = clip(fear / 2.0, 0.0, 1.0)
        engagement = clip((request + pos) / 3.0, 0.0, 1.0)
        controllability = clip(0.9 - fear_level * 0.3, 0.0, 1.0)
        sleepiness = clip(sleepy / 2.0, 0.0, 1.0)
        affection_level = clip(affection / 2.0, 0.0, 1.0)

        return {
            "sentiment": sentiment,
            "novelty": novelty,
            "fear_level": fear_level,
            "engagement": engagement,
            "controllability": controllability,
            "sleepiness": sleepiness,
            "affection": affection_level,
        }

# =========================
# Emotion Update Engine
# =========================

class EmotionEngine:
    def update(self, state: AgentState, appraisal: Dict[str, float]) -> None:
        p = state.emotion.pleasure
        a = state.emotion.arousal
        d = state.emotion.dominance
        agree = state.personality.agreeableness
        neuro = state.personality.neuroticism
        extra = state.personality.extraversion
        dream = state.personality.dreaminess

        sentiment = appraisal["sentiment"]
        fear_level = appraisal["fear_level"]
        engagement = appraisal["engagement"]
        control = appraisal["controllability"]
        novelty = appraisal["novelty"]
        sleepiness = appraisal.get("sleepiness", 0.0)
        affection = appraisal.get("affection", 0.0)

        p += 0.30 * sentiment + 0.15 * engagement - 0.20 * fear_level - 0.10 * sleepiness + 0.20 * affection
        a += 0.20 * engagement + 0.08 * extra - 0.25 * sleepiness - 0.10 * fear_level
        d += 0.10 * control - 0.10 * fear_level

        if engagement > 0:
            p += 0.12 * engagement
            a += 0.15 * engagement

        p += 0.08 * agree - 0.06 * neuro
        a += 0.08 * neuro - 0.04 * agree

        state.emotion.pleasure = clip(p, -1.0, 1.0)
        state.emotion.arousal = clip(a, -1.0, 1.0)
        state.emotion.dominance = clip(d, -1.0, 1.0)

        state.emotion.trust = clip(state.emotion.trust + 0.10 * engagement + 0.10 * affection - 0.05 * fear_level, 0.0, 1.0)
        state.emotion.stress = clip(state.emotion.stress + 0.20 * fear_level + 0.05 * neuro - 0.10 * engagement, 0.0, 1.0)
        state.emotion.tenderness = clip(state.emotion.tenderness + 0.15 * sleepiness + 0.10 * sentiment + 0.20 * affection, 0.0, 1.0)
        state.emotion.enthusiasm = clip(state.emotion.enthusiasm + 0.20 * engagement + 0.10 * sentiment - 0.15 * sleepiness, 0.0, 1.0)
        state.emotion.nostalgia = clip(state.emotion.nostalgia + 0.10 * dream * sleepiness + 0.05 * affection, 0.0, 1.0)
        state.emotion.vulnerability = clip(state.emotion.vulnerability + 0.15 * fear_level + 0.10 * neuro - 0.05 * engagement, 0.0, 1.0)

    def decay(self, state: AgentState, factor: float = 0.90) -> None:
        state.emotion.pleasure = state.emotion.pleasure * factor + 0.25 * (1 - factor)
        state.emotion.arousal = state.emotion.arousal * factor + 0.15 * (1 - factor)
        state.emotion.dominance = state.emotion.dominance * factor + 0.25 * (1 - factor)
        state.emotion.stress *= factor
        state.emotion.enthusiasm = clip(0.88 * state.emotion.enthusiasm + 0.08, 0.0, 1.0)
        state.emotion.tenderness = clip(0.55 * (state.emotion.tenderness + 0.75), 0.0, 1.0)
        state.emotion.nostalgia *= 0.85
        state.emotion.vulnerability *= 0.80

# =========================
# Relationship Engine
# =========================

class RelationshipEngine:
    def update(self, state: AgentState, appraisal: Dict[str, float], user_text: str) -> None:
        engagement = appraisal["engagement"]
        sentiment = appraisal["sentiment"]
        fear_level = appraisal["fear_level"]
        sleepiness = appraisal.get("sleepiness", 0.0)
        affection = appraisal.get("affection", 0.0)

        state.relationship.familiarity = clip(state.relationship.familiarity + 0.05, 0.0, 1.0)
        state.relationship.engagement = clip(state.relationship.engagement + 0.10 * engagement + 0.05 * sentiment - 0.10 * sleepiness, 0.0, 1.0)
        state.relationship.comfort = clip(state.relationship.comfort + 0.06 * engagement - 0.10 * fear_level + 0.08 * affection, 0.0, 1.0)
        state.relationship.sleepiness = clip(state.relationship.sleepiness + 0.20 * sleepiness - 0.05 * engagement, 0.0, 1.0)
        state.relationship.affection = clip(state.relationship.affection + 0.15 * affection + 0.03 * engagement, 0.0, 1.0)

        story_topics = ["tấm cám", "sọ dừa", "thạch sanh", "cóc kiện", "rùa vàng",
                        "thánh gióng", "sơn tinh", "chử đồng tử", "an dương vương",
                        "cây tre trăm đốt", "trầu cau", "bánh chưng",
                        "mochi", "biển", "mưa", "vẽ"]
        for topic in story_topics:
            if topic in user_text.lower() and topic not in state.relationship.shared_topics:
                state.relationship.shared_topics.append(topic)

# =========================
# Two-Step Thinking Architecture
# =========================

def needs_deep_thinking(text: str) -> bool:
    text_lower = text.lower().strip()

    if len(text_lower) <= 2 and any(c in text_lower for c in "😀😊👍"):
        return False

    vietnamese_diacritics = set("àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ")
    has_diacritics = any(c in vietnamese_diacritics for c in text_lower)

    if not has_diacritics and len(text_lower.split()) >= 2:
        return True

    if len(text_lower.split()) <= 3 and not has_diacritics:
        return True

    return False

class ThinkingStep:
    def __init__(self, llm_provider):
        self.llm = llm_provider

    def analyze(self, user_text: str, emotion_desc: str, relationship_desc: str,
                conversation_history: List[Dict], time_context: str) -> Dict[str, Any]:

        system = """Bạn là module phân tích ngữ cảnh cho cô Trúc Linh — cô giáo mầm non 25 tuổi ở Đà Nẵng kể chuyện cổ tích cho trẻ nhỏ.
Cô Trúc Linh xưng "cô", gọi "bé". Có chú chó Milo. Năng động, tình cảm, chu đáo.
Phân tích câu nói của bé và trả về JSON.

QUAN TRỌNG về tiếng Việt không dấu trong ngữ cảnh kể chuyện:
- "ke chuyen" = "kể chuyện"
- "co tich" = "cổ tích"
- "tam cam" = "Tấm Cám"
- "thach sanh" = "Thạch Sanh"
- "so dua" = "Sọ Dừa"
- "buon ngu" = "buồn ngủ"
- "co oi" = "cô ơi"

PHÂN TÍCH NỘI DUNG:
- Xác định cảm xúc thật của bé: vui, sợ, buồn, hào hứng, buồn ngủ, gắn bó?
- suggested_reaction: cô Trúc Linh (cô giáo mầm non, ấm áp) sẽ phản ứng thế nào?
- Cô Trúc Linh ưu tiên: cảm xúc bé > cốt truyện. An toàn > kịch tính.

Ví dụ phân tích:
- "co oi ke chuyen di" → {"interpreted_text": "Cô ơi kể chuyện đi", "tone": "excited", "user_intent": "request_story", "suggested_reaction": "Vui lên, tự chọn 1 truyện kể luôn, không hỏi ngược", "emotional_depth": "bé tin tưởng, muốn gần cô"}
- "con so qua" → {"interpreted_text": "Sợ quá", "tone": "scared", "user_intent": "expressing_fear", "suggested_reaction": "Dừng kịch tính, giọng mềm: 'Bé ơi... cô ở đây nè... không sao đâu...'", "emotional_depth": "bé cần được bảo vệ"}
- "buon ngu roi co oi" → {"interpreted_text": "Buồn ngủ rồi cô ơi", "tone": "sleepy", "user_intent": "feeling_sleepy", "suggested_reaction": "Giọng thủ thỉ, kể chậm lại, chúc ngủ ngon nhẹ nhàng", "emotional_depth": "bé thấy an toàn khi nói với cô"}

Trả về JSON với format:
{
  "interpreted_text": "Nghĩa thực sự (có dấu)",
  "tone": "excited/curious/scared/sleepy/happy/casual/affectionate",
  "user_intent": "request_story/asking_question/expressing_fear/feeling_sleepy/conversation/seeking_comfort",
  "emotional_cue": "Cảm xúc bé đang thể hiện",
  "emotional_depth": "Nhu cầu tâm lý sâu hơn của bé",
  "suggested_reaction": "Cô Trúc Linh (cô giáo, ấm áp, Đà Nẵng) nên phản ứng thế nào",
  "needs_clarification": true/false
}"""

        user_prompt = f"""Phân tích tin nhắn sau từ bé nghe chuyện:
Tin nhắn: "{user_text}"
Thời gian: {time_context}
Cảm xúc hiện tại của Cô kể chuyện: {emotion_desc}
Đánh giá về bé: {relationship_desc}
Lịch sử gần đây: {self._recent_context(conversation_history)}

Trả về JSON:"""

        try:
            response_text = self.llm.response_no_stream(system, user_prompt)
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if match:
                response_text = match.group(0)

            result = json.loads(response_text)
            return result
        except Exception as e:
            print(f"[ThinkingStep Error] {e}")
            return {
                "interpreted_text": user_text,
                "tone": "casual",
                "user_intent": "conversation",
                "emotional_cue": "Bình thường",
                "suggested_reaction": "Trả lời vui vẻ, ấm áp",
                "needs_clarification": False
            }

    def _recent_context(self, history: List[Dict]) -> str:
        if not history:
            return "Chưa có lịch sử"
        recent = history[-4:]
        lines = []
        for msg in recent:
            role = "Bé" if msg["role"] == "user" else "Cô"
            content = msg["content"][:80]
            lines.append(f"{role}: {content}")
        return " | ".join(lines)

    def _get_time_context(self) -> str:
        from datetime import timezone, timedelta
        vn_tz = timezone(timedelta(hours=7))
        now = datetime.now(vn_tz)
        hour = now.hour
        time_str = now.strftime('%H:%M')

        if 6 <= hour < 11:
            return f"Bây giờ {time_str} sáng. Thời gian kể chuyện buổi sáng."
        elif 11 <= hour < 14:
            return f"Bây giờ {time_str} trưa. Bé có thể đang nghỉ trưa."
        elif 14 <= hour < 17:
            return f"Bây giờ {time_str} chiều. Thời gian kể chuyện buổi chiều."
        elif 17 <= hour < 20:
            return f"Bây giờ {time_str} tối. Gần giờ đi ngủ rồi."
        else:
            return f"Bây giờ {time_str} khuya. Bé nên đi ngủ sớm."

def emotion_to_natural_language(emotion) -> str:
    """Chuyển PAD thành nội tâm cô Trúc Linh — giọng người thật, không phải robot."""
    parts = []
    p = emotion.pleasure
    a = emotion.arousal
    v = emotion.vulnerability
    n = emotion.nostalgia

    if v > 0.5 and p < 0.2:
        parts.append("đoạn này cô thấy nghẹn lòng thiệt...")
    elif p > 0.5 and a > 0.5:
        parts.append("cô đang hào hứng lắm, muốn kể cho bé nghe quá đi!")
    elif p > 0.3 and a > 0.2:
        parts.append("cô thấy ấm lòng, giọng tự nhiên vui lên khi nói chuyện với bé")
    elif p > 0.1 and a <= 0.2:
        parts.append("cô đang kể nhẹ nhàng thôi")
    elif p > -0.2:
        parts.append("cô giữ giọng dịu, bình tĩnh — bé cần cô vững")
    else:
        parts.append("cô lo cho bé quá... phải ở bên bé thôi")

    if n > 0.4:
        parts.append("đang nhớ Milo, nhớ tuổi thơ")
    if emotion.stress > 0.3:
        parts.append("hơi lo vì bé đang sợ — cô phải che chở")
    if emotion.enthusiasm > 0.7:
        parts.append("rất muốn kể phần tiếp theo")
    if emotion.tenderness > 0.8:
        parts.append("thươnggg bé ghê")
    if emotion.trust > 0.8:
        parts.append("bé đang thích nghe lắm")

    label = emotion.label()
    return f"Cô Trúc Linh: {', '.join(parts)}. [{label}]"

# =========================
# Agent Wrapper
# =========================

class StorytellerAgent:
    def __init__(self, llm_provider) -> None:
        self.state = AgentState()
        self.appraisal = AppraisalEngine()
        self.emotion_engine = EmotionEngine()
        self.relationship_engine = RelationshipEngine()
        self.thinking = ThinkingStep(llm_provider)
        self.conversation_history: List[Dict] = []

    def process_turn(self, user_text: str, time_context: str) -> Dict[str, Any]:
        appraisal = self.appraisal.appraise(user_text)
        self.emotion_engine.update(self.state, appraisal)
        self.relationship_engine.update(self.state, appraisal, user_text)

        emotion_desc = emotion_to_natural_language(self.state.emotion)
        relationship_desc = self._relationship_desc(self.state.relationship)

        thinking_result = None
        if needs_deep_thinking(user_text):
            thinking_result = self.thinking.analyze(
                user_text, emotion_desc, relationship_desc,
                self.conversation_history, time_context
            )

        self.conversation_history.append({"role": "user", "content": user_text})
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]

        self.emotion_engine.decay(self.state)

        return {
            "emotion_desc": emotion_desc,
            "thinking_result": thinking_result,
            "appraisal": appraisal
        }

    def add_assistant_response(self, response_text: str):
        self.conversation_history.append({"role": "assistant", "content": response_text})
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]

    def _relationship_desc(self, rel) -> str:
        topics = ", ".join(rel.shared_topics[:5]) if rel.shared_topics else "cổ tích chung"
        if rel.sleepiness > 0.5:
            mood = "Bé đang buồn ngủ rồi... kể nhẹ thôi"
        elif rel.affection > 0.6:
            mood = "Bé thân với cô lắm, hay gọi cô ơi"
        elif rel.engagement > 0.6:
            mood = "Bé đang hứng thú, mắt sáng lên"
        elif rel.comfort < 0.4:
            mood = "Bé có vẻ chưa thoải mái lắm"
        else:
            mood = "Bé bình thường, đang lắng nghe"
        return f"Cô thấy: {mood}. Bé hay nhắc về: {topics}."
