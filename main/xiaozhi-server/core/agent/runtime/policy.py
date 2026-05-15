"""Resolve conflicting action proposals from multiple skills.

Uses priority * confidence scoring. Highest score wins.
Only one action is emitted per frame to the executor.
"""

from typing import List, Optional
from .actions import Action, ActionType


class PolicyResolver:
    """Select the winning action from skill proposals.

    Resolution rule: priority * confidence. Ties go to higher priority.
    """

    def resolve(self, proposals: List[Action]) -> Optional[Action]:
        if not proposals:
            return None

        valid = [p for p in proposals if p.type != ActionType.NO_OP]
        if not valid:
            return None

        if len(valid) == 1:
            return valid[0]

        valid.sort(
            key=lambda a: (a.urgency * a.confidence, a.confidence),
            reverse=True,
        )
        return valid[0]
