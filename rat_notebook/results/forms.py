from django import forms
from django.core.exceptions import ValidationError
from .models import Athlete, DisciplineResult, Event


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
    'treadmill':    {'step': 0.01, 'min': 0,   'max': 60},  # секунды с сотыми
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
            # делаем таким же селектом, как у athlete в форме результатов
            'growth_category': forms.Select(attrs={'class': 'form-select'}),
            'is_champion': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'growth_category': 'Ростовая категория',
            'is_champion': 'Чемпион',
        }


# ---- Результат дисциплины ----
class DisciplineResultForm(forms.ModelForm):
    class Meta:
        model = DisciplineResult
        fields = ['athlete', 'discipline', 'result']
        widgets = {
            'athlete': forms.Select(attrs={
                'class': 'form-select'
            }),
            'discipline': forms.Select(attrs={
                'class': 'form-select'
            }),
            'result': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': 1,  # изменили шаг на 1
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

        def athlete_label(obj):
            cup = ' 🏆' if obj.is_champion else ''
            return f"{obj.name} ({obj.growth_category}){cup}"
        self.fields['athlete'].label_from_instance = athlete_label


    def clean_result(self):
        result     = self.cleaned_data.get('result')
        discipline = self.cleaned_data.get('discipline')

        if discipline and result is not None:
            rules = VALIDATION_RULES.get(discipline.code)
            if rules:
                mn, mx, step = rules['min'], rules['max'], rules['step']

                if not (mn <= result <= mx):
                    raise ValidationError(
                        f"Результат для «{discipline.verbose}» должен быть между {mn} и {mx}."
                    )

                rem = (result - mn) / step
                if abs(round(rem) - rem) > 1e-6:
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
