#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def clear_sessions():
    """Flush all sessions so no user stays logged in across server restarts."""
    try:
        from django.contrib.sessions.models import Session
        Session.objects.all().delete()
    except Exception:
        pass  # DB may not be ready yet on first run


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Clear all sessions every time the server starts
    if len(sys.argv) > 1 and sys.argv[1] == 'runserver':
        import django
        django.setup()
        clear_sessions()

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
