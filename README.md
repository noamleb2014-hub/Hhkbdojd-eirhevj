# SkyFinder

Point your phone at the sky and discover what you're looking at — stars,
constellations, planets, the Moon, aircraft, satellites and the ISS.

An installable PWA landing page.

## Structure

| Path | Purpose |
|---|---|
| `index.html` | The whole site — markup, CSS and JS in one file |
| `manifest.webmanifest` | PWA manifest (name, icons, theme colour) |
| `sw.js` | Service worker — offline shell + runtime caching |
| `icons/favicon.svg` | Source brand mark (text, committed) |
| `tools/make_icons.py` | Generates the PNG/ICO icon set at build time |

## Icons

The binary PNG and ICO icons are **not committed**. They are generated during
the GitHub Pages build by `tools/make_icons.py`, which needs Pillow. This keeps
the repository free of binary blobs and makes the icon set reproducible from
the source artwork.

To regenerate locally:

```bash
pip install pillow
python3 tools/make_icons.py
```

## Deployment

Pushing to `main` triggers `.github/workflows/pages.yml`, which generates the
icons, enables GitHub Pages if needed, and publishes the site.

## Notes

- The service worker requires HTTPS or `localhost`; it is skipped on `file://`.
- `netlify.toml` / `_headers` are not needed here — GitHub Pages derives the
  manifest MIME type from its own type table.
