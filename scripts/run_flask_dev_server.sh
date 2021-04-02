#!/bin/sh

export FLASK_APP=fhodot/app/__init__.py
export FLASK_ENV=development
python -m flask run --host 127.0.0.1
