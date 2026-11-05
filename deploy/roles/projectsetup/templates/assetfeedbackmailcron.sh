#!/bin/bash
cd {{ site_path }}/source/{{ app_name }}
{{ site_path }}/venv/bin/python manage.py assetfeedbackexport --no-contact --settings={{ django_settings }}
