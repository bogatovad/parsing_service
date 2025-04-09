import json
import os
import re
from datetime import datetime
from rapidfuzz import fuzz

DEDUP_LOG_PATH = "dedup_log.json"

def load_dedup_log(log_path: str = DEDUP_LOG_PATH) -> list:
    if not os.path.exists(log_path):
        return []
    with open(log_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_dedup_log(events: list, log_path: str = DEDUP_LOG_PATH) -> None:
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

def normalize_string(s: str) -> str:
    return s.lower().strip()

def normalize_date(dt) -> str:
    if dt is None:
        return ""
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d")
    return str(dt).strip()

def normalize_time(t: str) -> str:
    if not t:
        return ""
    return t.lower().strip()

def normalize_location(loc: str) -> str:
    return loc.lower().strip()

def normalize_fuzzy(s: str) -> str:
    s = re.sub(r'[^\w\s]', '', s.lower())
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def normalize_event_fields(event: dict) -> dict:
    return {
        "name": normalize_string(event.get("name", "")),
        "date": normalize_date(event.get("date_start", event.get("date"))),
        "time": normalize_time(event.get("time")),
        "location": normalize_location(event.get("location", ""))
    }

def is_duplicate(new_evt: dict, existing_evt: dict,
                 fuzz_threshold_name=80,
                 fuzz_threshold_location=85) -> bool:

    same_date = new_evt["date"] == existing_evt["date"]
    same_time = new_evt["time"] == existing_evt["time"] and new_evt["time"] != "" and existing_evt["time"] != ""

    location_similarity = fuzz.token_set_ratio(
        normalize_fuzzy(new_evt["location"]),
        normalize_fuzzy(existing_evt["location"])
    )
    same_loc = location_similarity >= fuzz_threshold_location

    name_similarity = fuzz.token_set_ratio(
        normalize_fuzzy(new_evt["name"]),
        normalize_fuzzy(existing_evt["name"])
    )
    same_name = name_similarity >= fuzz_threshold_name

    if same_date and same_time and same_loc:
        return True

    if same_date and (new_evt["time"] == "" or existing_evt["time"] == ""):
        if same_loc and same_name:
            return True

    return False

def check_and_add_event(new_event_raw: dict,
                        log_path: str = DEDUP_LOG_PATH,
                        fuzz_threshold_name: int = 80,
                        fuzz_threshold_location: int = 85) -> bool:

    existing_events = load_dedup_log(log_path)
    new_evt_norm = normalize_event_fields(new_event_raw)

    for ev in existing_events:
        if is_duplicate(new_evt_norm, ev,
                        fuzz_threshold_name=fuzz_threshold_name,
                        fuzz_threshold_location=fuzz_threshold_location):
            return True

    existing_events.append(new_evt_norm)
    save_dedup_log(existing_events, log_path)
    return False
