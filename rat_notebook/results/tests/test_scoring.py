# -*- coding: utf-8 -*-
import pytest
from results.models import Event, Athlete, DisciplineType, DisciplineResult
from results.scoring import assign_growth_scores

pytestmark = pytest.mark.django_db

# ====================== ФИКСТУРЫ ======================

@pytest.fixture
def event_with_disciplines():
    """Создаёт событие и справочник дисциплин."""
    d_long = DisciplineType.objects.create(code="long_jump", verbose="Прыжок в длину")
    d_wall = DisciplineType.objects.create(code="wall_jump", verbose="Стена")
    d_high = DisciplineType.objects.create(code="high_jump", verbose="Б/О прыжок")
    d_tread = DisciplineType.objects.create(code="treadmill", verbose="Дорожка (300 м)")

    ev = Event.objects.create(name="Rat Cup", date="2025-01-01")
    ev.disciplines.add(d_long, d_wall, d_high, d_tread)

    return {
        "event": ev,
        "disc": {"long_jump": d_long, "wall_jump": d_wall, "high_jump": d_high, "treadmill": d_tread},
    }


@pytest.fixture
def make_athlete_with_results(event_with_disciplines):
    """
    Фабрика спортсмена с результатами.
    Удобный ввод в МЕТРАХ для прыжков — конвертируем в СМ:
      - long_jump, wall_jump, high_jump: 5.50 -> 550, 2.05 -> 205
      - treadmill остаётся в секундах
    """
    ev = event_with_disciplines["event"]
    disc = event_with_disciplines["disc"]

    METER_BASED = {"long_jump", "wall_jump", "high_jump"}

    def _to_cm(x):
        if x is None:
            return 0
        xv = float(x)
        # если < 10, считаем, что это метры, иначе — уже сантиметры
        return int(round(xv * 100)) if xv < 10 else int(round(xv))

    def _make(name: str, growth="XL", is_champion=False, **results_by_code):
        ath = Athlete.objects.create(event=ev, name=name, growth_category=growth, is_champion=is_champion)
        for code, value in results_by_code.items():
            v = _to_cm(value) if code in METER_BASED else value
            DisciplineResult.objects.create(
                athlete=ath,
                discipline=disc[code],
                result=v,
                points=0,  # будет заполнено assign_growth_scores
            )
        return ath

    return _make


# ====================== ДАННЫЕ ДЛЯ ТЕСТОВ ======================

# --- Группа S (как раньше) ---
ATHLETES_S = [
    (
        "FDK’s Fiji aka Tykva / Тыква",
        {"long_jump": 420, "wall_jump": 330, "high_jump": 190, "treadmill": 40.55},
        {"long_jump": 25, "wall_jump": 20, "high_jump": 20, "treadmill": 25},
        90, 1,
    ),
    (
        "FLK’s Corpse Bride / Импала",
        {"long_jump": 380, "wall_jump": 260, "high_jump": 180, "treadmill": 41.94},
        {"long_jump": 20, "wall_jump": 15, "high_jump": 15, "treadmill": 20},
        70, 3,
    ),
    (
        "Dragon’s Emblema Tsunami / Цунами",
        {"long_jump": 300, "wall_jump": 340, "high_jump": 200, "treadmill": 52.04},
        {"long_jump": 15, "wall_jump": 25, "high_jump": 25, "treadmill": 15},
        80, 2,
    ),
]

