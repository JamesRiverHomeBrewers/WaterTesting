#! /bin/bash

mkdir -p html/location html/result html/img
cp -r css html/css
cp -r js html/js

python parse_data.py
