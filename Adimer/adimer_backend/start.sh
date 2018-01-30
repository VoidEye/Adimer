#!/bin/bash

echo "Starting migrations"
ret_code=1
python manage.py makemigrations core
while [ "$ret_code" -ne "0" ]
do
    python /app/adimer_backend/manage.py migrate
    ret_code=$?
    if [ "$ret_code" -ne "0" ]
    then
        echo "Cannot connect to DB, retrying..."
        sleep 3
    fi
done
echo "Starting gunicorn"
gunicorn Adimer.wsgi -b 0.0.0.0:8020