# --- Группа M (расширенная) ---
ATHLETES_M = [
    (
        "Крепкий Орешек Из Замка Ланселота/ Брюс",
        {"long_jump": 3.8, "wall_jump": 3.0, "high_jump": 1.85, "treadmill": 41.49},
        {"long_jump": 8,  "wall_jump": 4,  "high_jump": 8,  "treadmill": 2},
        22, 11,
    ),
    (
        "FDK’s Fargo / Фарго",
        {"long_jump": 5.0, "wall_jump": 3.8, "high_jump": 2.15, "treadmill": 37.10},
        {"long_jump": 15, "wall_jump": 20, "high_jump": 20, "treadmill": 15},
        70, 2,
    ),
    (
        "Брэйв Файтер’с Цусима/ Сима",
        {"long_jump": 5.2, "wall_jump": 3.4, "high_jump": 2.10, "treadmill": 37.58},
        {"long_jump": 20, "wall_jump": 10, "high_jump": 15, "treadmill": 12},
        57, 7,
    ),
    (
        "Flash Drive K9's Ecstasy (Эльза)",
        {"long_jump": 5.5, "wall_jump": 3.7, "high_jump": 2.15, "treadmill": 38.06},
        {"long_jump": 25, "wall_jump": 15, "high_jump": 20, "treadmill": 8},
        68, 5,
    ),
    (
        "Brave Fighter’s Unchain My Heart (Печенька)",
        {"long_jump": 5.5, "wall_jump": 3.4, "high_jump": 2.20, "treadmill": 37.75},
        {"long_jump": 25, "wall_jump": 10, "high_jump": 25, "treadmill": 10},
        70, 2,
    ),
    (
        "FDK’s Fargo /Смарт",
        {"long_jump": 4.0, "wall_jump": 3.5, "high_jump": 2.20, "treadmill": 54.67},
        {"long_jump": 10, "wall_jump": 12, "high_jump": 25, "treadmill": 0},
        47, 8,
    ),
    (
        "Brave Fighter's Rainbow (Рейси)",
        {"long_jump": 5.5, "wall_jump": 3.4, "high_jump": 2.20, "treadmill": 35.78},
        {"long_jump": 25, "wall_jump": 10, "high_jump": 25, "treadmill": 25},
        85, 1,
    ),
    (
        "FDK’s(GPK’s) Mr. Lover Boy / Ландо",
        {"long_jump": 3.0, "wall_jump": 3.2, "high_jump": 2.10, "treadmill": 39.20},
        {"long_jump": 6,  "wall_jump": 8,  "high_jump": 15, "treadmill": 4},
        33, 10,
    ),
    (
        "Шайена",
        {"long_jump": 5.5, "wall_jump": 3.5, "high_jump": 2.05, "treadmill": 36.46},
        {"long_jump": 25, "wall_jump": 12, "high_jump": 12, "treadmill": 20},
        69, 4,
    ),
    (
        "FDK’s Fury / Фьюри",
        {"long_jump": 5.0, "wall_jump": 4.0, "high_jump": 2.15, "treadmill": 50.71},
        {"long_jump": 15, "wall_jump": 25, "high_jump": 20, "treadmill": 1},
        61, 6,
    ),
    (
        "Framedog’s KEIJI / КЕЙДЖИ",
        {"long_jump": 4.6, "wall_jump": 3.1, "high_jump": 2.00, "treadmill": 39.03},
        {"long_jump": 12, "wall_jump": 6,  "high_jump": 10, "treadmill": 6},
        34, 9,
    ),
]

