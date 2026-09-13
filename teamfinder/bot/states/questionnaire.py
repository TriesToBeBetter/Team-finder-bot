from aiogram.fsm.state import State, StatesGroup


class TeamSearchStates(StatesGroup):
    """FSM states for individual specialist looking for a team."""
    name = State()
    role = State()
    skills = State()
    experience = State()
    looking_for = State()
    availability = State()
    about = State()
    confirm = State()


class MemberSearchStates(StatesGroup):
    """FSM states for a project creator looking for team members."""
    name = State()
    role = State()
    skills = State()
    experience = State()
    project_description = State()
    availability = State()
    about = State()
    confirm = State()
