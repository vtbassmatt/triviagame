# Tr¿via

This was built as a little project to host live trivia over video chat.
It was recently named "Tr¿via" because I couldn't think of a better name.

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

Assuming you've got that, you need a fly.io-hosted Postgres database:
```ShellSession
% flyctl postgres create -a some-db-app-name-1234
% flyctl postgres attach some-db-app-name-1234
```

`postgres attach` subcommand creates a database user and stores a secret named `DATABASE_URL` with the connection string.
You will also need to `flyctl secrets set DJANGO_SECRET_KEY=<some generated secret key>`.
(Thanks to https://davi.sh/blog/2022/10/django-with-flyio/ for originally posting these instructions!)

After you've `flyctl deploy`'d, you will probably also want to follow fly.io's instructions for adding a custom domain and HTTPS certificate.
https://fly.io/docs/app-guides/custom-domains-with-fly/#teaching-your-app-about-custom-domains

## Editing a game

`TODO`!

## Running a game

`TODO`!

## Thanks

Thanks to:
- the Git Fundamentals team at GitHub for playtesting early versions of this ap
- https://favicon.io/favicon-generator/ for the favicon generator
