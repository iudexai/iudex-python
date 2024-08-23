#!/usr/bin/env python
from iudex import instrument
"""Django's command-line utility for administrative tasks."""
import os
import sys
# from opentelemetry.instrumentation.django import DjangoInstrumentor
# from opentelemetry.instrumentation.dbapi import trace_integration
# import MySQLdb
# trace_integration(MySQLdb, "connect", "mysql")

def main():
    """Run administrative tasks."""
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "test_django_instrumentation.settings"
    )
    instrument(
        service_name="jobs_board_service", # Highly encouraged
        iudex_api_key="ixk_963e1991dc4df6b2cb132a59fadb1a30f7170b4108f7221b524c442322c06cb4", # Only ever commit your WRITE ONLY key
        env="prod", # Optional, dev, local, etc
        disable_print=True,
    )

    # from django.db.models import Model, QuerySet
    # from iudex import trace
    # queryset_methods_to_patch = [
    #     'get', 'create', 'get_or_create', 'update_or_create', 'bulk_create',
    #     'bulk_update', 'count', 'in_bulk', 'iterator', 'latest', 'earliest',
    #     'first', 'last', 'aggregate', 'exists', 'contains', 'update', 'delete',
    #     'as_manager', 'explain', 'all',
    # ]
    # def get_attributes(instance):
    #     return {'model': instance.model.__name__ or instance.__name__}
    # for method_name in queryset_methods_to_patch:
    #     original_method = getattr(QuerySet, method_name, None)
    #     if original_method:
    #         traced_method = trace(
    #             original_method,
    #             get_attributes=get_attributes,
    #         )
    #         setattr(QuerySet, method_name, traced_method)
    
    # model_methods_to_patch = ['save', 'delete', 'full_clean']
    # for method_name in model_methods_to_patch:
    #     original_method = getattr(Model, method_name, None)
    #     if original_method:
    #         traced_method = trace(
    #             original_method,
    #             get_attributes=get_attributes,
    #         )
    #         setattr(Model, method_name, traced_method)

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
