#!/bin/bash
output="$(cd {{ site_path }}/source/{{ app_name }}/;{{ site_path }}/venv/bin/python manage.py {{ item.name }} --settings={{ django_settings }})"
if [[ {{ item.output }} ]] ; then
    exit 0
else
    echo $output
    exit 0
fi
