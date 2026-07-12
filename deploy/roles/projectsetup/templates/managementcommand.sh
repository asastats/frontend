#!/bin/bash
cd {{ site_path }}/source/{{ app_name }}
{{ site_path }}/venv/bin/python manage.py {{ item }} --settings={{ django_settings }}
if [[ $? -ne 0 ]] ; then
    exit 1
fi
