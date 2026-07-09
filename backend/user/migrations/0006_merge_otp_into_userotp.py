# Generated manually to preserve existing OTP rows while merging OTP into UserOTP.

from django.db import migrations, models


def copy_otp_data(apps, schema_editor):
    UserOTP = apps.get_model("user", "UserOTP")

    for user_otp in UserOTP.objects.select_related("for_otp"):
        otp = user_otp.for_otp
        user_otp.otp = otp.otp
        user_otp.created_at = otp.created_at
        user_otp.expired_at = otp.expired_at
        user_otp.used = otp.used
        user_otp.failed_attempts = otp.failed_attempts
        user_otp.save(
            update_fields=[
                "otp",
                "created_at",
                "expired_at",
                "used",
                "failed_attempts",
            ]
        )


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0005_delete_otpverification_otp_failed_attempts"),
    ]

    operations = [
        migrations.AddField(
            model_name="userotp",
            name="created_at",
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name="userotp",
            name="expired_at",
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name="userotp",
            name="failed_attempts",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="userotp",
            name="otp",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="userotp",
            name="used",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(copy_otp_data, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="userotp",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="userotp",
            name="expired_at",
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name="userotp",
            name="otp",
            field=models.CharField(max_length=255),
        ),
        migrations.RemoveField(
            model_name="userotp",
            name="for_otp",
        ),
        migrations.DeleteModel(
            name="OTP",
        ),
        migrations.AlterModelOptions(
            name="userotp",
            options={"ordering": ["-created_at"]},
        ),
    ]
