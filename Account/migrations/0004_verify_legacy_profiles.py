from django.db import migrations


def verify_legacy_profiles(apps, schema_editor):
    Profile = apps.get_model("Account", "Profile")
    # profiles created before email verification existed have no token
    Profile.objects.filter(email_token__isnull=True).update(is_email_verified=True)
    Profile.objects.filter(user__is_superuser=True).update(is_email_verified=True)
    Profile.objects.filter(email="").update(email=None)


class Migration(migrations.Migration):

    dependencies = [
        ("Account", "0003_alter_profile_email"),
    ]

    operations = [
        migrations.RunPython(verify_legacy_profiles, migrations.RunPython.noop),
    ]