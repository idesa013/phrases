from dataclasses import dataclass


@dataclass
class MultiUserState:
    menu_level: str = "root"
    selected_player_count: int | None = None
    selected_game_id: int | None = None
    games_page: int = 1


_multi_states: dict[int, MultiUserState] = {}


def get_multi_state(user_id: int) -> MultiUserState:
    if user_id not in _multi_states:
        _multi_states[user_id] = MultiUserState()
    return _multi_states[user_id]


def reset_multi_state(user_id: int) -> None:
    _multi_states[user_id] = MultiUserState()
