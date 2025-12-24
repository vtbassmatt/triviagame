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

## Deploying to fly.io

**I used to deploy this to fly.io, but have recently switched to a VPS.**
Therefore the fly.io infrastructure won't be maintained, and will eventually be removed.

If you aren't me, you'll need to edit fly.toml with a new app name.

Assuming you've got that, you need a fly.io-hosted Postgres database:
```ShellSession
% fly postgres create -a some-db-app-name-1234
% fly postgres attach some-db-app-name-1234
```

`postgres attach` subcommand creates a database user and stores a secret named `DATABASE_URL` with the connection string.
You will also need to `fly secrets set DJANGO_SECRET_KEY=<some generated secret key>`.
(Thanks to https://davi.sh/blog/2022/10/django-with-flyio/ for originally posting these instructions!)

After you've `fly deploy`'d, you will probably also want to follow fly.io's instructions for adding a custom domain and HTTPS certificate.
https://fly.io/docs/app-guides/custom-domains-with-fly/#teaching-your-app-about-custom-domains

## Growing/shrinking the fly.io sizes

For limited testing, I've been running the database on a single `shared` CPU and 256mb of RAM.
During a recent bigger game, I temporarily doubled that and had a good experience (14 teams, 6 rounds, 92 points worth of questions).

```ShellSession
# grow
fly machine update -a some-db-app-name-1234 --vm-cpus 2 --vm-memory 512

# shrink
fly machine update -a some-db-app-name-1234 --vm-cpus 1 --vm-memory 256
```

## Editing a game

`TODO`!

## Running a game

`TODO`!

## Thanks

Thanks to:
- the Git Fundamentals team at GitHub for playtesting early versions of this app
- https://favicon.io/favicon-generator/ for the favicon generator
