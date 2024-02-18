# moekyun.me (Vercel) 
This is a Vercel adapted version of the [moekyun.me](https://moekyun.me) link shortener. This version uses Vercel's serverless functions + Flask and Vercel's PostgreSQL or Redis database to store the links.

<img src="https://files.catbox.moe/8lgla6.png"/>

## Deploy on Vercel
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new)

1. Import this repository or your fork into Vercel (make a fork if you'd like to change the appearence of the site)
    - Framework Preset: Other
    - Root Directory: `./` (the default)
    - Leave Build and Output Settings empty
Deploy the project, you may see an error page, but that's fine

2. Go to your Deployment page on Vercel and Select Storage

<img src="https://files.catbox.moe/4ix7zf.png" />

3. Connect Store and create a new PostgreSQL database (or an existing one)

Here you must decide between whether you'd like to use Redis or Postgres as your backend storage

4a. For Postgres create the following environment variables
```
POSTGRES_HOST (ex. somedomain.postgres.vercel-storage.com)
POSTGRES_USER (ex. default)
POSTGRES_PASSWORD (ex. mypassword123)
POSTGRES_PORT (ex. 5432)
POSTGRES_DATABASE (ex. verceldb)
```

4b. For Redis create the following environment variables
```
KV_URL (ex. someredis.upstash.io)
KV_USER (ex. default)
KV_PASSWORD (ex. 123456)
KV_PORT = 41891
```

**Additionally you must add the following variables manually:**

```
STORAGE_MODE (redis or psql)
CUSTOM_URL_REQUIRE_AUTH (set this to True if yes, do not create this is you don't want auth)
```

5. Add Additional variables, these are optional
```
MOE_IMAGE = YOUR_IMAGE_URL  # This image is shown as the center icon on the page

MOE_QUOTE = YOUR_QUOTE  # This message is shown center of the page

SITE_URL = YOUR_SITE_URL  # This is the domain of your site, e.g. https://moekyun.me

CORNER_GRAPHICS = [image1.png, image2.png, image3.png]
```


*Inspired by https://catbox.moe*