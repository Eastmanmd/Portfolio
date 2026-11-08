# eastmanmd.github.io

Personal site of Ali Oku, built with [Quarto](https://quarto.org) and deployed to GitHub Pages by `.github/workflows/publish.yml` on every push to `main`.

## Local preview

```bash
quarto preview
```

## Writing a review

1. Copy `reviews/_template/` to `reviews/YYYY-MM-short-name/`.
2. Fill it in. It stays hidden while `draft: true`.
3. Set `draft: false`, commit, and push.

Reviews that run code are rendered locally first (`quarto render`); commit the generated `_freeze/` folder so CI doesn't need to re-run the code.
