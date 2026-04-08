from dataclasses import dataclass


@dataclass
class MenuState:
    current_menu: str = "root"


_menu_states: dict[int, MenuState] = {}


def get_menu_state(user_id: int) -> str:
    if user_id not in _menu_states:
        _menu_states[user_id] = MenuState()
    return _menu_states[user_id].current_menu


def set_menu_state(user_id: int, menu_name: str) -> None:
    if user_id not in _menu_states:
        _menu_states[user_id] = MenuState()
    _menu_states[user_id].current_menu = menu_name


def reset_menu_state(user_id: int) -> None:
    _menu_states[user_id] = MenuState()
