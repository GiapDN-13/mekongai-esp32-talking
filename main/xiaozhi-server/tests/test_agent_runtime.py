"""Tests for the Agent Runtime pipeline.

Covers: events, actions, state, interpreter, memory, skills, policy.
Mocks opuslib_next since native Opus may not be available in CI.
"""

import sys
import time
from unittest.mock import MagicMock

sys.modules.setdefault("opuslib_next", MagicMock())
sys.modules.setdefault("config.logger", MagicMock(setup_logging=MagicMock(return_value=MagicMock())))

from core.agent.runtime.events import EventType, Event, AudioFeatures
from core.agent.runtime.actions import ActionType, Action
from core.agent.runtime.state import ConversationState, StateManager
from core.agent.runtime.interpreter import AudioInterpreter
from core.agent.runtime.perception import AudioPercept
from core.agent.runtime.policy import PolicyResolver
from core.agent.memory.working import WorkingMemory
from core.agent.memory.episodic import EpisodicMemory
from core.agent.skills.turn_taking import TurnTakingSkill
from core.agent.skills.interrupt import InterruptSkill


# ═══════════════════════════════════════════════════════════════════════
# Scenario 1: User nói bình thường → im → bot nhận diện kết thúc
# ═══════════════════════════════════════════════════════════════════════

class TestScenarioNormalSpeech:
    """User speaks for 2s, then silence 1000ms → MARK_UTTERANCE_COMPLETE."""

    def test_voice_start_transition(self):
        interpreter = AudioInterpreter()
        state = ConversationState(voice_active=False)
        percept = AudioPercept(
            timestamp_ms=1000.0, vad_result=True, rms_energy=2000, frame_class="human"
        )
        event = interpreter.interpret(percept, state)
        assert event.type == EventType.VOICE_STARTED

    def test_voice_continuing(self):
        interpreter = AudioInterpreter()
        state = ConversationState(voice_active=True, voice_start_ms=1000.0)
        percept = AudioPercept(
            timestamp_ms=1500.0, vad_result=True, rms_energy=1800, frame_class="human"
        )
        event = interpreter.interpret(percept, state)
        assert event.type == EventType.VOICE_CONTINUING
        assert event.speech_ms == 500.0

    def test_voice_stop_transition(self):
        interpreter = AudioInterpreter()
        state = ConversationState(voice_active=True, voice_start_ms=1000.0)
        percept = AudioPercept(timestamp_ms=3000.0, vad_result=False, rms_energy=0)
        event = interpreter.interpret(percept, state)
        assert event.type == EventType.VOICE_STOPPED
        assert event.speech_ms == 2000.0

    def test_silence_continuing_reports_duration(self):
        interpreter = AudioInterpreter()
        state = ConversationState(voice_active=False, last_voice_end_ms=3000.0)
        percept = AudioPercept(timestamp_ms=4000.0, vad_result=False, rms_energy=0)
        event = interpreter.interpret(percept, state)
        assert event.type == EventType.SILENCE_CONTINUING
        assert event.silence_ms == 1000.0

    def test_turn_taking_triggers_at_threshold(self):
        skill = TurnTakingSkill()
        episodic = EpisodicMemory()
        state = ConversationState(
            voice_active=False, last_voice_end_ms=3000.0, bot_is_speaking=False
        )
        event = Event(
            type=EventType.SILENCE_CONTINUING,
            timestamp_ms=4000.0,
            silence_ms=1000.0,
        )
        assert skill.should_activate(state, event) is True
        action = skill.propose(state, event, episodic)
        assert action is not None
        assert action.type == ActionType.MARK_UTTERANCE_COMPLETE

    def test_turn_taking_does_not_trigger_below_threshold(self):
        skill = TurnTakingSkill()
        episodic = EpisodicMemory()
        state = ConversationState(
            voice_active=False, last_voice_end_ms=3000.0, bot_is_speaking=False
        )
        event = Event(
            type=EventType.SILENCE_CONTINUING,
            timestamp_ms=3400.0,
            silence_ms=400.0,
        )
        action = skill.propose(state, event, episodic)
        assert action is None


# ═══════════════════════════════════════════════════════════════════════
# Scenario 2: User nghỉ giữa câu (mid-utterance pause) → bot chờ
# ═══════════════════════════════════════════════════════════════════════

