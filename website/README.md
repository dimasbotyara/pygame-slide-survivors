# Slide Survivors website

A static Angular landing page using the actual [ng-brutalism](https://github.com/khangtrannn/ng-brutalism) UI primitives (MIT) and Tailwind CSS v4. The default theme is dark. The site selects English or Russian from browser language preferences (falling back to English); a manually chosen language and theme are stored locally and take priority on future visits. The header includes a touch-friendly menu on small screens. The gameplay image is rendered from the game; the hero SVG illustration uses the game’s actual sprite patterns and colours. Bundled typefaces are from the game's `assets/fonts` directory (see their OFL licenses there).

## Develop

Requires Node.js 22 and npm:

```sh
cd website
npm ci
npm start
```

## Publish

The `Deploy website to GitHub Pages` workflow builds on pushes to `main`, with a base URL matching the repository name, and deploys the static output via GitHub Actions. In the repository's **Settings → Pages**, set **Build and deployment → Source** to **GitHub Actions**. After the workflow completes, the project site is available at `https://dimasbotyara.github.io/pygame-slide-survivors/` (or the URL shown in the deployment). The workflow can also be run manually.

To test a production build locally:

```sh
npm run build -- --base-href /pygame-slide-survivors/
```
