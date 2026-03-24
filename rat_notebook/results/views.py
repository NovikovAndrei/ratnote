import json
from datetime import date as dt_date
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST, require_GET
from django.http import HttpResponseForbidden, JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db import transaction
from django.utils.dateparse import parse_date
from .models import (
    Event, DisciplineResult, PuppyTrainingSession, PuppyTrainingExercise,
    Exercise, Puppy, Dog, EventDog, EventDogResult, GROWTH_CHOICES
)

from .forms import (
    AthleteForm, DisciplineResultForm, EventForm, LoginForm,
    PuppyTrainingSessionForm, PuppyTrainingExerciseCreateFormSet,
    PuppyTrainingExerciseEditFormSet, ExerciseForm, PuppyForm,
    DogForm, EventDogForm, EventDogResultForm
)
from .scoring import (
    assign_growth_scores,
    compute_final_places,
    assign_event_dog_growth_scores,
    compute_event_dog_final_places,
)


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
@permission_required('results.view_event', raise_exception=True)
def event_detail(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    is_legacy_event = event.is_legacy

    # по умолчанию
    a_form = None
    r_form = None
    dog_form = None
    event_dog_form = None
    event_dog_result_form = None

    if is_legacy_event:
        # =========================
        # СТАРЫЙ ИВЕНТ: ТОЛЬКО АРХИВ
        # =========================

        # Ничего нового добавлять не даём.
        # Просто считаем старые очки и показываем старую историю.
        assign_growth_scores(event)
        standings_old = compute_final_places(event, include_champions=False)

        category_rankings = {}

        # Чемпионы (старая схема)
        champs_old = list(
            event.athletes.filter(is_champion=True)
            .prefetch_related("results", "results__discipline")
        )

        if champs_old:
            champs = []
            for a in champs_old:
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
                setattr(a, "place", place)
                champs_rows.append(a)

            category_rankings["C"] = ("Чемпионы", champs_rows)

        # Ростовые группы (старая схема)
        for code, rows in standings_old.items():
            lst = []
            for row in rows:
                a = row["athlete"]
                setattr(a, "place", row["place"])
                lst.append(a)
            if lst:
                category_rankings[code] = (code, lst)

    else:
        # =========================
        # НОВЫЙ ИВЕНТ: ТОЛЬКО НОВАЯ СХЕМА
        # =========================

        # --- добавление собаки из базы в ивент
        if request.method == 'POST' and 'add_event_dog' in request.POST:
            if not request.user.has_perm('results.add_eventdog'):
                return HttpResponseForbidden('Недостаточно прав')
            event_dog_form = EventDogForm(request.POST, prefix='edog', event=event)
            if event_dog_form.is_valid():
                obj = event_dog_form.save(commit=False)
                obj.event = event
                obj.growth_category = obj.dog.growth_category
                obj.is_champion = obj.dog.is_champion
                obj.save()

                group_code = 'C' if obj.dog.is_champion else obj.dog.growth_category
                url = reverse('event_detail', args=[event.id])
                return redirect(f"{url}?group={group_code}#pane-{group_code}")
        else:
            event_dog_form = EventDogForm(prefix='edog', event=event)

        # --- добавление результата новой собаке
        if request.method == 'POST' and 'add_event_dog_result' in request.POST:
            if not request.user.has_perm('results.add_eventdogresult'):
                return HttpResponseForbidden('Недостаточно прав')
            event_dog_result_form = EventDogResultForm(request.POST, prefix='edres', event=event)
            if event_dog_result_form.is_valid():
                res = event_dog_result_form.save()
                event_dog = res.event_dog
                group_code = 'C' if event_dog.is_champion else event_dog.growth_category
                url = reverse('event_detail', args=[event.id])
                return redirect(f"{url}?group={group_code}#pane-{group_code}")
        else:
            event_dog_result_form = EventDogResultForm(prefix='edres', event=event)

        # Пересчёт очков по новой схеме
        assign_event_dog_growth_scores(event)
        standings_new = compute_event_dog_final_places(event, include_champions=False)

        category_rankings = {}

        # Чемпионы (новая схема)
        champs_new = list(
            event.event_dogs.filter(is_champion=True)
            .select_related("dog")
            .prefetch_related("results", "results__discipline")
        )

        if champs_new:
            champs = []
            for ed in champs_new:
                total = sum(int(r.points or 0) for r in ed.results.all())
                champs.append((ed, total))

            champs.sort(key=lambda p: (p[1], p[0].dog.name), reverse=True)

            last = None
            place = 0
            idx = 0
            champs_rows = []

            for ed, total in champs:
                idx += 1
                if total != last:
                    place = idx
                    last = total
                setattr(ed, "place", place)
                champs_rows.append(ed)

            category_rankings["C"] = ("Чемпионы", champs_rows)

        # Ростовые группы (новая схема)
        for code, rows in standings_new.items():
            lst = []
            for row in rows:
                ed = row["athlete"]
                setattr(ed, "place", row["place"])
                lst.append(ed)
            if lst:
                category_rankings[code] = (code, lst)

    # Какая вкладка активна
    active_group = request.GET.get("group")
    if active_group not in category_rankings:
        active_group = next(iter(category_rankings), None)

    return render(request, "results/event_detail.html", {
        "event": event,
        "is_legacy_event": is_legacy_event,

        "athlete_form": a_form,
        "result_form": r_form,

        "event_dog_form": event_dog_form,
        "event_dog_result_form": event_dog_result_form,

        "category_rankings": category_rankings,
        "active_group": active_group,
    })


@login_required
@permission_required('results.change_disciplineresult', raise_exception=True)
def edit_result(request, result_id):
    r = get_object_or_404(DisciplineResult, pk=result_id)
    event = r.athlete.event
    group_param = request.GET.get('group') or ('C' if r.athlete.is_champion else r.athlete.growth_category)

    if request.method == 'POST':
        form = DisciplineResultForm(request.POST, instance=r, event=event)
        form.fields['athlete'].disabled = True
        form.fields['discipline'].disabled = True

        if form.is_valid():
            obj = form.save(commit=False)
            obj.athlete_id = r.athlete_id
            obj.discipline_id = r.discipline_id
            obj.save()
            url = reverse('event_detail', args=[event.id])
            return redirect(f"{url}?group={group_param}#pane-{group_param}")
    else:
        form = DisciplineResultForm(instance=r, event=event)
        form.fields['athlete'].disabled = True
        form.fields['discipline'].disabled = True

    return render(request, 'results/edit_result.html', {'event': event, 'form': form})


@login_required
@permission_required('results.delete_disciplineresult', raise_exception=True)
def delete_result(request, result_id):
    r = get_object_or_404(DisciplineResult, pk=result_id)
    event = r.athlete.event
    group_param = request.GET.get('group') or ('C' if r.athlete.is_champion else r.athlete.growth_category)

    if request.method == 'POST':
        r.delete()
        url = reverse('event_detail', args=[event.id])
        return redirect(f"{url}?group={group_param}#pane-{group_param}")

    return render(request, 'results/confirm_delete.html', {'event': event, 'object': r})


@login_required
@permission_required('results.view_dog', raise_exception=True)
def dog_list(request):
    if request.method == 'POST':
        if not request.user.has_perm('results.add_dog'):
            return HttpResponseForbidden('Недостаточно прав')
        form = DogForm(request.POST, prefix='dog')
        if form.is_valid():
            dog = form.save()
            group_code = 'C' if dog.is_champion else dog.growth_category
            return redirect(f"{reverse('dog_list')}?group={group_code}#pane-{group_code}")
    else:
        form = DogForm(prefix='dog')

    dogs_qs = Dog.objects.order_by('name')

    category_dogs = {}

    champs = list(dogs_qs.filter(is_champion=True))
    if champs:
        category_dogs['C'] = ('Чемпионы', champs)

    for code, label in GROWTH_CHOICES:
        dogs = list(dogs_qs.filter(is_champion=False, growth_category=code))
        if dogs:
            category_dogs[code] = (code, dogs)

    active_group = request.GET.get('group')
    if active_group not in category_dogs:
        active_group = next(iter(category_dogs), None)

    return render(request, 'results/dog_list.html', {
        'form': form,
        'category_dogs': category_dogs,
        'active_group': active_group,
    })


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


@login_required
def puppy_list(request):
    qs = Puppy.objects.all()
    if not request.user.is_staff:
        qs = qs.filter(owner=request.user)
    return render(request, "results/puppy_list.html", {"puppies": qs})


def get_puppy_for_user_or_404(request, puppy_id: int):
    qs = Puppy.objects.all()
    if not request.user.is_staff:
        qs = qs.filter(owner=request.user)
    return get_object_or_404(qs, pk=puppy_id)


@staff_member_required
def puppy_create(request):
    if request.method == "POST":
        form = PuppyForm(request.POST)
        if form.is_valid():
            p = form.save(commit=False)
            p.owner = request.user  # ✅ важно
            p.save()
            return redirect("puppy_diary", puppy_id=p.id)
    else:
        form = PuppyForm()
    return render(request, "results/puppy_form.html", {"form": form, "title": "Добавить щенка"})


@staff_member_required
def puppy_edit(request, puppy_id: int):
    puppy = get_object_or_404(Puppy, pk=puppy_id)

    if request.method == "POST":
        form = PuppyForm(request.POST, instance=puppy)
        if form.is_valid():
            form.save()
            return redirect("puppy_list")
    else:
        form = PuppyForm(instance=puppy)

    return render(request, "results/puppy_form.html", {"form": form, "title": "Редактировать щенка"})


def puppy_diary(request, puppy_id: int):
    puppy = get_puppy_for_user_or_404(request, puppy_id)  # ✅ было get_object_or_404
    selected_date = parse_date(request.GET.get("date") or "") or dt_date.today()

    if request.method == "POST":
        session_form = PuppyTrainingSessionForm(request.POST)
        if session_form.is_valid():
            session = session_form.save(commit=False)
            session.puppy = puppy
            session.save()

            formset = PuppyTrainingExerciseCreateFormSet(request.POST, instance=session)
            if formset.is_valid():
                formset.save()
                return redirect(f"{request.path}?date={session.date.isoformat()}")
            session.delete()
        else:
            formset = PuppyTrainingExerciseCreateFormSet(request.POST)
    else:
        session_form = PuppyTrainingSessionForm(initial={"date": selected_date})
        formset = PuppyTrainingExerciseCreateFormSet()

    sessions = (
        PuppyTrainingSession.objects
        .filter(puppy=puppy, date=selected_date)
        .prefetch_related("exercises__exercise")
        .order_by("start_time", "id")
    )

    return render(request, "results/puppy_diary.html", {
        "puppy": puppy,
        "selected_date": selected_date,
        "session_form": session_form,
        "formset": formset,
        "sessions": sessions,
    })


def puppy_session_edit(request, puppy_id: int, pk: int):
    puppy = get_puppy_for_user_or_404(request, puppy_id)  # ✅ было get_object_or_404
    session = get_object_or_404(PuppyTrainingSession, pk=pk, puppy=puppy)

    if request.method == "POST":
        session_form = PuppyTrainingSessionForm(request.POST, instance=session)
        formset = PuppyTrainingExerciseEditFormSet(request.POST, instance=session)

        if session_form.is_valid() and formset.is_valid():
            session_form.save()
            formset.save()
            return redirect(f"{reverse('puppy_diary', args=[puppy.id])}?date={session.date.isoformat()}")
    else:
        session_form = PuppyTrainingSessionForm(instance=session)
        formset = PuppyTrainingExerciseEditFormSet(instance=session)

    return render(request, "results/puppy_session_edit.html", {
        "puppy": puppy,
        "session": session,
        "session_form": session_form,
        "formset": formset,
    })


def puppy_session_delete(request, puppy_id: int, pk: int):
    puppy = get_puppy_for_user_or_404(request, puppy_id)  # ✅ было get_object_or_404
    session = get_object_or_404(PuppyTrainingSession, pk=pk, puppy=puppy)

    if request.method == "POST":
        selected_date = session.date
        session.delete()
        return redirect(f"{reverse('puppy_diary', args=[puppy.id])}?date={selected_date.isoformat()}")

    return render(request, "results/puppy_session_confirm_delete.html", {
        "puppy": puppy,
        "session": session,
    })


@staff_member_required
def hattorihanzo_redirect(request):
    # совместимость со старой ссылкой
    puppy = Puppy.objects.order_by("id").first()
    if not puppy:
        return redirect("puppy_create")
    return redirect(f"{reverse('puppy_diary', args=[puppy.id])}?{request.META.get('QUERY_STRING','')}")


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


@login_required
def exercise_list(request):
    exercises = Exercise.objects.all()
    return render(request, "results/exercises_list.html", {
        "exercises": exercises,
    })


@staff_member_required
def exercise_create(request):
    if request.method == "POST":
        form = ExerciseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("exercise_list")
    else:
        form = ExerciseForm()

    return render(request, "results/exercise_form.html", {
        "form": form,
    })


@staff_member_required
@require_GET
def exercise_default_reps(request, pk: int):
    ex = get_object_or_404(Exercise, pk=pk)
    return JsonResponse({"default_reps": ex.default_reps})


@login_required
def dashboard(request):
    return render(request, "dashboard.html")


def exercise_description(request, pk: int):
    ex = get_object_or_404(Exercise, pk=pk)
    return JsonResponse({"description": ex.description or ""})
