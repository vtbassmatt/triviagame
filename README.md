# Trivia Game

This was built as a little project to host live trivia over video chat.

## To get started

Tested with Python 3.9 on macOS and Ubuntu 20.04.

```
pip install -r requirements.txt
cd app
./manage.py createsuperuser
./manage.py runserver
```

- Open your browser and head to https://127.0.0.1:8000/backstage
- Login with the superuser you created
- You're now in the Django admin, so:
  - Add a Game
  - Create some pages for the game
  - Create some questions for the pages

On the Game entry in the admin, you can click "View on site" to open the "join as host" flow.
From there, click "Manage game" and you can find the "Player join" link.

## Running a game

`TODO`!
