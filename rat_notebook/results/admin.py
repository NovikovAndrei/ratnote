# results/admin.py

from django.contrib import admin
from .models import Event, DisciplineType, Athlete, DisciplineResult, PuppyTrainingSession, PuppyTrainingExercise


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date')
    filter_horizontal = ('disciplines',)
    search_fields = ('name',)


@admin.register(DisciplineType)
class DisciplineTypeAdmin(admin.ModelAdmin):
    list_display = ('verbose', 'code')
    search_fields = ('verbose', 'code')


@admin.register(Athlete)
class AthleteAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'growth_category', 'is_champion', 'total_points')
    list_filter = ('event', 'growth_category', 'is_champion')
    search_fields = ('name',)


@admin.register(DisciplineResult)
class DisciplineResultAdmin(admin.ModelAdmin):
    list_display = ('athlete', 'discipline', 'result', 'points')
    list_filter = ('discipline', 'athlete__event')
    search_fields = ('athlete__name',)


class PuppyTrainingExerciseInline(admin.TabularInline):
    model = PuppyTrainingExercise
    extra = 0


@admin.register(PuppyTrainingSession)
class PuppyTrainingSessionAdmin(admin.ModelAdmin):
    list_display = ("date", "start_time", "end_time", "notes")
    list_filter = ("date",)
    inlines = [PuppyTrainingExerciseInline]
