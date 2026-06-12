"""Initial migration for the walletauth app."""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="WalletNonce",
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
                ("address", models.CharField(db_index=True, max_length=58)),
                ("nonce", models.CharField(max_length=64, unique=True)),
                ("chain", models.CharField(default="algorand", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("used", models.BooleanField(default=False)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="wallet_nonces",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="walletnonce",
            index=models.Index(
                fields=["address", "used"], name="walletauth_address_used_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="walletnonce",
            index=models.Index(
                fields=["created_at"], name="walletauth_created_idx"
            ),
        ),
    ]
