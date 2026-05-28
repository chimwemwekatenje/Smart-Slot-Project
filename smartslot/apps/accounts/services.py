from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from apps.core.models import Organisation, OrganisationApplication, ApplicationResource
from apps.resources.models import Resource
from django.utils import timezone

User = get_user_model()

def onboard_organisation(application):
    """
    Onboards an organization whose application registration payment is successful:
    1. Creates/activates the Organisation.
    2. Creates verified Resource objects from approved application resources.
    3. Creates the Organisation Admin user account.
    4. Generates a set-password URL and sends an onboarding email.
    """
    # 1. Create or get Organisation
    org, created = Organisation.objects.get_or_create(
        name=application.organisation_name,
        defaults={'logo': application.logo}
    )

    # Update application with created organization reference
    application.created_organisation = org
    application.status = OrganisationApplication.StatusChoices.COMPLETED
    application.save(update_fields=['created_organisation', 'status'])

    # 2. Replicate verified resources in apps.resources
    for app_res in application.resources.all():
        Resource.objects.get_or_create(
            organisation=org,
            name=app_res.name,
            defaults={
                'category': app_res.category,
                'description': app_res.description,
                'price': app_res.price,
            }
        )

    # 3. Create Organisation Admin User (inactive or randomized temp password)
    admin_username = application.contact_email.split('@')[0]
    # Handle username clash
    base_username = admin_username
    counter = 1
    while User.objects.filter(username=admin_username).exists():
        admin_username = f"{base_username}{counter}"
        counter += 1

    names = application.contact_name.split(' ', 1)
    first_name = names[0]
    last_name = names[1] if len(names) > 1 else ''

    admin_user, user_created = User.objects.get_or_create(
        email=application.contact_email,
        defaults={
            'username': admin_username,
            'first_name': first_name,
            'last_name': last_name,
            'role': User.RoleChoices.ORGANISATION_ADMIN,
            'organisation': org,
            'is_active': True,
        }
    )

    # 4. Generate Password Set Link
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(admin_user)
    
    # We use Django's auth uidb64 encoding style or a direct verification style.
    # Let's write a dedicated setup password view and token logic in views.
    from django.utils.http import urlsafe_base64_encode
    from django.utils.encoding import force_bytes
    uid = urlsafe_base64_encode(force_bytes(admin_user.pk))
    
    site_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
    setup_path = reverse('set_password_route', kwargs={'uidb64': uid, 'token': token})
    setup_url = f"{site_url}{setup_path}"

    # Send Email
    subject = 'SmartSlot - Activate Your Organisation Admin Account'
    body = (
        f"Dear {application.contact_name},\n\n"
        f"Congratulations! Your organisation '{application.organisation_name}' has been successfully verified "
        f"and registered on SmartSlot.\n\n"
        f"An administrator account has been created for you. Please click the link below to set your password "
        f"and activate your portal access:\n\n"
        f"{setup_url}\n\n"
        f"After setting your password, you will be redirected to your Organisation Dashboard to manage "
        f"your resources and staff.\n\n"
        f"Thank you,\n"
        f"SmartSlot Support"
    )

    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL or 'support@smartslot.com',
        recipient_list=[application.contact_email],
        fail_silently=True
    )

    return admin_user