class TestScenarioMidUtterancePause:
    """User pauses 400ms mid-sentence → bot waits, no action."""

    def test_short_pause_no_action(self):
        skill = TurnTakingSkill()
        episodic = EpisodicMemory()
        state = ConversationState(
            voice_active=False, last_voice_end_ms=5000.0, bot_is_speaking=False
        )
        event = Event(
            type=EventType.SILENCE_CONTINUING,
            timestamp_ms=5400.0,
            silence_ms=400.0,
        )
        action = skill.propose(state, event, episodic)
        assert action is None


# ═══════════════════════════════════════════════════════════════════════
# Scenario 3: Adaptive threshold học từ user
# ═══════════════════════════════════════════════════════════════════════

class TestScenarioAdaptiveThreshold:
    """After several turns, threshold adapts to user's pause pattern."""

    def test_default_threshold(self):
        episodic = EpisodicMemory()
        assert episodic.get_adaptive_silence_threshold() == 1000.0

    def test_threshold_adapts_with_data(self):
        episodic = EpisodicMemory()
        # User has short pauses: 300, 350, 400, 380, 320
        for p in [300, 350, 400, 380, 320]:
            episodic.record_mid_pause(p)

        threshold = episodic.get_adaptive_silence_threshold()
        # p75 ~ 380-400 + 200ms buffer → ~580-600ms
        assert threshold < 1000.0
        assert threshold >= 500.0

    def test_threshold_respects_max(self):
        episodic = EpisodicMemory()
        for p in [1500, 1600, 1700, 1800, 1900]:
            episodic.record_mid_pause(p)
        threshold = episodic.get_adaptive_silence_threshold()
        assert threshold <= 2000.0


# ═══════════════════════════════════════════════════════════════════════
# Scenario 4: Echo trong lúc TTS → bot ignore
# ═══════════════════════════════════════════════════════════════════════

class TestScenarioEchoDuringTTS:
    """TTS is playing, mic picks up echo → DISCARD_AUDIO."""

    def test_echo_frames_classified(self):
        interpreter = AudioInterpreter()
        state = ConversationState(bot_is_speaking=True, consecutive_echo_frames=3)
        percept = AudioPercept(
            timestamp_ms=1000.0,
            vad_result=True,
            rms_energy=500,
            spectral_flatness=0.03,
            frame_class="echo",
        )
        event = interpreter.interpret(percept, state)
        assert event.type == EventType.TTS_ECHO_FRAME
        assert event.consecutive_echo_frames == 4

    def test_interrupt_skill_discards_echo(self):
        skill = InterruptSkill()
        state = ConversationState(bot_is_speaking=True, consecutive_echo_frames=5)
        event = Event(
            type=EventType.TTS_ECHO_FRAME,
            timestamp_ms=1000.0,
            consecutive_echo_frames=5,
        )
        assert skill.should_activate(state, event) is True
        action = skill.propose(state, event, EpisodicMemory())
        assert action is not None
        assert action.type == ActionType.DISCARD_AUDIO


# ═══════════════════════════════════════════════════════════════════════
# Scenario 5: User chen ngang (barge-in) → STOP_TTS_AND_LISTEN
# ═══════════════════════════════════════════════════════════════════════

