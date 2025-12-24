import json
from datetime import date as dt_date
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db import transaction
from django.utils.dateparse import parse_date
from .models import Event, DisciplineResult, PuppyTrainingSession, PuppyTrainingExercise
from .forms import AthleteForm, DisciplineResultForm, EventForm, LoginForm, PuppyTrainingSessionForm, \
    PuppyTrainingExerciseCreateFormSet, PuppyTrainingExerciseEditFormSet
from .scoring import assign_growth_scores, compute_final_places


@login_required
@permission_required('results.view_event', raise_exception=True)
def event_list(request):
    events = Event.objects.order_by('-date')
    return render(request, 'results/event_list.html', {'events': events})


@login_required
@permission_required('results.add_event', raise_exception=True)
def event_create(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            ev = form.save()
            return redirect('event_detail', event_id=ev.id)
    else:
        form = EventForm()
    return render(request, 'results/event_form.html', {'form': form, 'title': 'Создать событие'})


@login_required
@permission_required('results.change_event', raise_exception=True)
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


@login_required
@permission_required('results.view_event', raise_exception=True)   # <— только право на просмотр страницы
def event_detail(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    # --- добавление спортсмена — требуем явное право add_athlete
    if request.method == 'POST' and 'add_athlete' in request.POST:
        if not request.user.has_perm('results.add_athlete'):
            return HttpResponseForbidden('Недостаточно прав')
        a_form = AthleteForm(request.POST, prefix='ath', event=event)
        if a_form.is_valid():
            at = a_form.save(commit=False)
            at.event = event
            at.save()
            group_code = 'C' if at.is_champion else at.growth_category
            url = reverse('event_detail', args=[event.id])
            return redirect(f"{url}?group={group_code}#pane-{group_code}")
    else:
        a_form = AthleteForm(prefix='ath', event=event)

    # --- добавление результата — требуем право add_disciplineresult
    if request.method == 'POST' and 'add_result' in request.POST:
        if not request.user.has_perm('results.add_disciplineresult'):
            return HttpResponseForbidden('Недостаточно прав')
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

    # Пересчёт очков по снарядам (идемпотентен)
    assign_growth_scores(event)

    # Готовим таблицы мест по competition внутри ростовых/породных групп
    standings = compute_final_places(event, include_champions=False)

    category_rankings = {}

    # Чемпионы
    champs_qs = (
        event.athletes.filter(is_champion=True)
        .prefetch_related("results", "results__discipline")
    )
    if champs_qs.exists():
        champs = []
        for a in champs_qs:
            total = sum(int(r.points or 0) for r in a.results.all())
            champs.append((a, total))

        champs.sort(key=lambda p: (p[1], p[0].name), reverse=True)

        last = None
        place = 0
        idx = 0
        champs_rows = []
        for a, total in champs:
            idx += 1
            if total != last:
                place = idx
                last = total
            setattr(a, "place", place)  # ← только place
            champs_rows.append(a)

        category_rankings["C"] = ("Чемпионы", champs_rows)

    # Ростовые/породные группы
    for code, rows in standings.items():
        lst = []
        for row in rows:
            a = row["athlete"]
            setattr(a, "place", row["place"])  # ← только place
            lst.append(a)
        if lst:
            category_rankings[code] = (code, lst)


    # Какая вкладка активна
    active_group = request.GET.get("group")
    if active_group not in category_rankings:
        active_group = next(iter(category_rankings), None)

    return render(request, "results/event_detail.html", {
        "event": event,
        "athlete_form": a_form,
        "result_form": r_form,
        "category_rankings": category_rankings,
        "active_group": active_group,
    })


@login_required
@permission_required('results.change_disciplineresult', raise_exception=True)
def edit_result(request, event_id, pk):
    event = get_object_or_404(Event, pk=event_id)
    r = get_object_or_404(DisciplineResult, pk=pk, athlete__event=event)
    group_param = request.GET.get('group') or ('C' if r.athlete.is_champion else r.athlete.growth_category)

    if request.method == 'POST':
        form = DisciplineResultForm(request.POST, instance=r, event=event)
        # визуально заблокированы — но главное, ниже жёстко фиксируем
        form.fields['athlete'].disabled = True
        form.fields['discipline'].disabled = True

        if form.is_valid():
            obj = form.save(commit=False)
            # серверная защита: не позволяем сменить спортсмена/дисциплину
            obj.athlete_id = r.athlete_id
            obj.discipline_id = r.discipline_id
            obj.save()
            url = reverse('event_detail', args=[event.id])
            return redirect(f"{url}?group={group_param}#pane-{group_param}")
    else:
        form = DisciplineResultForm(instance=r, event=event)
        # в UI селекты неактивны
        form.fields['athlete'].disabled = True
        form.fields['discipline'].disabled = True

    return render(request, 'results/edit_result.html', {'event': event, 'form': form})


@login_required
@permission_required('results.delete_disciplineresult', raise_exception=True)  # <—
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
                return redirect('event_list')
            else:
                form.add_error(None, "Неверное имя пользователя или пароль.")
    else:
        form = LoginForm()
    return render(request, 'auth/login.html', {'form': form})


def custom_logout(request):
    logout(request)
    return redirect('/')


@staff_member_required
def hattorihanzo(request):
    selected_date = parse_date(request.GET.get("date") or "") or dt_date.today()

    if request.method == "POST":
        session_form = PuppyTrainingSessionForm(request.POST)
        if session_form.is_valid():
            session = session_form.save()
            formset = PuppyTrainingExerciseCreateFormSet(request.POST, instance=session)
            if formset.is_valid():
                formset.save()
                return redirect(f"{request.path}?date={session.date.isoformat()}")
            # если formset невалидный — удаляем созданную сессию (чтобы не было пустых)
            session.delete()
        else:
            formset = PuppyTrainingExerciseCreateFormSet(request.POST)
    else:
        session_form = PuppyTrainingSessionForm(initial={"date": selected_date})
        formset = PuppyTrainingExerciseCreateFormSet()

    sessions = (
        PuppyTrainingSession.objects
        .filter(date=selected_date)
        .prefetch_related("exercises")
        .order_by("start_time", "id")
    )

    return render(
        request,
        "results/hattorihanzo.html",
        {
            "selected_date": selected_date,
            "sessions": sessions,
            "session_form": session_form,
            "formset": formset,
        },
    )


@staff_member_required
def hattorihanzo_session_edit(request, pk: int):
    session = get_object_or_404(PuppyTrainingSession, pk=pk)

    if request.method == "POST":
        session_form = PuppyTrainingSessionForm(request.POST, instance=session)
        formset = PuppyTrainingExerciseEditFormSet(request.POST, instance=session)

        if session_form.is_valid() and formset.is_valid():
            session_form.save()
            formset.save()
            return redirect(f"/hattorihanzo?date={session.date.isoformat()}")
    else:
        session_form = PuppyTrainingSessionForm(instance=session)
        formset = PuppyTrainingExerciseEditFormSet(instance=session)

    return render(
        request,
        "results/hattorihanzo_session_edit.html",
        {
            "session": session,
            "session_form": session_form,
            "formset": formset,
        },
    )


@staff_member_required
def hattorihanzo_session_delete(request, pk: int):
    session = get_object_or_404(PuppyTrainingSession, pk=pk)

    if request.method == "POST":
        selected_date = session.date
        session.delete()
        return redirect(f"/hattorihanzo?date={selected_date.isoformat()}")

    return render(
        request,
        "results/hattorihanzo_session_confirm_delete.html",
        {"session": session},
    )


@staff_member_required
@require_POST
def hattorihanzo_exercise_delete(request, pk: int):
    ex = get_object_or_404(PuppyTrainingExercise, pk=pk)
    session_id = ex.session_id
    ex.delete()
    return redirect("hattorihanzo_session_edit", pk=session_id)


@staff_member_required
@require_POST
def hattorihanzo_exercises_reorder(request, pk: int):
    """
    pk = id сессии
    body: {"ordered_ids":[12, 15, 9]}
    """
    session = get_object_or_404(PuppyTrainingSession, pk=pk)

    try:
        payload = json.loads(request.body.decode("utf-8"))
        ordered_ids = payload.get("ordered_ids", [])
        ordered_ids = [int(x) for x in ordered_ids]
    except Exception:
        return JsonResponse({"ok": False, "error": "bad_json"}, status=400)

    # проверяем что это упражнения именно этой сессии
    existing_ids = set(
        PuppyTrainingExercise.objects.filter(session=session).values_list("id", flat=True)
    )
    if not ordered_ids or any(x not in existing_ids for x in ordered_ids):
        return JsonResponse({"ok": False, "error": "invalid_ids"}, status=400)

    # Обновляем позиции 1..N в новом порядке
    with transaction.atomic():
        for pos, ex_id in enumerate(ordered_ids, start=1):
            PuppyTrainingExercise.objects.filter(id=ex_id, session=session).update(position=pos)

    return JsonResponse({"ok": True})