# --- Группа L (из твоей таблицы) ---
ATHLETES_L = [
    (
        "Strong Spirit Sherlock (Сэм)",
        {"long_jump": 3.4, "wall_jump": 3.0, "high_jump": 2.05, "treadmill": 40.01},
        {"long_jump": 8,  "wall_jump": 8,  "high_jump": 10, "treadmill": 12},
        38, 6,
    ),
    (
        "Dragon's Black Crazy Sqirrel / Белка",
        {"long_jump": 5.7, "wall_jump": 3.6, "high_jump": 2.05, "treadmill": 52.14},
        {"long_jump": 20, "wall_jump": 15, "high_jump": 10, "treadmill": 6},
        51, 3,
    ),
    (
        "ДэЙмон/Дэй",
        {"long_jump": 4.7, "wall_jump": 3.5, "high_jump": 2.10, "treadmill": 44.72},
        {"long_jump": 15, "wall_jump": 12, "high_jump": 12, "treadmill": 8},
        47, 4,
    ),
    (
        "Милана (Хамви)",
        {"long_jump": 4.2, "wall_jump": 3.2, "high_jump": 0.0, "treadmill": 0.0},
        {"long_jump": 12, "wall_jump": 10, "high_jump": -25, "treadmill": -25},
        -28, 9,
    ),
    (
        "Kage/Браун",
        {"long_jump": 3.5, "wall_jump": 3.2, "high_jump": 2.05, "treadmill": 32.95},
        {"long_jump": 10, "wall_jump": 10, "high_jump": 10, "treadmill": 25},
        55, 2,
    ),
    (
        "CHADIN'S SINAI  /  Синай",
        {"long_jump": 0.0, "wall_jump": 3.5, "high_jump": 2.15, "treadmill": 55.74},
        {"long_jump": -25, "wall_jump": 12, "high_jump": 15, "treadmill": 4},
        6, 8,
    ),
    (
        "Илон Маск Грейт Стар/Илон",
        {"long_jump": 2.5, "wall_jump": 3.5, "high_jump": 2.10, "treadmill": 37.60},
        {"long_jump": 6,  "wall_jump": 12, "high_jump": 12, "treadmill": 15},
        45, 5,
    ),
    (
        "Ram Pit Legion/Рам",
        {"long_jump": 0.0, "wall_jump": 4.1, "high_jump": 2.30, "treadmill": 43.82},
        {"long_jump": -25, "wall_jump": 25, "high_jump": 25, "treadmill": 10},
        35, 7,
    ),
    (
        "Brave Fighter's Pure Energy (Пуля)",
        {"long_jump": 5.8, "wall_jump": 3.7, "high_jump": 2.20, "treadmill": 33.49},
        {"long_jump": 25, "wall_jump": 20, "high_jump": 20, "treadmill": 20},
        85, 1,
    ),
]

# --- Группа XL (как раньше) ---
ATHLETES_XL = [
    (
        "Райан Winner View Ryan",
        {"long_jump": 4.7, "wall_jump": 3.4, "high_jump": 0.0, "treadmill": 0.0},
        {"long_jump": 12, "wall_jump": 12, "high_jump": -25, "treadmill": -25},
        -26, 6,
    ),
    (
        "Юкон-Рэд Пит Прайт (Кратос)",
        {"long_jump": 5.7, "wall_jump": 4.0, "high_jump": 2.25, "treadmill": 38.04},
        {"long_jump": 25, "wall_jump": 20, "high_jump": 20, "treadmill": 25},
        90, 1,
    ),
    (
        "Микрон-Рэд Пит Прайт (Медведь)",
        {"long_jump": 5.0, "wall_jump": 4.1, "high_jump": 2.40, "treadmill": 41.50},
        {"long_jump": 15, "wall_jump": 25, "high_jump": 25, "treadmill": 20},
        85, 2,
    ),
    (
        "Нейт/Альт",
        {"long_jump": 5.4, "wall_jump": 3.6, "high_jump": 2.20, "treadmill": 0.0},
        {"long_jump": 20, "wall_jump": 15, "high_jump": 15, "treadmill": -25},
        25, 5,
    ),
    (
        "Рональди-блу",
        {"long_jump": 4.4, "wall_jump": 3.6, "high_jump": 2.20, "treadmill": 48.33},
        {"long_jump": 10, "wall_jump": 15, "high_jump": 15, "treadmill": 15},
        55, 3,
    ),
    (
        "Аватар Де'Карон (Люцифер)",
        {"long_jump": 4.0, "wall_jump": 3.6, "high_jump": 2.00, "treadmill": 57.04},
        {"long_jump": 8,  "wall_jump": 15, "high_jump": 12, "treadmill": 12},
        47, 4,
    ),
]

