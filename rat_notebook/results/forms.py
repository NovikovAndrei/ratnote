from django import forms
from django.core.exceptions import ValidationError
from .models import Athlete, DisciplineResult, Event
from django.forms import inlineformset_factory
from django.forms.widgets import Select
from .models import PuppyTrainingSession, PuppyTrainingExercise, Exercise


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, label="Имя пользователя")
    password = forms.CharField(widget=forms.PasswordInput, label="Пароль")


# ---- Правила валидации результатов ----
VALIDATION_RULES = {
    'long_jump':    {'step': 10,   'min': 0,   'max': 800},
    'wall_jump':    {'step': 10,   'min': 0,   'max': 500},
    'high_jump':    {'step': 5,    'min': 0,   'max': 270},
    'barrier_jump': {'step': 5,    'min': 0,   'max': 180},
    'a_frame':      {'step': 1,    'min': 0,   'max': 80},
    'treadmill':    {'step': 0.01, 'min': 0,   'max': 120},  # секунды с сотыми
}


# ---- Спортсмен ----
class AthleteForm(forms.ModelForm):
    class Meta:
        model = Athlete
        fields = ['name', 'growth_category', 'is_champion']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Имя спортсмена'
            }),
            'growth_category': forms.Select(attrs={'class': 'form-select'}),
            'is_champion': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'growth_category': 'Ростовая категория',
            'is_champion': 'Чемпион:',
        }

    def __init__(self, *args, **kwargs):
        # получим event из вьюхи (передадим ниже)
        self.event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)
        self.label_suffix = ''  # убираем автоматическое двоеточие Django

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            return name
        name = name.strip()

        # выясняем событие: при создании — из self.event, при редактировании — из instance.event
        event = self.event or (self.instance.event if self.instance and self.instance.pk else None)
        if event:
            qs = Athlete.objects.filter(event=event, name=name)
            # если редактирование — исключаем самого себя
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('Спортсмен с таким именем уже существует в этом событии.')
        return name


# ---- Результат дисциплины ----
class DisciplineResultForm(forms.ModelForm):
    class Meta:
        model = DisciplineResult
        fields = ['athlete', 'discipline', 'result']
        widgets = {
            'athlete': forms.Select(attrs={'class': 'form-select'}),
            'discipline': forms.Select(attrs={'class': 'form-select'}),
            # result на старте — базовый, значения min/max/step будут перезаписаны в __init__
            'result': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Результат'
            }),
        }
        labels = {
            'athlete': 'Выберите спортсмена',
            'discipline': 'Выберите дисциплину',
            'result': 'Результат'
        }

    def __init__(self, *args, event=None, **kwargs):
        super().__init__(*args, **kwargs)

        if event is not None:
            self.fields['athlete'].queryset = event.athletes.order_by('name')
            self.fields['discipline'].queryset = event.disciplines.all()

        # красивое отображение спортсмена
        def athlete_label(obj):
            cup = ' 🏆' if obj.is_champion else ''
            return f"{obj.name} ({obj.growth_category}){cup}"
        self.fields['athlete'].label_from_instance = athlete_label

        # если дисциплина уже выбрана (редактирование результата) → подставляем step/min/max
        discipline = self.initial.get('discipline') or self.data.get('discipline')
        if discipline:
            try:
                # discipline может быть объектом или кодом
                if hasattr(discipline, 'code'):
                    code = discipline.code
                else:
                    # Получаем объект дисциплины по id
                    disc_obj = self.fields['discipline'].queryset.get(pk=discipline)
                    code = disc_obj.code
                rules = VALIDATION_RULES.get(code)
                if rules:
                    self.fields['result'].widget.attrs.update({
                        'step': rules['step'],
                        'min': rules['min'],
                        'max': rules['max'],
                    })
            except Exception:
                pass

    def clean_result(self):
        result = self.cleaned_data.get('result')
        discipline = self.cleaned_data.get('discipline')

        if discipline and result is not None:
            rules = VALIDATION_RULES.get(discipline.code)
            if rules:
                mn, mx, step = rules['min'], rules['max'], rules['step']

                if not (mn <= result <= mx):
                    raise ValidationError(
                        f"Результат для «{discipline.verbose}» должен быть между {mn} и {mx}."
                    )

                # проверка кратности шагу
                rem = (result - mn) / step
                if abs(round(rem) - rem) > 1e-9:
                    raise ValidationError(
                        f"Результат для «{discipline.verbose}» должен быть кратен {step}."
                    )
        return result


# ---- Событие ----
class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'date', 'disciplines']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'disciplines': forms.CheckboxSelectMultiple(),
        }
        labels = {
            'name': 'Название события',
            'date': 'Дата события',
            'disciplines': 'Дисциплины',
        }


class PuppyTrainingSessionForm(forms.ModelForm):
    class Meta:
        model = PuppyTrainingSession
        fields = ["date", "start_time", "end_time", "notes"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "start_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "end_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")
        if start and end and end <= start:
            raise forms.ValidationError("Время конца должно быть позже времени начала.")
        return cleaned


class ExerciseSelect(Select):
    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )

        # value может быть '', ModelChoiceIteratorValue или id
        ex_id = getattr(value, "value", value)
        try:
            ex_id = int(ex_id)
        except (TypeError, ValueError):
            return option

        ex = self.choices.queryset.filter(pk=ex_id).only("default_reps").first()
        if ex and ex.default_reps is not None:
            option["attrs"]["data-default-reps"] = str(ex.default_reps)

        return option


class PuppyTrainingExerciseForm(forms.ModelForm):
    class Meta:
        model = PuppyTrainingExercise
        fields = ["exercise", "planned_reps", "actual_reps", "pros", "cons"]
        widgets = {
            "planned_reps": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "actual_reps": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "pros": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "cons": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["exercise"].queryset = Exercise.objects.order_by("name")
        self.fields["exercise"].empty_label = "выбери упражнение"

        # чтобы было как bootstrap select
        cls = self.fields["exercise"].widget.attrs.get("class", "")
        self.fields["exercise"].widget.attrs["class"] = (cls + " form-select js-exercise-select").strip()


PuppyTrainingExerciseCreateFormSet = inlineformset_factory(
    parent_model=PuppyTrainingSession,
    model=PuppyTrainingExercise,
    form=PuppyTrainingExerciseForm,
    extra=1,           # на создании пусть будет 1 пустая строка
    can_delete=False,  # чекбокс удаления нам не нужен
)

PuppyTrainingExerciseEditFormSet = inlineformset_factory(
    parent_model=PuppyTrainingSession,
    model=PuppyTrainingExercise,
    form=PuppyTrainingExerciseForm,
    extra=0,           # на редактировании НЕ показываем пустую строку
    can_delete=True,
)


class ExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = ["name", "description", "default_reps"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "default_reps": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }
