from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_profile_api_tokens_valid_from"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="fiat",
            field=models.CharField(default="USD", max_length=3),
        ),
    ]
