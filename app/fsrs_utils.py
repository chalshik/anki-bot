from fsrs import Card


def card_from_row(row: dict) -> Card:
    return Card.from_dict({
        "card_id": row["card_id"],
        "state": row["state"],
        "step": row.get("step"),
        "stability": row.get("stability"),
        "difficulty": row.get("difficulty"),
        "due": row["due"],
        "last_review": row.get("last_review"),
    })


def card_to_dict(card: Card) -> dict:
    d = card.to_dict()
    return {
        "card_id": d["card_id"],
        "state": d["state"],
        "step": d["step"],
        "stability": d["stability"],
        "difficulty": d["difficulty"],
        "due": d["due"],
        "last_review": d["last_review"],
    }
