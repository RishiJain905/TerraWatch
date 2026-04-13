# aisstream API Key Setup Guide

This guide walks you through getting an aisstream API key and adding it to a local `.env` file when you run TerraWatch on your PC.

---

## What this key is for

TerraWatch uses aisstream as a secondary ship-data source for global vessel tracking.

The backend looks for this environment variable:

`AISSTREAM_API_KEY`

Without it, TerraWatch will safely fall back to other available ship sources (Digitraffic for Nordic/Baltic waters).

---

## Important note before you start

aisstream documents its API here:

Website:
- https://aisstream.io/

API access requires a free API key obtained via GitHub OAuth.

---

## Step-by-step: Get the API key

### Step 1 — Open the aisstream website
Go to:

https://aisstream.io/

### Step 2 — Sign in with GitHub
aisstream uses GitHub OAuth for authentication. Click "Sign In" and authorize with your GitHub account.

---

## Create your local `.env` file

When you run TerraWatch locally, create a `.env` file in the **project root** (not the backend folder).

The backend loads `.env` from the repo root via `python-dotenv`.

---

## What to put in the `.env` file

Create this file in the TerraWatch project root:

```
TerraWatch/.env
```

Add:

```env
AISSTREAM_API_KEY=your_key_here
```

Optional full example:

```env
PYTHON_ENV=development
AISSTREAM_API_KEY=your_key_here
ADSBLOL_REFRESH_SECONDS=30
```

---

## Security tips

- Never commit your real `.env` file to GitHub
- Never post your token in chat, screenshots, or issues
- Treat the token like a password

---

## Quick checklist

Before running locally, confirm:

- [ ] I signed into aisstream.io with GitHub OAuth
- [ ] I generated/copied my API key
- [ ] I created `TerraWatch/.env` in the project root
- [ ] I added `AISSTREAM_API_KEY=***` to the `.env` file
- [ ] I did not commit the token to Git