# --- АСТ_S ---
ATHLETES_AST_S = [
    (
        "Goldy  Alvares Victory (Голди)",
        {"long_jump": 3.2, "wall_jump": 2.5, "high_jump": 165, "treadmill": 0},
        {"long_jump": 6,  "wall_jump": 8,  "high_jump": 12, "treadmill": -25},
        1, 7,
    ),
    (
        "DENVERS ELITE BETTER PICK ME - Шая",
        {"long_jump": 4.6, "wall_jump": 2.9, "high_jump": 1.9, "treadmill": 41.48},
        {"long_jump": 15, "wall_jump": 15, "high_jump": 25, "treadmill": 20},
        75, 2,
    ),
    (
        "Короли Ночной Вероны Глория (Ари)",
        {"long_jump": 3.8, "wall_jump": 2.8, "high_jump": 1.7, "treadmill": 0},
        {"long_jump": 10, "wall_jump": 12, "high_jump": 15, "treadmill": -25},
        12, 6,
    ),
    (
        "Денверс Элит Редмун ( Муня)",
        {"long_jump": 4.7, "wall_jump": 3.0, "high_jump": 1.9, "treadmill": 45.21},
        {"long_jump": 20, "wall_jump": 20, "high_jump": 25, "treadmill": 10},
        75, 2,
    ),
    (
        "Винчестер",
        {"long_jump": 3.8, "wall_jump": 2.5, "high_jump": 175, "treadmill": 43.55},
        {"long_jump": 10, "wall_jump": 8,  "high_jump": 20, "treadmill": 12},
        50, 5,
    ),
    (
        "Денверс Элит Шейп Май Импреза Соул/Бася",
        {"long_jump": 3.6, "wall_jump": 2.7, "high_jump": 150, "treadmill": 0},
        {"long_jump": 8,  "wall_jump": 10, "high_jump": 8,  "treadmill": -25},
        1, 7,
    ),
    (
        "Цевитта из королевства стафф (Витта)",
        {"long_jump": 4.4, "wall_jump": 3.1, "high_jump": 1.55, "treadmill": 38.54},
        {"long_jump": 12, "wall_jump": 25, "high_jump": 10,  "treadmill": 25},
        72, 4,
    ),
    (
        "Денверс Элит Амейзинг (Харли)",
        {"long_jump": 4.8, "wall_jump": 3.0, "high_jump": 1.9, "treadmill": 41.73},
        {"long_jump": 25, "wall_jump": 20, "high_jump": 25, "treadmill": 15},
        85, 1,
    ),
]

# --- АСТ_M ---
ATHLETES_AST_M = [
    (
        "Денверс Элит Цирцея / Цири",
        {"long_jump": 4.0, "wall_jump": 3.3, "high_jump": 180, "treadmill": 39.49},
        {"long_jump": 20, "wall_jump": 25, "high_jump": 20, "treadmill": 20},
        85, 1,
    ),
    (
        "Прайд Спартанис Тедерика/ Альма",
        {"long_jump": 3.8, "wall_jump": 2.7, "high_jump": 180, "treadmill": 41.61},
        {"long_jump": 15, "wall_jump": 15, "high_jump": 20, "treadmill": 12},
        62, 4,
    ),
    (
        "Рой (АСТ М)",
        {"long_jump": 4.5, "wall_jump": 2.6, "high_jump": 140, "treadmill": 38.91},
        {"long_jump": 25, "wall_jump": 12, "high_jump": 15, "treadmill": 25},
        77, 3,
    ),
    (
        "Tsenniy Prize Esclusivo (Мачо)",
        {"long_jump": 4.0, "wall_jump": 3.0, "high_jump": 2.0, "treadmill": 41.55},
        {"long_jump": 20, "wall_jump": 20, "high_jump": 25, "treadmill": 15},
        80, 2,
    ),
]

# --- АСТ_L ---
ATHLETES_AST_L = [
    (
        "Faiter For Fun / Джеки",
        {"long_jump": 3.9, "wall_jump": 3.0, "high_jump": 225, "treadmill": 50.03},
        {"long_jump": 20, "wall_jump": 20, "high_jump": 25, "treadmill": 20},
        85, 1,
    ),
    (
        "Вэста/Веста",
        {"long_jump": 4.5, "wall_jump": 2.7, "high_jump": 190, "treadmill": 50.11},
        {"long_jump": 25, "wall_jump": 15, "high_jump": 15, "treadmill": 15},
        70, 3,
    ),
    (
        "Юрген Райвел (Честер)",
        {"long_jump": 2.5, "wall_jump": 3.2, "high_jump": 2.0, "treadmill": 37.96},
        {"long_jump": 12, "wall_jump": 25, "high_jump": 20, "treadmill": 25},
        82, 2,
    ),
    (
        "Гром",
        {"long_jump": 2.8, "wall_jump": 2.7, "high_jump": 1.9, "treadmill": 0},
        {"long_jump": 15, "wall_jump": 15, "high_jump": 15, "treadmill": -25},
        20, 4,
    ),
]

