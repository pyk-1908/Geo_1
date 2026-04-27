#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "4")


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'supplierinsights.settings')

    if os.getenv("ENV") != "DEV_LOCAL":
        try:
            from opentelemetry.instrumentation.django import DjangoInstrumentor
            from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
            DjangoInstrumentor().instrument()
            Psycopg2Instrumentor().instrument()
        except ImportError:
            pass

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
