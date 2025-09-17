import json
import csv
import datetime
import unicodedata
from typing import Dict, List, Set

JSON_PATH = "leads.json"
OUTPUT_CSV = "cards_with_source_list_month_and_target_move.csv"
UNRESOLVED_CSV = "unresolved_in_target_no_move_found.csv"

# --- Configure your target list (allow aliases to be safe) ---
TARGET_LIST_ALIASES = {
    "Positive Reply - sent to Qualified Leads",
    # add any historical or slightly different variants here:
    "Positive Reply – sent to Qualified Leads",  # en dash
    "Positive Reply—sent to Qualified Leads",    # em dash
    "positive reply - sent to qualified leads",  # casing variant (norm will lower anyway)
}

def norm(s: str) -> str:
    """Normalize strings for safe name comparison."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    # unify dashes
    s = s.replace("–", "-").replace("—", "-")
    # lowercase, trim, collapse spaces
    s = " ".join(s.strip().lower().split())
    return s

NORM_ALIASES = {norm(x) for x in TARGET_LIST_ALIASES}

def get_creation_datetime_from_id(trello_id: str) -> datetime.datetime:
    """Trello card IDs embed a unix timestamp (first 8 hex chars), UTC."""
    epoch_time = int(trello_id[:8], 16)
    return datetime.datetime.utcfromtimestamp(epoch_time)

def iso_to_dt_utc(s: str) -> datetime.datetime:
    """Parse ISO-8601 with optional Z, return aware datetime in UTC."""
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.datetime.fromisoformat(s)

def collect_target_list_ids(data: dict) -> Set[str]:
    """Find list IDs that currently have a name matching any alias."""
    ids = set()
    for lst in data.get("lists", []):
        if norm(lst.get("name")) in NORM_ALIASES:
            ids.add(lst["id"])
    return ids

def also_collect_ids_from_actions(data: dict, seed_ids: Set[str]) -> Set[str]:
    """
    Some actions only give names. If we ever see a list name that matches
    our aliases AND an id present, include that id too.
    """
    ids = set(seed_ids)
    for a in data.get("actions", []):
        d = a.get("data", {})
        # createCard: data.list may have id & name
        if a.get("type") == "createCard":
            lst = d.get("list") or {}
            if norm(lst.get("name")) in NORM_ALIASES and lst.get("id"):
                ids.add(lst["id"])
        # updateCard moves: data.listAfter may have id & name
        if a.get("type") == "updateCard":
            la = d.get("listAfter") or {}
            if norm(la.get("name")) in NORM_ALIASES and la.get("id"):
                ids.add(la["id"])
        # copyCard: data.list is the destination list
        if a.get("type") == "copyCard":
            lst = d.get("list") or {}
            if norm(lst.get("name")) in NORM_ALIASES and lst.get("id"):
                ids.add(lst["id"])
        # moveCardToBoard: data.list is the destination list on this board
        if a.get("type") == "moveCardToBoard":
            lst = d.get("list") or {}
            if norm(lst.get("name")) in NORM_ALIASES and lst.get("id"):
                ids.add(lst["id"])
        # convertToCardFromCheckItem: data.list is where the card was created
        if a.get("type") == "convertToCardFromCheckItem":
            lst = d.get("list") or {}
            if norm(lst.get("name")) in NORM_ALIASES and lst.get("id"):
                ids.add(lst["id"])
    return ids

def first_month_card_entered_target(data: dict, target_ids: Set[str]) -> Dict[str, str]:
    """
    Earliest YYYY-MM a card entered the target list, scanning multiple action types.
    """
    results: Dict[str, str] = {}
    actions = sorted(data.get("actions", []), key=lambda a: a.get("date", ""))

    def is_target_by_id_or_name(lst_obj: dict) -> bool:
        if not lst_obj:
            return False
        if lst_obj.get("id") in target_ids:
            return True
        return norm(lst_obj.get("name")) in NORM_ALIASES

    for a in actions:
        t = a.get("type")
        d = a.get("data", {})
        card = d.get("card") or {}

        if not card or not card.get("id"):
            continue

        # --- createCard (card starts in a list)
        if t == "createCard":
            lst = d.get("list") or {}
            if is_target_by_id_or_name(lst):
                month = iso_to_dt_utc(a["date"]).strftime("%Y-%m")
                results.setdefault(card["id"], month)

        # --- updateCard (moved to another list)
        elif t == "updateCard":
            list_after = d.get("listAfter") or {}
            if is_target_by_id_or_name(list_after):
                month = iso_to_dt_utc(a["date"]).strftime("%Y-%m")
                results.setdefault(card["id"], month)

        # --- copyCard (copied into a list)
        elif t == "copyCard":
            lst = d.get("list") or {}
            if is_target_by_id_or_name(lst):
                month = iso_to_dt_utc(a["date"]).strftime("%Y-%m")
                results.setdefault(card["id"], month)

        # --- moveCardToBoard (moved from another board into this list)
        elif t == "moveCardToBoard":
            lst = d.get("list") or {}
            if is_target_by_id_or_name(lst):
                month = iso_to_dt_utc(a["date"]).strftime("%Y-%m")
                results.setdefault(card["id"], month)

        # --- convertToCardFromCheckItem (card created from a checklist item)
        elif t == "convertToCardFromCheckItem":
            lst = d.get("list") or {}
            if is_target_by_id_or_name(lst):
                month = iso_to_dt_utc(a["date"]).strftime("%Y-%m")
                results.setdefault(card["id"], month)

    return results

def main():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    cards: List[dict] = data["cards"]
    lists_data: List[dict] = data.get("lists", [])
    label_names: dict = data.get("labelNames", {})
    labels_array: List[dict] = data.get("labels", [])

    # id -> list name map
    list_name_by_id = {lst["id"]: lst.get("name", "") for lst in lists_data}

    # custom labels: id -> name
    custom_label_by_id = {lab["id"]: lab.get("name", "") for lab in labels_array}

    # find target list IDs by current list names, and enrich them using actions
    target_ids = collect_target_list_ids(data)
    target_ids = also_collect_ids_from_actions(data, target_ids)

    # compute first month entering target
    entered_month = first_month_card_entered_target(data, target_ids)

    rows = []
    unresolved_rows = []  # cards currently in target but no move month found

    for card in cards:
        cid = card["id"]
        cname = card.get("name", "")

        # creation month from id
        creation_month = get_creation_datetime_from_id(cid).strftime("%Y-%m")

        # current column
        list_id = card.get("idList", "")
        current_list_name = list_name_by_id.get(list_id, "")

        # source label (first that contains 'SOURCE:')
        source_label = ""
        for lbl_id in card.get("idLabels", []):
            if lbl_id in label_names:
                txt = label_names.get(lbl_id, "")
                if "SOURCE:" in (txt or ""):
                    source_label = txt
                    break
            else:
                txt = custom_label_by_id.get(lbl_id, "")
                if "SOURCE:" in (txt or ""):
                    source_label = txt
                    break

        # earliest month card entered target
        target_month = entered_month.get(cid, "")
        moved_diff = ""
        if target_month:
            moved_diff = "Yes" if target_month != creation_month else "No"

        rows.append([
            cname,
            current_list_name,
            source_label,
            creation_month,
            target_month,
            moved_diff
        ])

        # collect unresolved
        if (list_id in target_ids or norm(current_list_name) in NORM_ALIASES) and not target_month:
            unresolved_rows.append([cname, cid, current_list_name])

    # write main CSV
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "Card Name",
            "Current Column",
            "Source Label",
            "Creation Month",
            "Moved to Target Month",
            "Moved to Target Different Month"
        ])
        w.writerows(rows)

    # write unresolved diagnostics CSV
    if unresolved_rows:
        with open(UNRESOLVED_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Card Name", "Card ID", "Current Column (is target) but no move-month found"])
            w.writerows(unresolved_rows)

    print(f"Done! Wrote {OUTPUT_CSV}")
    if unresolved_rows:
        print(f"Also wrote {UNRESOLVED_CSV} with cards in the target list but no detected entry month.")
        print("Likely causes: truncated/missing actions, historical rename/recreate, or an unhandled action type.")

if __name__ == "__main__":
    main()