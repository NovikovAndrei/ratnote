# нормативы по ростовым категориям (для чемпионов)
QUALIFYING_NORMS = {
    'XS': {'wall_jump': 280, 'high_jump': 180, 'long_jump': 400, 'barrier_jump': 90, 'a_frame': 28, 'treadmill': 0.48},
    'S': {'wall_jump': 310, 'high_jump': 195, 'long_jump': 490, 'barrier_jump': 105, 'a_frame': 30, 'treadmill': 0.46},
    'M': {'wall_jump': 330, 'high_jump': 205, 'long_jump': 510, 'barrier_jump': 115, 'a_frame': 32, 'treadmill': 0.44},
    'L': {'wall_jump': 350, 'high_jump': 215, 'long_jump': 530, 'barrier_jump': 125, 'a_frame': 34, 'treadmill': 0.42},
    'XL': {'wall_jump': 370, 'high_jump': 225, 'long_jump': 550, 'barrier_jump': 125, 'a_frame': 34, 'treadmill': 0.42},
    'АСТ_S': {'wall_jump': 310, 'high_jump': 190, 'long_jump': 450, 'barrier_jump': 100, 'a_frame': 32,
              'treadmill': 0.44},
    'АСТ_M': {'wall_jump': 320, 'high_jump': 200, 'long_jump': 470, 'barrier_jump': 105, 'a_frame': 32,
              'treadmill': 0.44},
    'АСТ_L': {'wall_jump': 330, 'high_jump': 210, 'long_jump': 490, 'barrier_jump': 110, 'a_frame': 32,
              'treadmill': 0.44},
    'СБТ': {'wall_jump': 270, 'high_jump': 165, 'long_jump': 370, 'barrier_jump': 85, 'a_frame': 28, 'treadmill': 0.50},
    'Малинуа': {'wall_jump': 370, 'high_jump': 230, 'long_jump': 530, 'barrier_jump': 130, 'a_frame': 36,
                'treadmill': 0.42},
}

STEP_CONFIG = {
    'long_jump': {'step_size': 10, 'points_per_step': 1},
    'wall_jump': {'step_size': 10, 'points_per_step': 3},
    'high_jump': {'step_size': 5, 'points_per_step': 3},
    'barrier_jump': {'step_size': 5, 'points_per_step': 3},
    'a_frame': {'step_size': 1, 'points_per_step': 1},
    'treadmill': {'step_size': 2, 'points_per_step': 1},
}

RANK_POINTS = [25, 20, 15, 12, 10, 8, 6, 4, 2, 1]

# ростовые группы (используются в assign_growth_scores)
GROWTH_GROUPS = ['XS', 'S', 'M', 'L', 'XL', 'АСТ_S', 'АСТ_M', 'АСТ_L', 'СБТ', 'Малинуа']


def calculate_champion_points(category: str, discipline: str, result: float) -> int:
    norms = QUALIFYING_NORMS.get(category)
    config = STEP_CONFIG.get(discipline)
    if norms is None or config is None:
        return 0
    norm = norms[discipline]
    # штраф за 0 или None
    if result is None or result == 0:
        return -10
    if discipline == 'treadmill':
        if result > norm:
            return 0
        delta = norm - result
    else:
        if result < norm:
            return 0
        delta = result - norm

    steps = int(delta // config['step_size'])
    return 10 + steps * config['points_per_step']


def assign_growth_scores(event):
    """
    Для каждого discipline в событии:
     – выбираем только ростовые группы (is_champion=False)
     – сортируем по результату (None/0 -> 0)
     – даём по dense-ранжированию: при ничьей оба получают один и тот же place,
       а следующий спортсмен получает place+1.
     – до 10-го места очки из RANK_POINTS, нулевые результаты штраф –25.
    """
    from .models import DisciplineResult

    for discipline in event.disciplines.all():
        qs = DisciplineResult.objects.filter(
            athlete__event=event,
            athlete__is_champion=False,
            athlete__growth_category__in=GROWTH_GROUPS,
            discipline=discipline
        )
        # сортируем по результату (None/0 -> 0), по убыванию
        sorted_results = sorted(qs, key=lambda r: r.result or 0, reverse=True)

        rank = 1
        i = 0
        while i < len(sorted_results):
            # собираем всех с одинаковым результатом
            same = [sorted_results[i]]
            j = i + 1
            while j < len(sorted_results) and (sorted_results[j].result or 0) == (sorted_results[i].result or 0):
                same.append(sorted_results[j])
                j += 1

            # определяем очки: либо штраф, либо по списку RANK_POINTS
            res_val = (sorted_results[i].result or 0)
            if res_val == 0:
                pts = -25
            else:
                pts = RANK_POINTS[rank - 1] if rank <= len(RANK_POINTS) else 0

            # сохраняем
            for r in same:
                r.points = pts
                r.save()

            # переходим к следующему рангу (dense ranking!)
            rank += 1
            i = j


def calculate_points(category: str, discipline: str, result: float) -> int:
    """
    Чемпионы получают баллы по нормативам,
    ростовые группы — через assign_growth_scores (здесь просто 0).
    """
    if category in GROWTH_GROUPS:
        return 0
    return calculate_champion_points(category, discipline, result)
