from pathlib import Path

DB_PATH = Path(__file__).parent / "kekobo.db"

CATEGORIES = [
    "Необходимые",
    "Еда домашняя",
    "Еда работа",
    "Ребёнок",
    "Хотелки",
    "Внезапные траты",
]

# Эти две категории считаются отдельными «кошельками»
FOOD_CATEGORIES = {"Еда домашняя", "Еда работа"}