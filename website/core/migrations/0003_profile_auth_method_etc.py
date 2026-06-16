"""Add auth_method/authorized_at and widen authorized on Profile."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_remove_bundlename_unique_profile_name_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="authorized",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="profile",
            name="auth_method",
            field=models.CharField(
                blank=True,
                max_length=20,
                choices=[
                    ("escrow", "Escrow note"),
                    ("algorand_wallet", "Algorand wallet"),
                    ("evm_xchain", "EVM / xChain"),
                ],
            ),
        ),
        migrations.AddField(
            model_name="profile",
            name="authorized_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
