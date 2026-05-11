#!/usr/bin/env bash


# we have to make the files before running the container, otherwise they will be mounted as folders.

if [ ! -f settings.json ]; then
    cp default_settings.json settings.json
    echo "settings.json has been created."
fi

if [ ! -f .env ]; then
    echo "TOKEN=TOKEN_HERE" > ./.env
    echo "The .env file has been created. Please replace 'TOKEN_HERE' with your bot's token, then re-run this script to launch the bot."
    exit 0
fi


# build and run the container

docker compose build
docker compose down
docker compose up -d
