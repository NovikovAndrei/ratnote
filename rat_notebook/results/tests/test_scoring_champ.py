import pytest
from results.scoring import calculate_champion_points

# ---- ДАННЫЕ ЧЕМПИОНОВ (из твоей таблицы) ----

CHAMPIONS = [
    # name, norms_key, results_in, expected_points, total_expected, place_expected
    (
        "Flash Drive K9's Caribbean Cocaine  (Кока)",
        "L",  # АПБТ L → нормы L
        {"long_jump": 5.3, "wall_jump": 3.6, "high_jump": 2.2, "treadmill": 38.85},
        {"long_jump": 10,  "wall_jump": 13,  "high_jump": 13,  "treadmill": 11},
        47, 4,
    ),
    (
        "Ирма Императрица Роял Бриллиантс (Ирма)",
        "M",  # АПБТ M → нормы M
        {"long_jump": 5.8, "wall_jump": 3.7, "high_jump": 2.2, "treadmill": 52.03},
        {"long_jump": 17,  "wall_jump": 22,  "high_jump": 19,  "treadmill": 0},
        58, 2,
    ),
    (
        "Flash Drive K9's Arabella (Белка)",
        "S",  # АПБТ S → нормы S
        {"long_jump": 5.7, "wall_jump": 3.2, "high_jump": 1.9, "treadmill": 42.66},
        {"long_jump": 18,  "wall_jump": 13,  "high_jump": 0,   "treadmill": 11},
        42, 5,
    ),
    (
        "Шакира",
        "M",  # АПБТ M → нормы M
        {"long_jump": 5.0, "wall_jump": 0.0, "high_jump": 2.2, "treadmill": 39.53},
        {"long_jump": 0,   "wall_jump": -10, "high_jump": 19,  "treadmill": 12},
        21, 10,
    ),
    (
        "Denvers Elite Tinki (Трой)",
        "АСТ_M",
        {"long_jump": 4.7, "wall_jump": 3.0, "high_jump": 2.05, "treadmill": 52.00},
        {"long_jump": 10,  "wall_jump": 0,   "high_jump": 13,   "treadmill": 0},
        23, 9,
    ),
    (
        "FOREVER YOUNG'S BALAGOS (ARCHI) (Арчи)",
        "L",
        {"long_jump": 5.0, "wall_jump": 3.0, "high_jump": 2.35, "treadmill": 36.25},
        {"long_jump": 0,   "wall_jump": 0,   "high_jump": 22,   "treadmill": 12},
        34, 6,
    ),
    (
        "Шайтан Коденц де Лютвинс (Найк)",
        "Малинуа",
        {"long_jump": 6.0, "wall_jump": 3.3, "high_jump": 2.45, "treadmill": 36.75},
        {"long_jump": 17,  "wall_jump": 0,   "high_jump": 19,   "treadmill": 12},
        48, 3,
    ),
    (
        "Юнн Король Лесных Эльфов (Юнн)",
        "СБТ",
        {"long_jump": 4.5, "wall_jump": 2.7, "high_jump": 1.75, "treadmill": 0.0},
        {"long_jump": 18,  "wall_jump": 10,  "high_jump": 16,   "treadmill": -10},
        34, 6,
    ),
    (
        "Hassliebenk's Kraken (Кракен)",
        "S",
        {"long_jump": 5.1, "wall_jump": 2.9, "high_jump": 1.95, "treadmill": 42.97},
        {"long_jump": 12,  "wall_jump": 0,   "high_jump": 10,   "treadmill": 11},
        33, 8,
    ),
    (
        "Винер хунд Оскар (Оскар)",
        "Малинуа",
        {"long_jump": 6.0, "wall_jump": 4.3, "high_jump": 2.35, "treadmill": 41.50},
        {"long_jump": 17,  "wall_jump": 28,  "high_jump": 13,   "treadmill": 10},
        68, 1,
    ),
]

def _m_to_cm(x):
    """Прыжки из м → см (если <10 считаем метры)."""
    return int(round(float(x) * 100)) if x is not None and float(x) < 10 else int(round(float(x or 0)))

def _competition_places(items):
    """items: list[(name, total)] → {name: place} по competition ranking."""
    items_sorted = sorted(items, key=lambda t: t[1], reverse=True)
    places = {}
    last = None
    place = 0
    idx = 0
    for name, total in items_sorted:
        idx += 1
        if total != last:
            place = idx
            last = total
        places[name] = place
    return places


@pytest.mark.parametrize(
    "name,cat,results_in,points_expected,total_expected,_place",
    CHAMPIONS,
)
def test_champions_points_and_totals_formula(name, cat, results_in, points_expected, total_expected, _place):
    """
    Чемпионы: проверяем, что calculate_champion_points на базе нормативов
    даёт ожидаемые очки по каждому снаряду и сумму.
    """
    # Конвертим прыжки в сантиметры
    r_long = _m_to_cm(results_in["long_jump"])
    r_wall = _m_to_cm(results_in["wall_jump"])
    r_high = _m_to_cm(results_in["high_jump"])
    r_tread = results_in["treadmill"]

    got = {
        "long_jump":   calculate_champion_points(cat, "long_jump", r_long),
        "wall_jump":   calculate_champion_points(cat, "wall_jump", r_wall),
        "high_jump":   calculate_champion_points(cat, "high_jump", r_high),
        "treadmill":   calculate_champion_points(cat, "treadmill", r_tread),
    }

    assert got == points_expected, f"{name}: ожидали {points_expected}, получили {got}"
    assert sum(got.values()) == total_expected, f"{name}: сумма должна быть {total_expected}"


def test_champions_competition_ranking():
    """
    Чемпионы: проверяем итоговые места по competition ranking на основе сумм очков.
    """
    totals = [(name, total) for (name, _cat, _rin, _pexp, total, _pl) in CHAMPIONS]
    expected_places = {name: place for (name, _cat, _rin, _pexp, _tot, place) in CHAMPIONS}
    got_places = _competition_places(totals)

    assert got_places == expected_places, f"Места: ожидали {expected_places}, получили {got_places}"
