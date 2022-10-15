# Trivia Game

This was built as a little project to host live trivia over video chat.

## To get started

Tested locally with Python 3.10 on macOS.

```
poetry install
poetry run ./manage.py migrate
poetry run ./manage.py createsuperuser
poetry run ./manage.py runserver
```

- Open your browser and head to https://127.0.0.1:8000/backstage
- Login with the superuser you created
- You're now in the Django admin, so:
  - Add a Game
  - Create some pages for the game
  - Create some questions for the pages

On the Game entry in the admin, you can click "View on site" to open the "join as host" flow.
From there, click "Manage game" and you can find the "Player join" link.

## Deploying to fly.io

If you aren't me, you'll need to edit fly.toml with a new app name.
You'll also need a fly.io-hosted Postgres database and some of the instructions here:
https://davi.sh/blog/2022/10/django-with-flyio/

## Editing a game

`TODO`!

## Running a game

`TODO`!
