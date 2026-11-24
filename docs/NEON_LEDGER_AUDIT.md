# Neon Ledger City — accessibility, runtime and claim-integrity audit

The creative interface is a research storytelling layer, not a live Bitcoin fraud checker. Audit scope: source-backed story build and interactive components. GitHub Actions run [45315793715](https://github.com/Thizisfranklin/FraudGraph/actions/runs/45315793715) is the first verified browser audit; later changes run the same tests.

## Measured automated checks

| Verification | Actual result | Important caveat |
| --- | --- | --- |
| TypeScript strict compilation and Vite singlefile build | Pass | Source compilation does not prove scientific inference |
| Research data intake | Pass | Original tracked tables and two saved experiment artifacts generate typed src/data/data.ts |
| Evidence assertions | Pass | Original step-43 AP and missing-data semantics retained |
| Static theme contrast | Pass | All five palettes meet WCAG AA normal-text contrast for text, muted, accents and focus against the dark background; muted against secondary solid surfaces |
| Real-browser interaction tests | Pass | Playwright exercised all 13 chapters, navigation, keyboard time scrubber, source overlay, theme switch, read mode, mobile menu, reduced motion |
| Lighthouse Performance | **80 / 100** | Measured on the CI runner; variable by host/device; large offline bundle affects speed |
| Lighthouse Accessibility | **100 / 100** | Automated checks do not replace full human assistive-technology review |
| Lighthouse Best Practices | **100 / 100** | On audited CI revision only |

GitHub Actions attaches the Lighthouse JSON, desktop/mobile screenshots and test output. Scores correspond to the audited PR revision and are not hardware guarantees.

## Keyboard-only walkthrough

1. Tab through header controls, verify visible focus, and activate radio/theme by Enter/Space.
2. Use the chapter navigation to jump to a later evidence chapter.
3. Focus the temporal scrubber; arrow keys change the recorded time step.
4. Open the evidence drawer / research phone; Escape closes the dialog.
5. Inspect a real case-network node; node information remains text-described.
6. Switch Read/Play mode without changing any recorded numerical outcome.
7. Enable reduced motion; vortex and scanline effects should be removed.

Automated Playwright tests cover navigation, slider, drawers, theme, mobile menu and reduced motion. A full human screen-reader/touch-device trial is still future work.

## Potentially misleading claims explicitly prevented

- A dataset illicit label does **not** establish an individual's guilt; labels are retrospective transaction annotations.
- A high uncalibrated score is **not** a probability of criminal behavior.
- An unknown label is **not** licit.
- Graph features do **not** universally improve every learner or feature family.
- The original illustrative graph-uplift case is **not** a representative sample.
- Pooled AP does **not** demonstrate model stability; the step-43 collapse is central.
- PSI/Wasserstein do **not** establish a verified change in P(Y|X).
- Later adaptive test replay is **post-hoc**, not fresh independent confirmation.
- Hypothetical label delays are **not** actual source label-availability dates.
- Review-priority stars are sample-ranking tiers, **not** a guilt scale.
- The app does **not** look up arbitrary live Bitcoin wallets or TXIDs.
- The existing React Investigator is a historical case-review prototype, **not** a deployed fraud service.
- Money recovered, customer outcomes and prospective reliability were **not** measured.

## Remaining limitations

- GitHub Pages requires owner activation via Settings → Pages → Source: GitHub Actions. CI cannot grant itself this administrative permission.
- Performance can improve by deferring offscreen visuals and reducing the large single-file bundle.
- The skyline, colors and audio-feedback tones are original CSS/SVG/procedural UI elements. No commercial game assets are used.
- Human analyst usability and prospective validation are still missing.

## Reproduce

From the story directory: npm install, npm test, npm run build, npx playwright install --with-deps chromium, npm run test:ui.

The source generator must be run first with the original tracked reports and pinned temporal and robustness experiment CSVs. It refuses missing evidence rather than inventing metrics.
