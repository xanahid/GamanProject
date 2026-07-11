"""
Thin wrapper around ZarinPal's REST API (https://docs.zarinpal.com).

Kept deliberately small and dependency-free (just `requests`) so the entire
money-moving surface of the app is auditable in one file. Nothing here ever
touches a raw card number — ZarinPal's hosted payment page collects card
details directly; we only ever see `authority` (transaction handle) and,
after verification, `ref_id` (settlement reference) and a masked PAN.
"""
import requests
from django.conf import settings

ZARINPAL_SANDBOX_BASE = "https://sandbox.zarinpal.com/pg/v4/payment"
ZARINPAL_LIVE_BASE = "https://payment.zarinpal.com/pg/v4/payment"
ZARINPAL_SANDBOX_STARTPAY = "https://sandbox.zarinpal.com/pg/StartPay/"
ZARINPAL_LIVE_STARTPAY = "https://payment.zarinpal.com/pg/StartPay/"

REQUEST_TIMEOUT_SECONDS = 10


class ZarinPalError(Exception):
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code


def _base_url():
    return ZARINPAL_SANDBOX_BASE if settings.ZARINPAL_SANDBOX else ZARINPAL_LIVE_BASE


def _startpay_url():
    return ZARINPAL_SANDBOX_STARTPAY if settings.ZARINPAL_SANDBOX else ZARINPAL_LIVE_STARTPAY


def request_payment(amount_rials: int, description: str, callback_url: str, mobile: str = "", email: str = "") -> dict:
    """
    Step 1 of ZarinPal flow: ask for a transaction `authority`.
    Returns {"authority": "...", "redirect_url": "..."} on success.
    Raises ZarinPalError on any non-100 status code from the gateway.
    """
    payload = {
        "merchant_id": settings.ZARINPAL_MERCHANT_ID,
        "amount": amount_rials,
        "description": description,
        "callback_url": callback_url,
    }
    if mobile:
        payload["metadata"] = {"mobile": mobile}
    if email:
        payload.setdefault("metadata", {})["email"] = email

    try:
        resp = requests.post(f"{_base_url()}/request.json", json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        raise ZarinPalError(f"خطا در ارتباط با درگاه پرداخت: {exc}") from exc

    errors = data.get("errors")
    if errors:
        raise ZarinPalError(str(errors), code=errors.get("code") if isinstance(errors, dict) else None)

    result = data.get("data", {})
    if result.get("code") != 100:
        raise ZarinPalError(f"درگاه پرداخت درخواست را رد کرد: {result}", code=result.get("code"))

    authority = result["authority"]
    return {
        "authority": authority,
        "redirect_url": f"{_startpay_url()}{authority}",
    }


def verify_payment(amount_rials: int, authority: str) -> dict:
    """
    Step 2: after ZarinPal redirects the user back to our callback URL,
    confirm the transaction actually succeeded server-to-server before we
    ever mark a slot as booked. Returns {"ref_id": ..., "card_pan": ...}
    on success; raises ZarinPalError otherwise.
    """
    payload = {
        "merchant_id": settings.ZARINPAL_MERCHANT_ID,
        "amount": amount_rials,
        "authority": authority,
    }
    try:
        resp = requests.post(f"{_base_url()}/verify.json", json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        raise ZarinPalError(f"خطا در تأیید پرداخت: {exc}") from exc

    errors = data.get("errors")
    if errors:
        raise ZarinPalError(str(errors), code=errors.get("code") if isinstance(errors, dict) else None)

    result = data.get("data", {})
    # 100 = freshly verified, 101 = already verified (idempotent retry) —
    # both count as success per ZarinPal docs.
    if result.get("code") not in (100, 101):
        raise ZarinPalError(f"پرداخت تأیید نشد: {result}", code=result.get("code"))

    return {
        "ref_id": str(result.get("ref_id", "")),
        "card_pan": result.get("card_pan", ""),
    }
