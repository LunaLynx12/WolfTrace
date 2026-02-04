# WolfTrace Frontend - TODO & Roadmap
*Last Updated: 2026-01-22*

## ✅ Recently Completed
- Updated error handling to use structured API errors via `getErrorMessage()` helper (all components)
- Verified edge handling uses `source/target` fields only
- Session flows compatible with UUID `id` + timestamped `file_name`

## 🔴 High Priority
- [ ] Add loading/error states for all API calls (spinners + inline errors)
- [ ] Surface backend error codes/messages in UI notifications (map codes to friendly text)
- [ ] Protect destructive actions with confirmations + disabled states while in-flight

## 🟡 Medium Priority
- [ ] Improve session list UI (search, sort by updated_at, pagination)
- [ ] Add retry/backoff for flaky network calls (axios interceptors)
- [ ] Cache session list in IndexedDB with staleness TTL
- [ ] Add toast for successful exports (JSON/PNG/SVG) and handle blob download errors
- [ ] Centralize API base URL and feature flags in a config module

## 🟢 Low Priority
- [ ] Add keyboard shortcuts cheat sheet modal
- [ ] Dark mode polish (contrast/accessibility check)
- [ ] Animations for panel transitions and toasts
- [ ] Add empty states/placeholders for all panels

## 🧪 Testing
- [ ] Add Playwright/E2E smoke tests for critical flows (sessions, query, bulk ops, exports)
- [ ] Add component-level tests for error handling fallbacks

## 📄 Documentation
- [ ] Document API error shapes and how UI maps them
- [ ] Update README with environment variables (VITE_API_URL, feature flags)
- [ ] Add onboarding section for frontend dev (lint/format/test commands)

## 📦 Tooling & Quality
- [ ] Add ESLint + Prettier config and CI checks
- [ ] Add type safety for API responses (TypeScript types or JSDoc)

*This is a living document. Update as tasks are completed or new requirements emerge.*
