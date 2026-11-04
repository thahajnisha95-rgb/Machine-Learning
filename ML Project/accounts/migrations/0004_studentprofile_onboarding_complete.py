from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_studentresourceprogress"),
    ]

    operations = [
        migrations.AddField(
            model_name="studentprofile",
            name="onboarding_complete",
            field=models.BooleanField(default=False),
        ),
    ]
