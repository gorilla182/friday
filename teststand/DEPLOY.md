# Deploy to GitHub Pages

The static site lives in the `site/` folder.

## Quick deploy (recommended)

1. Push this repository to GitHub (e.g. `https://github.com/USERNAME/teststand`)

2. Go to your repository → **Settings → Pages**

3. Under "Build and deployment":
   - Source: **GitHub Actions**

4. Push to `main` branch (or run the workflow manually).

The site will be available at:
`https://USERNAME.github.io/teststand`

## How it works

- `.github/workflows/deploy-pages.yml` uploads only the `site/` folder.
- GitHub Pages serves it statically.
- The site talks directly to your Supabase project (public publishable key).

## Important notes

- The Supabase publishable key is **safe** to commit (it's meant for client-side).
- If your repo name is not `teststand`, the URL will be `https://USERNAME.github.io/REPO-NAME`.
- All links inside the site are relative, so subpath works.

## After first deploy

1. Open the site.
2. Test login with `alice@example.com` / `password123`.
3. Try adding to cart and checkout.

## Resetting data for tests

See the reset instructions in the main README or run:

```bash
# In Supabase SQL Editor
# (use the reset_teststand function or the Edge Function)
```

## Local testing

```bash
cd site
python -m http.server 8000
# open http://localhost:8000
```
