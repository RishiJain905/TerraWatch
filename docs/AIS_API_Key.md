# AIS Friends API Key Setup Guide

This guide walks you through getting an AIS Friends API key and adding it to a local `.env` file when you run TerraWatch on your PC.

---

## What this key is for

TerraWatch uses AIS Friends as a secondary ship-data source.

The backend looks for this environment variable:

`AIS_FRIENDS_API_KEY`

Without it, the AIS Friends ship service will safely return an empty list and TerraWatch will fall back to other available ship sources.

---

## Important note before you start

AIS Friends documents its API here:

Website / docs:
- https://www.aisfriends.com/
- https://www.aisfriends.com/docs/api/v1

According to their documentation, API access requires:
- an AIS Friends account
- a Bearer token
- and, in many cases, contributing AIS data with your own station

If the site does not immediately show you an API token after signup, that is likely why.

---

## Step-by-step: Get the API key

### Step 1 — Open the AIS Friends website
Go to:

https://www.aisfriends.com/

If you want to read their API docs first, open:

https://www.aisfriends.com/docs/api/v1

---

### Step 2 — Create an account or sign in
- Click Sign Up / Register if you do not already have an account
- If you already have one, sign in

Use a real email address so you can complete any verification steps.

---

### Step 3 — Verify your account if required
After signup:
- check your email inbox
- click any verification / activation link they send you
- sign back into the AIS Friends site

---

### Step 4 — Look for your API access page
Once logged in, look for sections such as:
- API
- Developer
- Access Token
- Profile
- Account Settings
- My Stations

The token may be listed as:
- API key
- API token
- Access token
- Bearer token

What you need is the token value used like this:

`Authorization: Bearer YOUR_TOKEN`

---

### Step 5 — If no token is visible, check whether AIS data contribution is required
AIS Friends says API access is tied to contributing AIS data with your own station.

If you do not see an API token, look for pages about:
- setting up a station
- feeding AIS data
- claiming a station
- linking a receiver
- becoming a contributor

You may need to complete that process before the token becomes available.

---

### Step 6 — Copy the token carefully
When you find the token:
- copy it exactly
- do not add extra spaces
- do not include the word `Bearer`

Example:
- correct: `abc123xyz...`
- not correct: `Bearer abc123xyz...`

Your `.env` file should contain only the raw token value.

---

## Create your local `.env` file

When you run TerraWatch locally on your PC, create a `.env` file in the backend folder unless your local setup expects it elsewhere.

Based on the current TerraWatch backend layout, the safest location is:

`TerraWatch/backend/.env`

If you already use a repo-root `.env` in your local workflow, keep your setup consistent — but the backend-local `.env` is the clearest choice.

---

## What to put in the `.env` file

Create this file:

`TerraWatch/backend/.env`

Add:

```env
AIS_FRIENDS_API_KEY=your_token_here
AIS_FRIENDS_REFRESH_SECONDS=60
```

Optional example with other backend values:

```env
PYTHON_ENV=development
AIS_FRIENDS_API_KEY=your_real_token_here
AIS_FRIENDS_REFRESH_SECONDS=60
ADSBLOL_REFRESH_SECONDS=30
```

---

## Example workflow on your PC

### 1. Open your TerraWatch project
Example:

```bash
cd TerraWatch/backend
```

### 2. Create the `.env` file
On Linux/macOS:

```bash
touch .env
```

On Windows PowerShell:

```powershell
New-Item .env -ItemType File
```

### 3. Open the `.env` file in your editor
Paste:

```env
AIS_FRIENDS_API_KEY=your_real_token_here
AIS_FRIENDS_REFRESH_SECONDS=60
```

### 4. Save the file

---

## Security tips

- Never commit your real `.env` file to GitHub
- Never post your token in chat, screenshots, or issues
- Treat the token like a password

Good practice:
- keep `.env` local only
- rotate/regenerate the token if you think it was exposed

---

## How TerraWatch uses the key

The current backend reads:
- `AIS_FRIENDS_API_KEY`
- `AIS_FRIENDS_REFRESH_SECONDS`

If the key is missing:
- TerraWatch will not crash
- the AIS Friends ship fetch will be skipped
- ship results from AIS Friends will be empty until the key is added

---

## Quick checklist

Before running locally, confirm:

- [ ] I created or signed into my AIS Friends account
- [ ] I found or generated my API token
- [ ] I copied only the raw token value
- [ ] I created `TerraWatch/backend/.env`
- [ ] I added `AIS_FRIENDS_API_KEY=...`
- [ ] I saved the file
- [ ] I did not commit the token to Git

---

## If you get stuck

If AIS Friends does not show you a token:
1. re-check the API docs: https://www.aisfriends.com/docs/api/v1
2. check your account/profile/settings pages
3. look for station or feeder setup requirements
4. verify your account email
5. check whether contributor access is required before API access is enabled

---

## Ready-to-copy template

Use this in your local backend `.env` file:

```env
AIS_FRIENDS_API_KEY=your_real_token_here
AIS_FRIENDS_REFRESH_SECONDS=60
```
