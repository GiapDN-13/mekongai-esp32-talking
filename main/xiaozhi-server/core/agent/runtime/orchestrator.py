"""Main orchestrator: wires perception -> interpreter -> state -> skills -> policy -> executor.

Processes one audio frame per call. Includes FrameTrace for latency tracking.
"""

import time
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

from .perception import AudioPerception
from .interpreter import AudioInterpreter
from .state import StateManager
from .policy import PolicyResolver
from .executor import ActionExecutor
from .actions import Action, ActionType
from .events import Event
from ..skills.base import Skill
from ..skills.turn_taking import TurnTakingSkill
from ..skills.interrupt import InterruptSkill
from ..memory.working import WorkingMemory
from ..memory.episodic import EpisodicMemory
from config.logger import setup_logging

if TYPE_CHECKING:
    from core.connection import ConnectionHandler
    from core.providers.vad.base import VADProviderBase

TAG = __name__
logger = setup_logging()

SLOW_FRAME_THRESHOLD_MS = 10.0


@dataclass
class FrameTrace:
    """Per-frame latency trace. All times in ms."""

    frame_start_ms: float = 0.0
    perception_ms: float = 0.0
    interpret_ms: float = 0.0
    state_ms: float = 0.0
    skills_ms: float = 0.0
    policy_ms: float = 0.0
    executor_ms: float = 0.0
    total_ms: float = 0.0
    action_taken: str = "NO_OP"
    is_slow: bool = False


class AgentOrchestrator:
    """One instance per connection. Owns the full agent pipeline."""

    def __init__(self, vad_provider: "VADProviderBase"):
        self.perception = AudioPerception(vad_provider)
        self.interpreter = AudioInterpreter()
        self.state_manager = StateManager()
        self.policy = PolicyResolver()
        self.executor = ActionExecutor()
        self.working_memory = WorkingMemory()
        self.episodic = EpisodicMemory()

        self.skills: List[Skill] = [
            TurnTakingSkill(),
            InterruptSkill(),
        ]

        self._last_trace: Optional[FrameTrace] = None
        self._slow_frame_count: int = 0
        self._total_frame_count: int = 0

    async def process_frame(self, conn: "ConnectionHandler", opus_packet: bytes):
        """Process a single audio frame through the full pipeline."""
        trace = FrameTrace()
        trace.frame_start_ms = time.time() * 1000

        # Sync state from connection (before-swap strategy)
        self.state_manager.sync_from_conn(conn)

        # 1. Perception (stateless signal extraction)
        t0 = time.time() * 1000
        percept = self.perception.analyze(conn, opus_packet)
        trace.perception_ms = time.time() * 1000 - t0

        # 2. Interpretation (emit observation event)
        t0 = time.time() * 1000
        event = self.interpreter.interpret(percept, self.state_manager.current)
        trace.interpret_ms = time.time() * 1000 - t0

        # 3. State update
        t0 = time.time() * 1000
        self.state_manager.update(event)
        trace.state_ms = time.time() * 1000 - t0

        # 4. Working memory
        self.working_memory.push_frame(opus_packet)

        # 5. Skills (propose actions)
        t0 = time.time() * 1000
        proposals = self._gather_proposals(event)
        trace.skills_ms = time.time() * 1000 - t0

        # 6. Policy (resolve single action)
        t0 = time.time() * 1000
        action = self.policy.resolve(proposals)
        trace.policy_ms = time.time() * 1000 - t0

        # 7. Execute
        t0 = time.time() * 1000
        if action:
            if action.type == ActionType.STOP_TTS_AND_LISTEN:
                action.pre_roll_audio = self.working_memory.get_pre_roll()
            await self.executor.execute(action, conn)
            trace.action_taken = action.type.name

            # Track turns in episodic memory
            if action.type == ActionType.MARK_UTTERANCE_COMPLETE:
                self._record_turn_end(event)
        trace.executor_ms = time.time() * 1000 - t0

        # Sync state back to connection (after-swap strategy)
        self.state_manager.sync_to_conn(conn)

        # Finalize trace
        trace.total_ms = time.time() * 1000 - trace.frame_start_ms
        trace.is_slow = trace.total_ms > SLOW_FRAME_THRESHOLD_MS
        self._last_trace = trace
        self._total_frame_count += 1
        if trace.is_slow:
            self._slow_frame_count += 1
            logger.bind(tag=TAG).warning(
                f"[SLOW_FRAME] {trace.total_ms:.1f}ms "
                f"(perc={trace.perception_ms:.1f} interp={trace.interpret_ms:.1f} "
                f"skills={trace.skills_ms:.1f} exec={trace.executor_ms:.1f}) "
                f"action={trace.action_taken}"
            )

    def _gather_proposals(self, event: Event) -> List[Action]:
        proposals = []
        state = self.state_manager.current
        for skill in self.skills:
            if skill.should_activate(state, event):
                proposal = skill.propose(state, event, self.episodic)
                if proposal:
                    proposal.urgency = skill.priority / 100.0
                    proposals.append(proposal)
        return proposals

    def _record_turn_end(self, event: Event):
        """Record completed turn in episodic memory."""
        state = self.state_manager.current
        self.episodic.record_turn(
            speech_ms=state.current_speech_ms,
            pause_before_ms=state.silence_ms,
        )

    def cleanup(self):
        """Release resources."""
        self.perception.cleanup_conn(None)

    @property
    def stats(self) -> dict:
        return {
            "total_frames": self._total_frame_count,
            "slow_frames": self._slow_frame_count,
            "slow_pct": (
                f"{self._slow_frame_count / self._total_frame_count * 100:.1f}%"
                if self._total_frame_count > 0
                else "0%"
            ),
            "episodic_turns": self.episodic.turn_count,
            "adaptive_threshold_ms": self.episodic.get_adaptive_silence_threshold(),
        }
