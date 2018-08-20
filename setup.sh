#!/bin/bash

echo "Installing virtual environment"
sudo apt-get install python3-venv
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt

echo "Setting up database"
export FLASK_ENV=development
export FLASK_DEBUG=true
export FLASK_APP=BigBrewer
flask init-db

echo "Setting up git"
git submodule init
git submodule update
