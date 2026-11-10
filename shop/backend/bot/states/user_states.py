from aiogram.fsm.state import State, StatesGroup


class UserPromoStates(StatesGroup):
    waiting_for_promo_code = State()


class UserDeviceRenameStates(StatesGroup):
    waiting_for_name = State()


class WinbackSurveyStates(StatesGroup):
    waiting_for_location = State()
    waiting_for_unstable_note = State()


class NotrialSurveyStates(StatesGroup):
    waiting_for_reason_text = State()
