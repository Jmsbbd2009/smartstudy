def normalize_login(value: str) -> str:
    raw = value.strip().lower()
    if "@" in raw:
        return raw
    if any(character not in "+0123456789 ()-." for character in raw):
        return "".join(raw.split())
    phone = "".join(character for character in raw if character.isdigit() or character == "+")
    if sum(character.isdigit() for character in phone) >= 7:
        return phone
    return "".join(raw.split())
