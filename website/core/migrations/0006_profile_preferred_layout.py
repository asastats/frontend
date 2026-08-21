"""Add Profile.preferred_layout (preferred address-page layout key)."""

from django.db import migrations, models


class Migration(migrations.Migration):
    """Add the preferred_layout preference field to Profile."""

    dependencies = [
        ("core", "0005_profile_preferred_explorer"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="preferred_layout",
            field=models.CharField(blank=True, default="", max_length=32),
        ),
    ]
