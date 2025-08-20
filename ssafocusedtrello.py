import json
import csv
import datetime
import os

# 1) Point this at your JSON export (absolute or relative path)
INPUT_JSON = 'leads.json'
OUTPUT_CSV = 'cards.csv'

def get_creation_month(card_id):
    """Trello’s card IDs encode the creation timestamp in the first 8 hex chars."""
    ts = int(card_id[:8], 16)
    return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m')

def main():
    # Load the board export
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        board = json.load(f)

    # Build lookups
    lists   = {lst['id']: lst['name'] for lst in board.get('lists', [])}
    members = {m['id']: (m.get('fullName') or m.get('username')) for m in board.get('members', [])}
    labels  = {lbl['id']: lbl['name'] for lbl in board.get('labels', [])}

    # Write CSV with new columns
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            'card_name',
            'created_month',
            'members',
            'list_name',
            'source_labels',  # labels starting with "SOURCE"
            'li_labels'       # labels starting with "LI"
        ])

        for card in board.get('cards', []):
            if card.get('closed'):
                continue

            card_name    = card.get('name', '')
            month        = get_creation_month(card['id'])
            member_names = [
                members[mid]
                for mid in card.get('idMembers', [])
                if mid in members
            ]
            list_name    = lists.get(card.get('idList'), '')

            # labels beginning with "SOURCE"
            source_labels = [
                labels[lid]
                for lid in card.get('idLabels', [])
                if labels.get(lid, '').startswith('SOURCE')
            ]
            # labels beginning with "LI"
            li_labels = [
                labels[lid]
                for lid in card.get('idLabels', [])
                if labels.get(lid, '').startswith('LI')
            ]

            writer.writerow([
                card_name,
                month,
                '; '.join(member_names),
                list_name,
                '; '.join(source_labels),
                '; '.join(li_labels)
            ])

    print(f"Wrote CSV to {os.path.abspath(OUTPUT_CSV)}")

if __name__ == '__main__':
    main()
