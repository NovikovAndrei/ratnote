# results/admin.py

from django.contrib import admin
from .models import (
    Event, DisciplineType, Athlete, DisciplineResult,
    PuppyTrainingSession, PuppyTrainingExercise, Exercise, Puppy,
    Dog, EventDog, EventDogResult,
    QualificationNormSet, QualificationNorm,
)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'is_legacy', 'norm_set')
    list_filter = ('is_legacy', 'date', 'norm_set')
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


@admin.register(Dog)
class DogAdmin(admin.ModelAdmin):
    list_display = ('name', 'growth_category', 'is_champion')
    list_filter = ('growth_category', 'is_champion')
    search_fields = ('name',)


@admin.register(EventDog)
class EventDogAdmin(admin.ModelAdmin):
    list_display = ('dog', 'event', 'growth_category', 'is_champion', 'total_points')
    list_filter = ('event', 'growth_category', 'is_champion')
    search_fields = ('dog__name', 'event__name')


@admin.register(EventDogResult)
class EventDogResultAdmin(admin.ModelAdmin):
    list_display = ('event_dog', 'discipline', 'result', 'points')
    list_filter = ('discipline', 'event_dog__event')
    search_fields = ('event_dog__dog__name', 'event_dog__event__name')


class QualificationNormInline(admin.TabularInline):
    model = QualificationNorm
    extra = 0


@admin.register(QualificationNormSet)
class QualificationNormSetAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    inlines = [QualificationNormInline]


@admin.register(QualificationNorm)
class QualificationNormAdmin(admin.ModelAdmin):
    list_display = ('norm_set', 'growth_category', 'discipline', 'value')
    list_filter = ('norm_set', 'growth_category', 'discipline')
    search_fields = ('growth_category', 'discipline__code', 'discipline__verbose')


class PuppyTrainingExerciseInline(admin.TabularInline):
    model = PuppyTrainingExercise
    extra = 0


@admin.register(PuppyTrainingSession)
class PuppyTrainingSessionAdmin(admin.ModelAdmin):
    list_display = ("date", "start_time", "end_time", "notes")
    list_filter = ("date",)
    inlines = [PuppyTrainingExerciseInline]


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("name", "default_reps", "created_at")
    search_fields = ("name",)


@admin.register(Puppy)
class PuppyAdmin(admin.ModelAdmin):
    list_display = ("pet_name", "registered_name", "sex", "birth_date")
    search_fields = ("pet_name", "registered_name")
    list_filter = ("sex",)
