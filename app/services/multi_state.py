from dataclasses import dataclass, field


@dataclass
class MultiUserState:
    selected_player_count: int | None = None
    selected_game_id: int | None = None
    games_page: int = 1


@dataclass
class MultiRuntimeState:
    game_id: int
    current_round: int = 0
    total_rounds: int = 0
    phrase: str | None = None
    round_active: bool = False
    start_scheduled: bool = False
    next_round_scheduled: bool = False
    attempts_left: dict[int, int] = field(default_factory=dict)
    answered_correctly: set[int] = field(default_factory=set)
    round_players: dict[int, str | None] = field(default_factory=dict)
    last_phrase: str | None = None


_multi_user_states: dict[int, MultiUserState] = {}
_multi_runtime_states: dict[int, MultiRuntimeState] = {}


def get_multi_state(user_id: int) -> MultiUserState:
    if user_id not in _multi_user_states:
        _multi_user_states[user_id] = MultiUserState()
    return _multi_user_states[user_id]


def reset_multi_state(user_id: int) -> None:
    _multi_user_states[user_id] = MultiUserState()


def get_runtime_state(game_id: int) -> MultiRuntimeState:
    if game_id not in _multi_runtime_states:
        _multi_runtime_states[game_id] = MultiRuntimeState(game_id=game_id)
    return _multi_runtime_states[game_id]


def remove_runtime_state(game_id: int) -> None:
    _multi_runtime_states.pop(game_id, None)
