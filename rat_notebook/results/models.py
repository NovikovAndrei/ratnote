from django.db import models
from .scoring import GROWTH_GROUPS, calculate_champion_points

# ростовые категории
GROWTH_CHOICES = [(c, c) for c in GROWTH_GROUPS]


class Event(models.Model):
    name = models.CharField("Название события", max_length=200)
    date = models.DateField("Дата события")
    disciplines = models.ManyToManyField("DisciplineType", verbose_name="Дисциплины")

    class Meta:
        verbose_name = "Событие"
        verbose_name_plural = "События"

    def __str__(self):
        return f"{self.name} ({self.date})"


class DisciplineType(models.Model):
    code = models.CharField("Код дисциплины", max_length=50, choices=[
        ("long_jump", "Прыжок в длину"),
        ("wall_jump", "Стена"),
        ("high_jump", "Б/О прыжок"),
        ("barrier_jump", "Барьер"),
        ("a_frame", "A-фрейм"),
        ("treadmill", "Дорожка (300 м)"),
    ], unique=True)
    verbose = models.CharField("Название дисциплины", max_length=100)

    class Meta:
        verbose_name = "Тип дисциплины"
        verbose_name_plural = "Типы дисциплин"
        ordering = ["verbose"]

    def __str__(self):
        return self.verbose


class Athlete(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="athletes")
    name = models.CharField("Имя спортсмена", max_length=100)
    growth_category = models.CharField("Ростовая категория", max_length=12,
                                       choices=GROWTH_CHOICES, default="XS", blank=True, null=True)
    is_champion = models.BooleanField("Чемпион", default=False)

    class Meta:
        verbose_name = "Спортсмен"
        verbose_name_plural = "Спортсмены"
        unique_together = ("event", "name")

    def __str__(self):
        return f"{self.name} ({self.event.name})"

    @property
    def total_points(self):
        return sum(r.points for r in self.results.all())


class DisciplineResult(models.Model):
    athlete = models.ForeignKey(Athlete, on_delete=models.CASCADE, related_name="results")
    discipline = models.ForeignKey(DisciplineType, on_delete=models.PROTECT)
    result = models.FloatField("Результат", null=True, blank=True)
    points = models.FloatField("Очки", editable=False)

    class Meta:
        verbose_name = "Результат дисциплины"
        verbose_name_plural = "Результаты дисциплин"
        unique_together = ("athlete", "discipline")

    def save(self, *args, **kwargs):
        if self.athlete.is_champion:
            # начисляем сразу нормативы по ростовой группе чемпиона
            self.points = calculate_champion_points(
                self.athlete.growth_category,
                self.discipline.code,
                self.result
            )
        else:
            # ростовые группы: сначала 0, потом assign_growth_scores обновит
            if self.pk is None:
                self.points = 0
            # при повторном save (после assign_growth_scores) points не меняется
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.athlete.name}: {self.discipline.verbose} — {self.points} очков"


class PuppyTrainingSession(models.Model):
    date = models.DateField("Дата",db_index=True)
    start_time = models.TimeField("Время начала")
    end_time = models.TimeField("Время конца")
    notes = models.TextField("Заметка к тренировке", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-start_time", "-id"]

    def __str__(self):
        return f"{self.date} {self.start_time}-{self.end_time}"


class PuppyTrainingExercise(models.Model):
    session = models.ForeignKey(
        PuppyTrainingSession,
        on_delete=models.CASCADE,
        related_name="exercises",
    )

    exercise = models.CharField("Упражнение", max_length=200)
    planned_reps = models.PositiveIntegerField("План (повторения)")
    actual_reps = models.PositiveIntegerField("Факт (повторения)")
    pros = models.TextField("Плюсы", blank=True)
    cons = models.TextField("Минусы", blank=True)

    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return self.exercise

    def save(self, *args, **kwargs):
        if not self.position:
            max_pos = (
                PuppyTrainingExercise.objects
                .filter(session_id=self.session_id)
                .aggregate(m=models.Max("position"))
                .get("m")
            ) or 0
            self.position = max_pos + 1
        super().save(*args, **kwargs)
