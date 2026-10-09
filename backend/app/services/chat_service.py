# On-platform chat anti-fraud moderation and communication leakage filters
import re
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User

# Regular expressions matching phone numbers, UPI IDs, and external URL redirects
PHONE_REGEX = re.compile(r"(\+91[\-\s]?)?[6-9]\d{4}[\-\s]?\d{5}|\b[6-9]\d{9}\b")
UPI_REGEX = re.compile(r"[a-zA-Z0-9.\-_]{2,64}@(okhdfcbank|okaxis|oksbi|paytm|ybl|upi|axl|ibl|barodampay|icici|postbank)", re.IGNORECASE)
LINK_REGEX = re.compile(r"(https?:\/\/|www\.|wa\.me\/|t\.me\/|[a-zA-Z0-9\-]+\.(com|in|co|net|org|io))", re.IGNORECASE)

def sanitize_chat_message(message_text: str) -> dict:
    # Detects and censors phone numbers, UPI IDs, and external links in chat messages
    censored_text = message_text
    leaks_detected = []

    if PHONE_REGEX.search(censored_text):
        leaks_detected.append("PHONE_NUMBER")
        censored_text = PHONE_REGEX.sub("[CENSORED: Phone numbers prohibited on CarVault]", censored_text)

    if UPI_REGEX.search(censored_text):
        leaks_detected.append("UPI_HANDLE")
        censored_text = UPI_REGEX.sub("[CENSORED: Direct UPI payments prohibited]", censored_text)

    if LINK_REGEX.search(censored_text):
        leaks_detected.append("EXTERNAL_LINK")
        censored_text = LINK_REGEX.sub("[CENSORED: External links prohibited]", censored_text)

    has_violation = len(leaks_detected) > 0

    return {
        "original_text": message_text,
        "sanitized_text": censored_text,
        "has_violation": has_violation,
        "violations": leaks_detected
    }

async def record_chat_leak_penalty(sender_id: str, violations: list, db: AsyncSession):
    # Penalizes trust score and flags profile for off-platform payment solicitation
    user = await db.get(User, sender_id)
    if user and user.trust_score:
        if "OFF_PLATFORM_PAYMENT_ATTEMPT" not in user.trust_score.risk_flags:
            user.trust_score.risk_flags.append("OFF_PLATFORM_PAYMENT_ATTEMPT")
            user.trust_score.score = max(0, user.trust_score.score - 15)
            await db.commit()