class TestScenarioBargeIn:
    """User speaks over TTS with strong human signal → stop TTS."""

    def test_human_frames_classified(self):
        interpreter = AudioInterpreter()
        state = ConversationState(bot_is_speaking=True, consecutive_human_frames=2)
        percept = AudioPercept(
            timestamp_ms=1000.0,
            vad_result=True,
            rms_energy=3000,
            spectral_flatness=0.25,
            frame_class="human",
        )
        event = interpreter.interpret(percept, state)
        assert event.type == EventType.TTS_HUMAN_FRAME
        assert event.consecutive_human_frames == 3

    def test_interrupt_skill_triggers_barge_in(self):
        skill = InterruptSkill()
        state = ConversationState(bot_is_speaking=True, consecutive_human_frames=2)
        event = Event(
            type=EventType.TTS_HUMAN_FRAME,
            timestamp_ms=1000.0,
            consecutive_human_frames=2,
        )
        action = skill.propose(state, event, EpisodicMemory())
        assert action is not None
        assert action.type == ActionType.STOP_TTS_AND_LISTEN

    def test_interrupt_below_threshold_no_action(self):
        skill = InterruptSkill()
        state = ConversationState(bot_is_speaking=True, consecutive_human_frames=1)
        event = Event(
            type=EventType.TTS_HUMAN_FRAME,
            timestamp_ms=1000.0,
            consecutive_human_frames=1,
        )
        action = skill.propose(state, event, EpisodicMemory())
        assert action is None

    def test_ambiguous_frames_do_not_trigger_barge_in(self):
        """Ambiguous frames are likely echo — they should NOT trigger barge-in."""
        skill = InterruptSkill()
        state = ConversationState(bot_is_speaking=True, consecutive_human_frames=0)
        event = Event(
            type=EventType.TTS_AMBIGUOUS_FRAME,
            timestamp_ms=1000.0,
        )
        action = skill.propose(state, event, EpisodicMemory())
        assert action is None

    def test_cooldown_blocks_rapid_retrigger(self):
        """After barge-in triggers, cooldown prevents immediate re-trigger."""
        skill = InterruptSkill()
        state = ConversationState(bot_is_speaking=True, consecutive_human_frames=3)
        event = Event(
            type=EventType.TTS_HUMAN_FRAME,
            timestamp_ms=1000.0,
            consecutive_human_frames=3,
        )
        # First trigger succeeds
        action = skill.propose(state, event, EpisodicMemory())
        assert action is not None
        assert action.type == ActionType.STOP_TTS_AND_LISTEN

        # Immediately after, cooldown blocks
        assert skill.should_activate(state, event) is False


# ═══════════════════════════════════════════════════════════════════════
# Scenario 6: Policy conflict resolution
# ═══════════════════════════════════════════════════════════════════════

class TestScenarioPolicyConflict:
    """Two skills propose → higher priority*confidence wins."""

    def test_interrupt_wins_over_turn_taking(self):
        policy = PolicyResolver()
        proposals = [
            Action(
                type=ActionType.MARK_UTTERANCE_COMPLETE,
                confidence=0.8,
                skill_name="turn_taking",
                urgency=0.5,
            ),
            Action(
                type=ActionType.STOP_TTS_AND_LISTEN,
                confidence=0.9,
                skill_name="interrupt",
                urgency=0.9,
            ),
        ]
        winner = policy.resolve(proposals)
        assert winner.type == ActionType.STOP_TTS_AND_LISTEN

    def test_single_proposal_passes_through(self):
        policy = PolicyResolver()
        proposals = [
            Action(type=ActionType.MARK_UTTERANCE_COMPLETE, confidence=0.7, urgency=0.5)
        ]
        winner = policy.resolve(proposals)
        assert winner.type == ActionType.MARK_UTTERANCE_COMPLETE

    def test_empty_proposals_returns_none(self):
        policy = PolicyResolver()
        assert policy.resolve([]) is None

    def test_no_op_filtered(self):
        policy = PolicyResolver()
        proposals = [Action(type=ActionType.NO_OP, confidence=1.0, urgency=1.0)]
        assert policy.resolve(proposals) is None


# ═══════════════════════════════════════════════════════════════════════
# Scenario 7: State manager transitions
# ═══════════════════════════════════════════════════════════════════════

class TestScenarioStateManager:
    """State updates correctly from events."""

    def test_voice_started_updates_state(self):
        sm = StateManager()
        event = Event(type=EventType.VOICE_STARTED, timestamp_ms=1000.0)
        sm.update(event)
        assert sm.current.voice_active is True
        assert sm.current.voice_start_ms == 1000.0
        assert sm.current.silence_ms == 0.0

    def test_voice_stopped_updates_state(self):
        sm = StateManager()
        sm.current.voice_active = True
        sm.current.voice_start_ms = 1000.0
        event = Event(type=EventType.VOICE_STOPPED, timestamp_ms=3000.0, speech_ms=2000.0)
        sm.update(event)
        assert sm.current.voice_active is False
        assert sm.current.last_voice_end_ms == 3000.0
        assert sm.current.current_speech_ms == 2000.0

    def test_silence_accumulates(self):
        sm = StateManager()
        sm.current.voice_active = False
        event = Event(type=EventType.SILENCE_CONTINUING, timestamp_ms=4000.0, silence_ms=1200.0)
        sm.update(event)
        assert sm.current.silence_ms == 1200.0

    def test_tts_human_frame_accumulates(self):
        sm = StateManager()
        event = Event(
            type=EventType.TTS_HUMAN_FRAME,
            timestamp_ms=1000.0,
            consecutive_human_frames=3,
        )
        sm.update(event)
        assert sm.current.consecutive_human_frames == 3
        assert sm.current.consecutive_echo_frames == 0

    def test_sync_from_conn(self):
        sm = StateManager()
        conn = MagicMock()
        conn.client_is_speaking = True
        conn.client_have_voice = True
        sm.sync_from_conn(conn)
        assert sm.current.bot_is_speaking is True
        assert sm.current.voice_active is True

    def test_sync_to_conn(self):
        # sync_to_conn is intentionally a no-op: VAD provider owns conn state
        sm = StateManager()
        sm.current.voice_active = True
        conn = MagicMock(spec=[])
        sm.sync_to_conn(conn)
        assert not hasattr(conn, "client_have_voice")


