"""Add the WalletLoginNonce model for wallet sign-in challenges."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("walletauth", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="WalletLoginNonce",
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
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["address", "used"],
                        name="walletauth_w_address_login_idx",
                    ),
                    models.Index(
                        fields=["created_at"],
                        name="walletauth_w_created_login_idx",
                    ),
                ],
            },
        ),
    ]
