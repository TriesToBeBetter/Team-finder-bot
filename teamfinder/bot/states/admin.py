from aiogram.fsm.state import State, StatesGroup


class AdminContactStates(StatesGroup):
    """FSM states when admin sends a message to an applicant."""
    waiting_for_message = State()


class UserReplyStates(StatesGroup):
    """FSM states when an applicant replies back to an admin message."""
    waiting_for_reply = State()


class AdminSearchStates(StatesGroup):
    """FSM states when admin searches applications."""
    waiting_for_query = State()
