# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0.202608252030] - 2026-08-25
### Added
- Packaged local brand assets (`icon.png` and `logo.png`) inside the custom component to satisfy HACS Action validation requirements.
- Refined configuration description translations to remove prohibited raw URLs.
- Alphabetized `manifest.json` keys to conform to Hassfest layout rules.

## [1.0.0.202608231225] - 2026-08-23
### Added
- Initial release of **SG Muslim Prayer Timetable from MUIS** custom integration.
- Year-grouped offline local caching (`muslim_prayers_{year}.json`).
- Collection-based metadata scan to resolve dataset links.
- Smart November/December check for next year's schedule.
- Timestamp entities with prefix `sg_muis_` and next-occurrence rolling logic.
- Config flow UI for custom Collection IDs.

