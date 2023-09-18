# moekyun.me (Vercel) 
This is a Vercel adapted version of the [moekyun.me](https://moekyun.me) link shortener. This version uses Vercel's serverless functions + Flask and Vercel's PostgreSQL database to store the links.

An alternative version that uses MySQL and that can be deployed using WSGI can be found [here](https://github.com/pinapelz/link-shortener-moekyun.me)

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

4. Let Vercel create the environment variables for you. Ensure they all start with `POSTGRES`
```
POSTGRES_URL
POSTGRES_URL_NON_POOLING
POSTGRES_PRISMA_URL
POSTGRES_USER
POSTGRES_HOST
POSTGRES_PASSWORD
POSTGRES_DATABASE
```

**Additionally you must add the following variables manually:**
```
POSTGRES_PORT = 5432

MOE_IMAGE = YOUR_IMAGE_URL  # This image is shown as the center icon on the page

MOE_QUOTE = YOUR_QUOTE  # This message is shown center of the page
```
5. Customize and redeploy the project!

*Inspired by https://catbox.moe*