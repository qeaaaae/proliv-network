from __future__ import annotations

from bot.app.web.route_contracts import (
    INTEGER_SCHEMA,
    NULLABLE_STRING_SCHEMA,
    RouteContract,
    ok_envelope_with,
)

from .contract_schemas import BALANCE_SCHEMA, PAYMENT_RESPONSE_SCHEMA, user_contract
from .payloads import WebAppBalanceTopupPayload, WebAppReferralExchangePayload

BALANCE_ROUTE_CONTRACTS: dict[str, RouteContract] = {
    "balance_route": user_contract(response_schema=BALANCE_SCHEMA),
    "balance_topup_route": user_contract(
        request_model=WebAppBalanceTopupPayload,
        response_schema=PAYMENT_RESPONSE_SCHEMA,
    ),
    "referral_exchange_route": user_contract(
        request_model=WebAppReferralExchangePayload,
        response_schema=ok_envelope_with(
            {
                "days": INTEGER_SCHEMA,
                "end_date": NULLABLE_STRING_SCHEMA,
                "end_date_text": NULLABLE_STRING_SCHEMA,
            }
        ),
    ),
}