# --- СБТ ---
ATHLETES_SBT = [
    (
        "Gambling Charm Scrappy Fella/ Стив",
        {"long_jump": 3.0, "wall_jump": 2.7, "high_jump": 155, "treadmill": 0},
        {"long_jump": 15, "wall_jump": 20, "high_jump": 15, "treadmill": -25},
        25, 5,
    ),
    (
        "Шайн Брайт (Бадди)",
        {"long_jump": 2.7, "wall_jump": 2.5, "high_jump": 155, "treadmill": 49.13},
        {"long_jump": 12, "wall_jump": 15, "high_jump": 15, "treadmill": 20},
        62, 2,
    ),
    (
        "West Galaxy Buorbon (Борик)",
        {"long_jump": 3.6, "wall_jump": 2.7, "high_jump": 165, "treadmill": 0},
        {"long_jump": 20, "wall_jump": 20, "high_jump": 20, "treadmill": -25},
        35, 4,
    ),
    (
        "Пайн форест бест Жетти (Шанти)",
        {"long_jump": 3.7, "wall_jump": 3.0, "high_jump": 170, "treadmill": 48.35},
        {"long_jump": 25, "wall_jump": 25, "high_jump": 25, "treadmill": 25},
        100, 1,
    ),
    (
        "Beso Del Toro Great Imperial / Бостон",
        {"long_jump": 2.7, "wall_jump": 1.8, "high_jump": 140, "treadmill": 60},
        {"long_jump": 12, "wall_jump": 12, "high_jump": 12, "treadmill": 15},
        51, 3,
    ),
]

# --- Малинуа ---
ATHLETES_MALINUA = [
    (
        "Виннер хунд Нирвана (Яра)",
        {"long_jump": 4.7, "wall_jump": 3.5, "high_jump": 210, "treadmill": 42.1},
        {"long_jump": 12, "wall_jump": 10, "high_jump": 8,  "treadmill": 10},
        40, 6,
    ),
    (
        "Виннер Хунд Опий / Опий",
        {"long_jump": 0, "wall_jump": 4.0, "high_jump": 2.45, "treadmill": 36.63},
        {"long_jump": -25, "wall_jump": 25, "high_jump": 20, "treadmill": 20},
        40, 6,
    ),
    (
        "Ченс оф Лайф Дарк Крокодайл/Кроки",
        {"long_jump": 5.6, "wall_jump": 3.7, "high_jump": 2.5, "treadmill": 40.47},
        {"long_jump": 20, "wall_jump": 15, "high_jump": 25, "treadmill": 12},
        72, 2,
    ),
    (
        "Alekster Hof Malandra  (Волга)",
        {"long_jump": 5.5, "wall_jump": 3.7, "high_jump": 2.4, "treadmill": 32.31},
        {"long_jump": 15, "wall_jump": 15, "high_jump": 15, "treadmill": 25},
        70, 3,
    ),
    (
        "Бранде Мали Габриела (Пума)",
        {"long_jump": 4.7, "wall_jump": 3.6, "high_jump": 2.35, "treadmill": 39.63},
        {"long_jump": 12, "wall_jump": 12, "high_jump": 12, "treadmill": 15},
        51, 4,
    ),
    (
        "Виннер хунд Эрсель",
        {"long_jump": 4.0, "wall_jump": 3.2, "high_jump": 1.9, "treadmill": 0},
        {"long_jump": 10, "wall_jump": 8,  "high_jump": 6,  "treadmill": -25},
        -1, 8,
    ),
    (
        "Франни Тейл Моретта / Руни",
        {"long_jump": 4.0, "wall_jump": 3.9, "high_jump": 230, "treadmill": 48.16},
        {"long_jump": 10, "wall_jump": 20, "high_jump": 10, "treadmill": 8},
        48, 5,
    ),
    (
        "Виннер Хунд Бастилия ( Баста)",
        {"long_jump": 6.0, "wall_jump": 3.9, "high_jump": 250, "treadmill": 58.25},
        {"long_jump": 25, "wall_jump": 20, "high_jump": 25, "treadmill": 6},
        76, 1,
    ),
]


