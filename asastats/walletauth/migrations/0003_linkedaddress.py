import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("walletauth", "0002_walletloginnonce"),
        # Profile (and Profile.address) exist from core's first migration. If a
        # downstream project introduced Profile later, bump this accordingly.
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="LinkedAddress",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("address", models.CharField(max_length=58)),
                ("canonical_address", models.CharField(db_index=True, max_length=58)),
                ("chain", models.CharField(max_length=20)),
                ("auth_method", models.CharField(max_length=20)),
                ("authorized", models.CharField(blank=True, default="", max_length=64)),
                ("is_primary", models.BooleanField(default=False)),
                ("login_enabled", models.BooleanField(default=False)),
                ("label", models.CharField(blank=True, default="", max_length=64)),
                (
                    "verified_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="linked_addresses",
                        to="core.profile",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="linkedaddress",
            constraint=models.UniqueConstraint(
                fields=("canonical_address",),
                name="uniq_linkedaddress_canonical",
            ),
        ),
        migrations.AddConstraint(
            model_name="linkedaddress",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_primary", True)),
                fields=("profile",),
                name="uniq_linkedaddress_one_primary",
            ),
        ),
        migrations.AddConstraint(
            model_name="linkedaddress",
            constraint=models.CheckConstraint(
                condition=models.Q(("is_primary", False))
                | models.Q(("login_enabled", True)),
                name="ck_linkedaddress_primary_login",
            ),
        ),
    ]
