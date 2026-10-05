from django.shortcuts import render
from Account.models import Profile


def activate_account(request, email_token):
    profile = Profile.objects.filter(email_token=email_token).first()

    if not profile:
        return render(request, 'verification/activation_result.html', {
            'success': False,
            'message': 'This activation link is invalid or has already been used.',
        })

    if profile.is_email_verified:
        return render(request, 'verification/activation_result.html', {
            'success': True,
            'message': 'Your account is already verified. You can log in now.',
        })

    profile.is_email_verified = True
    profile.save()

    return render(request, 'verification/activation_result.html', {
        'success': True,
        'message': 'Your account has been verified successfully. You can log in now.',
    })