# ═══════════════════════════════════════════════════════════════════════
# Scenario 8: Working memory pre-roll buffer
# ═══════════════════════════════════════════════════════════════════════

class TestScenarioWorkingMemory:
    """Pre-roll buffer maintains last N frames."""

    def test_pre_roll_fills(self):
        wm = WorkingMemory(pre_roll_size=3)
        wm.push_frame(b"frame1")
        wm.push_frame(b"frame2")
        wm.push_frame(b"frame3")
        wm.push_frame(b"frame4")
        pre_roll = wm.get_pre_roll()
        assert len(pre_roll) == 3
        assert pre_roll == [b"frame2", b"frame3", b"frame4"]

    def test_collecting_includes_pre_roll(self):
        wm = WorkingMemory(pre_roll_size=2)
        wm.push_frame(b"a")
        wm.push_frame(b"b")
        wm.start_collecting()
        wm.push_frame(b"c")
        wm.push_frame(b"d")
        frames = wm.stop_collecting()
        assert frames == [b"a", b"b", b"c", b"d"]

    def test_discard_clears(self):
        wm = WorkingMemory()
        wm.start_collecting()
        wm.push_frame(b"x")
        wm.discard()
        assert wm.is_collecting is False


# ═══════════════════════════════════════════════════════════════════════
# Scenario 9: Full pipeline flow (no real audio)
# ═══════════════════════════════════════════════════════════════════════

class TestScenarioFullPipeline:
    """Simulate frames through interpreter → state → skill → policy."""

    def test_end_to_end_utterance_complete(self):
        """Simulate: voice starts, continues, stops, silence grows → MARK_UTTERANCE_COMPLETE."""
        interpreter = AudioInterpreter()
        sm = StateManager()
        skill = TurnTakingSkill()
        policy = PolicyResolver()
        episodic = EpisodicMemory()

        now = 10000.0

        # Frame 1: Voice starts
        percept = AudioPercept(timestamp_ms=now, vad_result=True, rms_energy=2000, frame_class="human")
        event = interpreter.interpret(percept, sm.current)
        assert event.type == EventType.VOICE_STARTED
        sm.update(event)

        # Frames 2-30: Voice continues (2s)
        for i in range(30):
            now += 60
            percept = AudioPercept(timestamp_ms=now, vad_result=True, rms_energy=1800, frame_class="human")
            event = interpreter.interpret(percept, sm.current)
            assert event.type == EventType.VOICE_CONTINUING
            sm.update(event)

        # Frame 31: Voice stops
        now += 60
        percept = AudioPercept(timestamp_ms=now, vad_result=False, rms_energy=0)
        event = interpreter.interpret(percept, sm.current)
        assert event.type == EventType.VOICE_STOPPED
        sm.update(event)

        # Frames 32-48: Silence grows (1020ms)
        action_result = None
        for i in range(17):
            now += 60
            percept = AudioPercept(timestamp_ms=now, vad_result=False, rms_energy=0)
            event = interpreter.interpret(percept, sm.current)
            assert event.type == EventType.SILENCE_CONTINUING
            sm.update(event)

            if skill.should_activate(sm.current, event):
                proposal = skill.propose(sm.current, event, episodic)
                if proposal:
                    proposal.urgency = 0.5
                    action_result = policy.resolve([proposal])

        assert action_result is not None
        assert action_result.type == ActionType.MARK_UTTERANCE_COMPLETE
