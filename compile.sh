#! /bin/bash

mkdir -p html/location html/result html/img
cp -r css/* html/stylesheets
cp -r js/* html/js
cp -r fonts/* html/fonts

python parse_data.py
