from django.db import migrations, models


def forwards(apps, schema_editor):
    Puppy = apps.get_model("results", "Puppy")
    PuppyTrainingSession = apps.get_model("results", "PuppyTrainingSession")

    # 1) создаём "первого" щенка под текущие данные
    # (поля можно потом отредактировать в интерфейсе)
    puppy, _ = Puppy.objects.get_or_create(
        pet_name="Hattori Hanzo",
        defaults={
            "registered_name": "",
            "sex": "M",
            "birth_date": "2024-01-01",  # поставь любую, потом поменяешь
        },
    )

    # 2) всем существующим сессиям, у кого puppy NULL, проставляем этого щенка
    PuppyTrainingSession.objects.filter(puppy__isnull=True).update(puppy=puppy)


def backwards(apps, schema_editor):
    # обратная миграция: просто отвяжем
    PuppyTrainingSession = apps.get_model("results", "PuppyTrainingSession")
    PuppyTrainingSession.objects.all().update(puppy=None)


class Migration(migrations.Migration):
    dependencies = [
        ("results", "0005_exercise_alter_puppytrainingsession_date_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Puppy",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("pet_name", models.CharField(max_length=120, verbose_name="Домашняя кличка")),
                ("registered_name", models.CharField(blank=True, max_length=200, verbose_name="Кличка по документам")),
                ("sex", models.CharField(choices=[("M", "Кобель"), ("F", "Сука")], max_length=1, verbose_name="Пол")),
                ("birth_date", models.DateField(verbose_name="Дата рождения")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Щенок",
                "verbose_name_plural": "Щенки",
                "ordering": ["pet_name", "id"],
            },
        ),

        # добавляем FK как nullable, чтобы прошла миграция
        migrations.AddField(
            model_name="puppytrainingsession",
            name="puppy",
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=models.deletion.CASCADE,
                related_name="sessions",
                to="results.puppy",
                verbose_name="Щенок",
                db_index=True,
            ),
        ),

        migrations.RunPython(forwards, backwards),

        # делаем обязательным после переноса данных
        migrations.AlterField(
            model_name="puppytrainingsession",
            name="puppy",
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE,
                related_name="sessions",
                to="results.puppy",
                verbose_name="Щенок",
                db_index=True,
            ),
        ),
    ]
