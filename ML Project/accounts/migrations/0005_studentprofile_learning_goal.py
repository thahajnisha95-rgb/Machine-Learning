from django.db import migrations, models


def reopen_survey_for_new_questions(apps, schema_editor):
    StudentProfile = apps.get_model("accounts", "StudentProfile")
    StudentProfile.objects.filter(learning_goal="").update(onboarding_complete=False)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_studentprofile_onboarding_complete"),
    ]

    operations = [
        migrations.AddField(
            model_name="studentprofile",
            name="learning_goal",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.RunPython(reopen_survey_for_new_questions, migrations.RunPython.noop),
    ]
