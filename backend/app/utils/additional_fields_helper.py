import re


MONTH_KEY_REGEX = re.compile(r"^[a-zA-Z]+_\d{2}$")

MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8,
    "sep": 9, "sept": 9,
    "oct": 10, "nov": 11, "dec": 12
}


def normalize_additional_fields(af: dict | None) -> dict:
    """
    Normalizes additional_fields into a strict schema:

    {
        "dpd36m": {...},
        "collection36m": {...}
    }
    """

    def _filter_month_keys(d: dict) -> dict:
        return {
            k.lower(): v
            for k, v in d.items()
            if isinstance(k, str) and MONTH_KEY_REGEX.match(k)
        }

    # Invalid / empty
    if not isinstance(af, dict):
        return {"dpd36m": {}, "collection36m": {}}

    # ✅ New structure (current system)
    if "dpd36m" in af or "collection36m" in af:
        return {
            "dpd36m": _filter_month_keys(af.get("dpd36m", {}))
            if isinstance(af.get("dpd36m"), dict) else {},
            "collection36m": _filter_month_keys(af.get("collection36m", {}))
            if isinstance(af.get("collection36m"), dict) else {},
        }

    out = {"dpd36m": {}, "collection36m": {}}

    # 🟡 Legacy namespaced structure
    if isinstance(af.get("dpd"), dict):
        out["dpd36m"] = _filter_month_keys(af["dpd"])

    if isinstance(af.get("collection"), dict):
        out["collection36m"] = _filter_month_keys(af["collection"])

    # 🔵 Very old flat structure → assume dpd36m
    if not out["dpd36m"] and not out["collection36m"]:
        out["dpd36m"] = _filter_month_keys(af)

    return out
