# -*- coding: utf-8 -*-
from math import floor
from typing import Dict, Iterable, List, Optional, Tuple

# Нормативы по ростовым категориям для чемпионов
# treadmill — в секундах (например, 25.20 = 25.20 сек)
QUALIFYING_NORMS = {
    'XS':      {'wall_jump': 280, 'high_jump': 180, 'long_jump': 400, 'barrier_jump':  90, 'a_frame': 28, 'treadmill': 48.00},
    'S':       {'wall_jump': 310, 'high_jump': 195, 'long_jump': 490, 'barrier_jump': 105, 'a_frame': 30, 'treadmill': 46.00},
    'M':       {'wall_jump': 330, 'high_jump': 205, 'long_jump': 510, 'barrier_jump': 115, 'a_frame': 32, 'treadmill': 44.00},
    'L':       {'wall_jump': 350, 'high_jump': 215, 'long_jump': 530, 'barrier_jump': 125, 'a_frame': 34, 'treadmill': 42.00},
    'XL':      {'wall_jump': 370, 'high_jump': 225, 'long_jump': 550, 'barrier_jump': 125, 'a_frame': 34, 'treadmill': 42.00},
    'АСТ_S':   {'wall_jump': 310, 'high_jump': 190, 'long_jump': 450, 'barrier_jump': 100, 'a_frame': 32, 'treadmill': 44.00},
    'АСТ_M':   {'wall_jump': 320, 'high_jump': 200, 'long_jump': 470, 'barrier_jump': 105, 'a_frame': 32, 'treadmill': 44.00},
    'АСТ_L':   {'wall_jump': 330, 'high_jump': 210, 'long_jump': 490, 'barrier_jump': 110, 'a_frame': 32, 'treadmill': 44.00},
    'СБТ':     {'wall_jump': 270, 'high_jump': 165, 'long_jump': 370, 'barrier_jump':  85, 'a_frame': 28, 'treadmill': 50.00},
    'Малинуа': {'wall_jump': 370, 'high_jump': 230, 'long_jump': 530, 'barrier_jump': 130, 'a_frame': 36, 'treadmill': 42.00},
}

# Порог/шаги прироста «от нормы» для чемпионов
STEP_CONFIG = {
    'long_jump':    {'step_size': 10,   'points_per_step': 1},  # +1 балл за каждые полные 10 см сверх нормы
    'wall_jump':    {'step_size': 10,   'points_per_step': 3},  # +3 балла за каждые полные 10 см
    'high_jump':    {'step_size': 5,    'points_per_step': 3},  # +3 балла за каждые полные 5 см
    'barrier_jump': {'step_size': 5,    'points_per_step': 3},
    'a_frame':      {'step_size': 1,    'points_per_step': 1},
    # treadmill: +1 балл за каждые ПОЛНЫЕ 2 секунды улучшения относительно нормы
    'treadmill':    {'step_size': 2.0,  'points_per_step': 1},
}

# Очки за места (dense-ранжирование), до 10-го
RANK_POINTS = [25, 20, 15, 12, 10, 8, 6, 4, 2, 1]

# Ростовые группы (используются для «негероев», т.е. is_champion=False)
GROWTH_GROUPS = ['XS', 'S', 'M', 'L', 'XL', 'АСТ_S', 'АСТ_M', 'АСТ_L', 'СБТ', 'Малинуа']


def _full_steps(delta: float, step: float) -> int:
    """
    Кол-во ПОЛНЫХ шагов без артефактов float.
    Например: delta=3.999999, step=2.0 -> 1 (а не 0).
    """
    if delta is None or step is None or delta <= 0 or step <= 0:
        return 0
    eps = 1e-9
    return floor((delta + eps) / step)


def calculate_champion_points(category: str, discipline: str, result: Optional[float]) -> int:
    """
    Начисление очков «чемпионам» по нормативам для их категории.
    Для treadmill — меньше это лучше; остальные — больше лучше.
    """
    norms = QUALIFYING_NORMS.get(category)
    cfg = STEP_CONFIG.get(discipline)
    if norms is None or cfg is None:
        return 0

    norm = norms.get(discipline)
    if norm is None:
        return 0

    # штраф за отсутствие результата
    if result is None or result == 0:
        return -10

    if discipline == 'treadmill':
        # Ограничение на «слишком долго»
        if result > 60:
            return -10
        # Норму не выполнил (медленнее нормы)
        if result > norm:
            return 0
        delta = norm - result  # улучшение в секундах
    else:
        # Норму не выполнил (меньше нормы в см/см/…)
        if result < norm:
            return 0
        delta = result - norm

    steps = _full_steps(delta, cfg['step_size'])
    return 10 + steps * cfg['points_per_step']


