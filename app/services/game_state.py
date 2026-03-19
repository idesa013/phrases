from dataclasses import dataclass
from time import time


@dataclass
class GameState:
    phrase: str | None = None
    last_phrase: str | None = None
    waiting_for_answer: bool = False
    answer_shown: bool = False
    generated_at: float = 0.0
    image_message_id: int | None = None


USER_STATES: dict[int, GameState] = {}


def get_state(user_id: int) -> GameState:
    if user_id not in USER_STATES:
        USER_STATES[user_id] = GameState()
    return USER_STATES[user_id]


def mark_generated(user_id: int, phrase: str) -> GameState:
    state = get_state(user_id)

    if state.phrase:
        state.last_phrase = state.phrase

    state.phrase = phrase
    state.waiting_for_answer = True
    state.answer_shown = False
    state.generated_at = time()
    state.image_message_id = None
    return state