# ====================== УТИЛИТЫ ======================

def _get_points_dict(ath):
    return {r.discipline.code: int(r.points) for r in ath.results.all()}


def _get(ath, code):
    return _get_points_dict(ath)[code]


# ====================== ТЕСТЫ ======================

@pytest.mark.parametrize(
    "name,results_in,points_expected,total_expected,_place",
    ATHLETES_S
    + ATHLETES_M
    + ATHLETES_L
    + ATHLETES_XL
    + ATHLETES_AST_S
    + ATHLETES_AST_M
    + ATHLETES_AST_L
    + ATHLETES_SBT
    + ATHLETES_MALINUA,
)
def test_all_categories_points_and_totals(event_with_disciplines, make_athlete_with_results,
                                          name, results_in, points_expected, total_expected, _place):
    """
    Универсальный тест:
    - проверяем очки по каждому снаряду (dense-ранжирование ВНУТРИ своей ростовой/породной группы),
    - проверяем общую сумму очков,
    - проверяем идемпотентность assign_growth_scores.
    """
    ev = event_with_disciplines["event"]

    # Загружаем всех участников всех групп
    group_map = [
        (ATHLETES_S, "S"),
        (ATHLETES_M, "M"),
        (ATHLETES_L, "L"),
        (ATHLETES_XL, "XL"),
        (ATHLETES_AST_S, "АСТ_S"),
        (ATHLETES_AST_M, "АСТ_M"),
        (ATHLETES_AST_L, "АСТ_L"),
        (ATHLETES_SBT, "СБТ"),
        (ATHLETES_MALINUA, "Малинуа"),
    ]

    for group, growth in group_map:
        for n, inp, *_ in group:
            make_athlete_with_results(
                n,
                growth=growth,
                long_jump=inp["long_jump"],
                wall_jump=inp["wall_jump"],
                high_jump=inp["high_jump"],
                treadmill=inp["treadmill"],
            )

    # Act
    assign_growth_scores(ev)
    assign_growth_scores(ev)  # идемпотентность

    # Assert
    ath = Athlete.objects.get(event=ev, name=name)
    points = _get_points_dict(ath)

    for code, pts in points_expected.items():
        assert code in points, f"{name}: нет результата для {code}"
        assert points[code] == pts, f"{name}: ожидали {pts} очков в {code}, получили {points[code]}"

    total = sum(points.values())
    assert total == total_expected, f"{name}: ожидали сумму {total_expected}, получили {total}"


def test_dense_ranking_with_ties_inside_group(event_with_disciplines, make_athlete_with_results):
    """
    Проверяем dense-ранжирование внутри ОДНОЙ ростовой группы (M) при ничьих:
    - long_jump: 5.50, 5.50, 5.20, 5.00  → очки 25, 25, 20, 15
    - treadmill: 35.00, 35.00, 36.00, 37.00 (меньше — лучше) → 25, 25, 20, 15
    """
    ev = event_with_disciplines["event"]

    a1 = make_athlete_with_results("A1", growth="M", long_jump=5.50, treadmill=35.00)
    a2 = make_athlete_with_results("A2", growth="M", long_jump=5.50, treadmill=35.00)
    a3 = make_athlete_with_results("A3", growth="M", long_jump=5.20, treadmill=36.00)
    a4 = make_athlete_with_results("A4", growth="M", long_jump=5.00, treadmill=37.00)

    assign_growth_scores(ev)

    assert _get(a1, "long_jump") == 25
    assert _get(a2, "long_jump") == 25
    assert _get(a3, "long_jump") == 20
    assert _get(a4, "long_jump") == 15

    assert _get(a1, "treadmill") == 25
    assert _get(a2, "treadmill") == 25
    assert _get(a3, "treadmill") == 20
    assert _get(a4, "treadmill") == 15