def assign_growth_scores(event):
    """
    Начисление очков для НЕ чемпионов (is_champion=False) по ростовым группам.
    Ранжирование выполняется ВНУТРИ КАЖДОЙ ростовой группы по каждой дисциплине.
    Правила:
      * treadmill — меньше лучше; 0/None в конец; dense-ранжирование; очки по RANK_POINTS; ноль = -25
      * остальные — больше лучше; 0/None в конец; dense-ранжирование; очки по RANK_POINTS; ноль = -25
    Функция идемпотентна: повторный вызов не изменит правильно расставленные очки.
    """
    from .models import DisciplineResult  # локальный импорт, чтобы избежать циклов

    for discipline in event.disciplines.all():
        is_time = (discipline.code == 'treadmill')

        for group in GROWTH_GROUPS:
            qs = DisciplineResult.objects.filter(
                athlete__event=event,
                athlete__is_champion=False,
                athlete__growth_category=group,
                discipline=discipline
            )

            items = list(qs)
            if not items:
                continue

            if is_time:
                # Меньше — лучше; 0/None в конец
                def sort_key(r):
                    v = r.result or 0
                    return (v <= 0, v)
                sorted_results = sorted(items, key=sort_key)
            else:
                # Больше — лучше; 0/None в конец
                sorted_results = sorted(items, key=lambda r: (r.result or 0), reverse=True)

            # Dense-ранжирование по уникальным значениям result (с учётом 0-значений)
            rank = 1
            i = 0
            n = len(sorted_results)
            while i < n:
                base_val = (sorted_results[i].result or 0)
                same_bucket = [sorted_results[i]]
                j = i + 1
                while j < n and (sorted_results[j].result or 0) == base_val:
                    same_bucket.append(sorted_results[j])
                    j += 1

                if base_val == 0:
                    pts = -25
                else:
                    pts = RANK_POINTS[rank - 1] if rank <= len(RANK_POINTS) else 0

                # Обновляем только если есть изменения — ускоряет идемпотентный повтор
                for r in same_bucket:
                    if r.points != pts:
                        r.points = pts
                        r.save(update_fields=['points'])

                rank += 1
                i = j


def calculate_points(category: str, discipline: str, result: Optional[float]) -> int:
    """
    Обёртка: чемпионы получают очки по нормативам,
    ростовые группы — через assign_growth_scores (здесь 0, т.к. они расставляются ранжированием).
    """
    if category in GROWTH_GROUPS:
        return 0
    return calculate_champion_points(category, discipline, result)


def _competition_rank(pairs: Iterable[Tuple[object, int]]) -> List[Tuple[object, int, int]]:
    """
    Присваивает места по competition-ранжированию (1,2,2,4,5,...).

    pairs: iterable из (obj, score), отсортированных по score по убыванию.
    Возвращает список (obj, score, place) в том же порядке.
    """
    ranked = []
    last_score: Optional[int] = None
    place = 0
    idx = 0
    for obj, score in pairs:
        idx += 1
        if score != last_score:
            place = idx
            last_score = score
        ranked.append((obj, score, place))
    return ranked


def compute_final_places(
    event,
    groups: Optional[Iterable[str]] = None,
    include_champions: bool = False,
) -> Dict[str, List[dict]]:
    """
    Считает ИТОГОВЫЕ места по сумме очков внутри каждой ростовой группы
    по правилу competition ranking (1,2,2,4,...).

    Аргументы:
      - event: объект Event
      - groups: какие группы учитывать; по умолчанию все из GROWTH_GROUPS
      - include_champions: включать ли чемпионов (is_champion=True).
        По умолчанию False — считаем только ростовые (is_champion=False).

    Возвращает:
      {
        "<group_code>": [
           {
             "athlete": <Athlete>,
             "total_points": <int>,
             "place": <int>,
             "results": <QuerySet[DisciplineResult]>,  # для детализации на фронте
           },
           ...
        ],
        ...
      }
    """
    from .models import Athlete  # локальный импорт, чтобы избежать циклов

    group_codes = list(groups) if groups is not None else list(GROWTH_GROUPS)
    out: Dict[str, List[dict]] = {}

    for g in group_codes:
        qs = Athlete.objects.filter(event=event, growth_category=g)
        if not include_champions:
            qs = qs.filter(is_champion=False)

        athletes = list(qs.prefetch_related("results", "results__discipline"))
        # Собираем пары (athlete, total)
        pairs: List[Tuple[object, int]] = []
        for a in athletes:
            total = sum(int(r.points or 0) for r in a.results.all())
            pairs.append((a, total))

        # Стабильная сортировка: по сумме очков ↓, затем по имени ↑ — чтобы детерминировать порядок при полном равенстве
        pairs.sort(key=lambda p: (p[1], p[0].name), reverse=True)

        ranked = _competition_rank(pairs)

        group_rows: List[dict] = []
        for a, total, place in ranked:
            group_rows.append({
                "athlete": a,
                "total_points": total,
                "place": place,
                "results": a.results.all(),
            })
        out[g] = group_rows

    return out
