#!/bin/bash

## ~~~ TO BE EDITED TO BE TAILORED TO THE CLUSTER ~~~
##
## You only need to edit the venv creation line below, marked "EDIT ME".
## Make sure you are loading python 3.8 or greater.
##

# store the cwd in case we need to filter on it
userCWD="$(pwd)"

# Cd into the directory where the GA files are located
parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path"

# Test if the virtualenv GA_env already exists, and if not, creates it. Download python 3.11 or higher for better results.
if [ ! -f GA_env/bin/activate ]; then
  echo "Need to create virtualenv"
  /usr/bin/python3.11 -m venv GA_env # EDIT ME: this line needs updating to load python on your server
  source GA_env/bin/activate
  pip3 install -r requirements.txt
else
  echo "Virtualenv: OK"
  source GA_env/bin/activate
fi

# Test if the python version is at least 3.11
version_major=$(python -c 'import sys; print(sys.version_info[0])')
version_minor=$(python -c 'import sys; print(sys.version_info[1])')
if (( $version_major < 3 )); then
  echo "The command python needs to refer to python 3"
  exit 1
fi

if (( $version_minor < 11 )); then
  echo "The command python needs to refer to python3.11 or higher."
  exit 1
fi
  echo "Python versions: OK"


# Run the python code and pass on the arguments
#userCWD="/home/ll582/ with space" # DEBUGONLY
python __init__.py "$@" --userCWD "$userCWD"