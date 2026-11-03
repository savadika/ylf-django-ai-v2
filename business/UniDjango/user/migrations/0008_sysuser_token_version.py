from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0007_alter_sysuser_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="sysuser",
            name="token_version",
            field=models.PositiveIntegerField(
                default=0,
                verbose_name="令牌版本",
            ),
        ),
    ]
