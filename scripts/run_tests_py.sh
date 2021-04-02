#!/bin/sh
coverage run -m unittest discover
echo
coverage report -m
coverage html -d coverage/python
#open htmlcov/index.html
