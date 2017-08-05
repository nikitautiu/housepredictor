#!/bin/bash

# adds the script's path to pythonpath so you can run the command
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHONPATH=$PYTHONPATH:$DIR/housepredictor

# pass the arguments
housepredictor/cmd.py "$@"