# results/views.py

from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Event, Athlete, DisciplineResult, GROWTH_GROUPS
from .forms import AthleteForm, DisciplineResultForm, EventForm, LoginForm
from .scoring import assign_growth_scores


def event_list(request):
    events = Event.objects.order_by('-date')
    return render(request, 'results/event_list.html', {'events': events})

def event_create(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            ev = form.save()
            return redirect('event_detail', event_id=ev.id)
    else:
        form = EventForm()
    return render(request, 'results/event_form.html', {'form': form, 'title': 'Создать событие'})

def event_edit(request, event_id):
    ev = get_object_or_404(Event, pk=event_id)
    if request.method == 'POST':
        form = EventForm(request.POST, instance=ev)
        if form.is_valid():
            form.save()
            return redirect('event_detail', event_id=ev.id)
    else:
        form = EventForm(instance=ev)
    return render(request, 'results/event_form.html', {'form': form, 'title': 'Редактировать событие'})

def event_detail(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    # --- обработка добавления спортсмена ---
    if request.method == 'POST' and 'add_athlete' in request.POST:
        a_form = AthleteForm(request.POST, prefix='ath')
        if a_form.is_valid():
            at = a_form.save(commit=False)
            at.event = event
            at.save()
            group_code = 'C' if at.is_champion else at.growth_category
            url = reverse('event_detail', args=[event.id])
            return redirect(f"{url}?group={group_code}#pane-{group_code}")
    else:
        a_form = AthleteForm(prefix='ath')

    # --- обработка добавления результата ---
    if request.method == 'POST' and 'add_result' in request.POST:
        r_form = DisciplineResultForm(request.POST, prefix='res', event=event)
        if r_form.is_valid():
            res = r_form.save(commit=False)
            res.athlete = r_form.cleaned_data['athlete']
            res.save()
            ath = res.athlete
            group_code = 'C' if ath.is_champion else ath.growth_category
            url = reverse('event_detail', args=[event.id])
            return redirect(f"{url}?group={group_code}#pane-{group_code}")
    else:
        r_form = DisciplineResultForm(prefix='res', event=event)

    assign_growth_scores(event)

    # соберём рейтинги: чемпионы, затем по ростовым
    all_ath = event.athletes.all()
    category_rankings = {}
    champs = sorted(all_ath.filter(is_champion=True), key=lambda x: x.total_points, reverse=True)
    if champs:
        category_rankings['C'] = ('Чемпионы', champs)
    for cat in GROWTH_GROUPS:
        lst = sorted(
            all_ath.filter(is_champion=False, growth_category=cat),
            key=lambda x: x.total_points, reverse=True
        )
        if lst:
            category_rankings[cat] = (cat, lst)

    # активная вкладка из query-параметра, иначе первая доступная
    active_group = request.GET.get('group')
    if active_group not in category_rankings:
        active_group = next(iter(category_rankings), None)

    return render(request, 'results/event_detail.html', {
        'event': event,
        'athlete_form': a_form,
        'result_form': r_form,
        'category_rankings': category_rankings,
        'active_group': active_group,   # <-- добавили
    })

def edit_result(request, event_id, pk):
    event = get_object_or_404(Event, pk=event_id)
    r = get_object_or_404(DisciplineResult, pk=pk, athlete__event=event)
    group_param = request.GET.get('group') or ('C' if r.athlete.is_champion else r.athlete.growth_category)

    if request.method == 'POST':
        form = DisciplineResultForm(request.POST, instance=r)
        if form.is_valid():
            form.save()
            url = reverse('event_detail', args=[event.id])
            return redirect(f"{url}?group={group_param}#pane-{group_param}")
    else:
        form = DisciplineResultForm(instance=r)
    return render(request, 'results/edit_result.html', {'event': event, 'form': form})

def delete_result(request, event_id, pk):
    event = get_object_or_404(Event, pk=event_id)
    r = get_object_or_404(DisciplineResult, pk=pk, athlete__event=event)
    group_param = request.GET.get('group') or ('C' if r.athlete.is_champion else r.athlete.growth_category)

    if request.method == 'POST':
        r.delete()
        url = reverse('event_detail', args=[event.id])
        return redirect(f"{url}?group={group_param}#pane-{group_param}")
    return render(request, 'results/confirm_delete.html', {'event': event, 'object': r})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('event_list')  # Замените на нужный URL после успешного входа
            else:
                form.add_error(None, "Неверное имя пользователя или пароль.")
    else:
        form = LoginForm()

    return render(request, 'auth/login.html', {'form': form})


def custom_logout(request):
    logout(request)
    return redirect('/')