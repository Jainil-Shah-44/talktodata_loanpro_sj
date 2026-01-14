import re
from datetime import date, timedelta
from calendar import monthrange

DPD36M_THRESHOLD = 90
DPD36M_TOLERANCE_DAYS = 0

MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12
}

# def infer_npa_from_dpd36m(additional_fields: dict):
#     """
#     Infers NPA date from DPD 36M values using threshold-crossing logic.
#     """
#     if not additional_fields:
#         return None

#     pattern = pattern = re.compile(r"([a-z]{3})_(\d{2})", re.IGNORECASE)

#     series = []

#     for k, v in additional_fields.items():
#         m = pattern.match(k)
#         if not m:
#             continue

#         try:
#             mon_txt, yr_txt = m.groups()
#             month = MONTH_MAP[mon_txt.lower()]
#             year = 2000 + int(yr_txt)
#             dpd_val = int(v)
#         except Exception:
#             continue

#         series.append((year, month, dpd_val))

#     # Need at least two months
#     if len(series) < 2:
#         return None

#     # Sort chronologically
#     series.sort(key=lambda x: (x[0], x[1]))

#     for i in range(1, len(series)):
#         prev_year, prev_month, prev_dpd = series[i - 1]
#         curr_year, curr_month, curr_dpd = series[i]

#         if prev_dpd < DPD36M_THRESHOLD <= curr_dpd:
#             # Days into current month where threshold is crossed
#             days_into_month = DPD36M_THRESHOLD - prev_dpd

#             # Clamp safety
#             days_in_month = monthrange(curr_year, curr_month)[1]
#             days_into_month = min(days_into_month, days_in_month - 1)

#             inferred_date = date(curr_year, curr_month, days_into_month)

#             return inferred_date
    
    

#     return None
def normalize_additional_fields(af: dict) -> dict:
    if not af:
        return {"collection": {}, "dpd": {}}

    # ✅ NEW MODEL
    if "dpd36m" in af or "collection36m" in af:
        return {
            "collection": af.get("collection36m", {}),
            "dpd": af.get("dpd36m", {})
        }

    # Legacy namespaced
    if "dpd" in af or "collection" in af:
        return {
            "collection": af.get("collection", {}),
            "dpd": af.get("dpd", {})
        }

    # Legacy flat → assume DPD
    return {
        "collection": {},
        "dpd": af
    }


def infer_npa_from_dpd36m(additional_fields: dict):
    af = normalize_additional_fields(additional_fields)
    dpd_fields = af.get("dpd", {})

    if not dpd_fields:
        return None

    pattern = re.compile(r"([a-z]{3})_(\d{2})", re.IGNORECASE)
    series = []

    for k, v in dpd_fields.items():
        m = pattern.match(k)
        if not m:
            continue

        try:
            mon_txt, yr_txt = m.groups()
            month = MONTH_MAP[mon_txt.lower()]
            year = 2000 + int(yr_txt)
            try:
                dpd_val = int(float(v))
            except Exception:
                continue

        except Exception:
            continue

        series.append((year, month, dpd_val))

    if len(series) < 2:
        return None

    series.sort(key=lambda x: (x[0], x[1]))

    for i in range(1, len(series)):
        prev_year, prev_month, prev_dpd = series[i - 1]
        curr_year, curr_month, curr_dpd = series[i]

        if prev_dpd < DPD36M_THRESHOLD <= curr_dpd:
            day = DPD36M_THRESHOLD - prev_dpd
            days_in_month = monthrange(curr_year, curr_month)[1]
            day = max(1, min(day, days_in_month))

            return date(curr_year, curr_month, day)

    return None
