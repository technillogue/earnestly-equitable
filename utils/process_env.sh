#!/usr/bin/env bash

set -e

env=${FLASK_ENV:-""}

# -- Set default values --

if [[ "$env" == "development" ]]; then
    dev=true
else
    dev=false
fi
compile=false
wipe=false

# -- Set config from options --

while [[ -n "$1" ]]; do
    case "$1" in
        --dev) dev=true ;;
        --compile) compile=true ;;
        --wipe) wipe=true ;;
        *) echo "Option \"$1\" not recognized"
    esac
    shift
done

# -- Validate --

if [[ "$compile" == true && "$dev" != true ]]; then
    echo "Compile requires dev"
    exit 1
fi

# -- Run --

if [[ "$dev" == true ]]; then
    pip install --upgrade -r requirements/dev.txt
    if [[ "$compile" == true ]]; then
        pip-compile --output-file requirements/lock.txt requirements/base.txt --no-header 2>/dev/null
    fi
fi

if [[ "$wipe" == true ]]; then
    # Compare currently installed packages to what's required to be installed, and wipe old packages

    if [[ "$dev" == true ]]; then
        # Required packages needs to include complete dev tree
        xargs -r -a <(
            comm -2 -3 \
                <(pip freeze | cut -d'=' -f1 | sed -e 's/\(.*\)/\L\1/' | sort) \
                <(cat <(pip-compile --output-file - requirements/dev.txt --no-header 2>/dev/null | grep '^\w') \
                      <(grep '^\w' requirements/lock.txt) | cut -d'=' -f1 | sort -u)
        ) pip uninstall -y
    else
        xargs -r -a <(
            comm -2 -3 \
                <(pip freeze | cut -d'=' -f1 | sed -e 's/\(.*\)/\L\1/' | sort) \
                <(grep '^\w' requirements/lock.txt | cut -d'=' -f1 | sort)
        ) pip uninstall -y
    fi
fi

pip install -r requirements/lock.txt