def test_zero_results_penalty_and_order(event_with_disciplines, make_athlete_with_results):
    """
    Нули/None:
      - получают штраф -25,
      - идут в конец,
      - не влияют на очки валидных результатов.
    Тестируем на группе S для wall_jump (больше лучше) и treadmill (меньше лучше).
    """
    ev = event_with_disciplines["event"]

    a_ok   = make_athlete_with_results("OK",   growth="S", wall_jump=330, treadmill=40.0)
    a_zero = make_athlete_with_results("ZERO", growth="S", wall_jump=0,   treadmill=0)
    a_none = make_athlete_with_results("NONE", growth="S", wall_jump=None, treadmill=None)

    assign_growth_scores(ev)

    assert _get(a_ok,   "wall_jump") == 25
    assert _get(a_zero, "wall_jump") == -25
    assert _get(a_none, "wall_jump") == -25

    assert _get(a_ok,   "treadmill") == 25
    assert _get(a_zero, "treadmill") == -25
    assert _get(a_none, "treadmill") == -25


def _dense_places(items):
    """
    items: list[(name, total_points)]
    Возвращает {name: place} по competition-ранжированию (1,2,2,4,...).
    Больше сумма — лучше.
    """
    items_sorted = sorted(items, key=lambda x: x[1], reverse=True)
    places = {}
    last_score = None
    place = 0       # текущее присваиваемое место
    idx = 0         # счётчик позиций (1..N)
    for name, score in items_sorted:
        idx += 1
        if score != last_score:
            place = idx   # у нового уникального результата место = текущий индекс
            last_score = score
        places[name] = place
    return places


def test_group_final_places(event_with_disciplines, make_athlete_with_results):
    """
    Проверяем ИТОГОВЫЕ места в группе: считаем суммарные очки по всем снарядам
    и ранжируем внутри каждой группы dense-методом. Сравниваем с _place из данных.
    """
    ev = event_with_disciplines["event"]

    group_map = [
        (ATHLETES_S, "S"),
        (ATHLETES_M, "M"),
        (ATHLETES_L, "L"),
        (ATHLETES_XL, "XL"),
        (ATHLETES_AST_S, "АСТ_S"),
        (ATHLETES_AST_M, "АСТ_M"),
        (ATHLETES_AST_L, "АСТ_L"),
        (ATHLETES_SBT, "СБТ"),
        (ATHLETES_MALINUA, "Малинуа"),
    ]

    # Создаём участников и копим ожидания мест
    expected_places_by_group = {}
    for data, group in group_map:
        exp = {}
        for name, _, __, ___, place in data:
            exp[name] = place
        expected_places_by_group[group] = exp

        for name, inp, *_ in data:
            make_athlete_with_results(
                name,
                growth=group,
                long_jump=inp["long_jump"],
                wall_jump=inp["wall_jump"],
                high_jump=inp["high_jump"],
                treadmill=inp["treadmill"],
            )

    assign_growth_scores(ev)

    # Считаем фактические суммы и места по группам
    from results.models import Athlete

    for data, group in group_map:
        athletes = Athlete.objects.filter(event=ev, growth_category=group).all()
        totals = []
        for a in athletes:
            s = sum(int(r.points) for r in a.results.all())
            totals.append((a.name, s))

        places = _dense_places(totals)

        # Проверяем ожидания для каждой записи в исходных данных группы
        for name, _, __, ___, expected_place in data:
            assert name in places, f"{group}: участник {name} не найден в расчёте мест"
            got = places[name]
            assert got == expected_place, (
                f"{group}: {name} — ожидали место {expected_place}, получили {got}. "
                f"Итоги группы: {sorted(totals, key=lambda x: x[1], reverse=True)}"
            )
