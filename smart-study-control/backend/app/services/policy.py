from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def window_active(window, local):
    minute = local.hour * 60 + local.minute
    day = local.isoweekday()
    start, end = window["start_minute"], window["end_minute"]
    if start < end:
        return day in window["days"] and start <= minute < end
    previous = (day - 2) % 7 + 1
    return (day in window["days"] and minute >= start) or (previous in window["days"] and minute < end)


def decision(policy, package, instant, earned=False, protected=()):
    if package in protected or package in policy.get("essential_packages", []):
        return "ESSENTIAL"
    if package in policy.get("safety_packages", []):
        return "SAFETY"
    override = policy.get("override_until")
    if override:
        value = datetime.fromisoformat(override.replace("Z", "+00:00"))
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        if instant < value:
            return "OVERRIDE"
    if package not in policy.get("blocked_packages", []):
        return "ALLOW"
    local = instant.astimezone(ZoneInfo(policy.get("timezone", "Asia/Tashkent")))
    if any(window_active(w, local) for w in policy.get("sleep", [])):
        return "SLEEP"
    if any(window_active(w, local) for w in policy.get("study", [])):
        return "STUDY"
    if earned:
        return "EARNED"
    return "DEFAULT_BLOCK" if policy.get("default_blocked", False) else "ALLOW"
