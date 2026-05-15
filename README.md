# Tr¿via

This was built as a little project to host live trivia over video chat.
It was recently named "Tr¿via" because I couldn't think of a better name.

## To get started

Tested locally with Python 3.14 on macOS.

```
uv install
uv run ./manage.py migrate
uv run ./manage.py createsuperuser
uv run ./manage.py runserver
```

- Open your browser and head to https://127.0.0.1:8000/backstage
- Login with the superuser you created
- You're now in the Django admin, so:
  - Add a Game
  - Create some pages for the game
  - Create some questions for the pages

On the Game entry in the admin, you can click "View on site" to open the "join as host" flow.
From there, click "Manage game" and you can find the "Player join" link.

## Editing a game

`TODO`!

## Running a game

`TODO`!

## Thanks

Thanks to:
- the Git Fundamentals team at GitHub for playtesting early versions of this app
- https://favicon.io/favicon-generator/ for the favicon generator
