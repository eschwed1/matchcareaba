# Match Care ABA — Project Memory

## Project Overview
Static HTML website for Match Care ABA — a free ABA therapy matching service serving NY, NJ, and NC.
Working directory: `/Users/sara/Desktop/github.com/eschwed1/matchcareaba`

## Key Files
- `index.html` — Main homepage
- `blog.html` — Blog index page (lists all blog cards)
- `blog-*.html` — Individual blog post pages
- `sitemap.xml` — Sitemap (update when adding pages)
- `logo.jpeg`, `family-hero.jpeg`, `consultation.jpeg` — Images

## Blog Posts (11 total, sorted newest to oldest)
1. `blog-aba-therapy-waitlist.html` — Mar 3, 2025
2. `blog-medicaid-aba-therapy-ny-nj-nc.html` — Feb 18, 2025
3. `blog-aba-therapy-cost.html` — Feb 3, 2025
4. `blog-aba-therapy-activities-at-home.html` — Jan 10, 2025
5. `blog-aba-therapy-at-school-daycare.html` — Dec 3, 2024
6. `blog-why-does-aba-therapy-work.html` — Nov 12, 2024
7. `blog-how-long-does-aba-therapy-take.html` — Oct 8, 2024
8. `blog-aba-therapy-medicaid-providers.html` — Sep 15, 2024
9. `blog-aba-therapy-insurance-coverage.html` — Sep 2, 2024
10. `blog-early-signs-aba-therapy.html` — Aug 20, 2024
11. `blog-find-aba-therapy-ny-nj-nc.html` — Aug 5, 2024

## Blog Post Structure
Each blog post HTML file has:
- Full CSS block (copy from existing posts)
- Nav with serving bar
- `.article-hero` div with: back-link, `.article-tag`, h1, `.article-meta` (date • read time • "By The Match Care ABA Team"), `.article-intro`
- `<article class="article-body">` with h2/h3/p/ul/ol, special boxes, `.inline-cta`
- Bottom `.blog-cta` section
- Footer
- Hamburger menu JS

## Author Byline Convention
**Always use:** "By The Match Care ABA Team" (with "The")

## Design System
- Colors: --navy #1B3A6B, --navy-mid #2A5298, --gold #F5A623, --gold-light #FFD166
- Fonts: Nunito (primary), Quicksand
- Background: --sky #EEF6FF
- Special box types: `.state-box` (.ny/.nj/.nc), `.highlight-box`, `.reassurance-box`, `.inline-cta`, `.warning-box`, `.qa-box`
- JotForm CTA link: https://form.jotform.com/260662279796069
- GA4 tag: G-37F7PCXW57

## blog.html Grid
- 3-column grid, 8 posts shown
- Each card shows: tag, h2 title, date • read time • author byline, excerpt, "Read More" button
- nth-child animations set for cards 1-8

## Hosting
See DEPLOY.md for deployment instructions.

---

# Provider Portal — Separate Project

## Location
`/Users/sara/Desktop/github.com/eschwed1/provider-portal`

## Stack
- React 18 + Vite + Tailwind CSS (Navy #1B3A6B / Gold #D4A843)
- Netlify Functions (Express + serverless-http) as backend API
- AWS RDS PostgreSQL (10 tables), AWS S3 (docs), AWS SES (emails)
- Google Maps Distance Matrix API for provider matching (server-side only)
- TanStack Query, React Router v6, Recharts, react-hook-form

## Key Architecture
- Frontend: `/src` — React SPA deployed as static files on Netlify
- Backend: `/netlify/functions/api.js` — Express app, routes at `/api/*`
- Redirect: `/api/*` → `/.netlify/functions/api/:splat` (netlify.toml)
- Auth: JWT access token (15min, Bearer header) + refresh token (7d, httpOnly cookie)
- Roles: `admin` and `provider`

## Key Files
- `db/schema.sql` — all 10 tables + triggers
- `netlify/functions/api.js` — Express entry point
- `netlify/functions/lib/matching.js` — Google Maps matching algorithm
- `netlify/functions/lib/ses.js` — 6 email templates
- `netlify/functions/package.json` — backend deps (separate from frontend)
- `src/utils/api.js` — Axios with auto-refresh interceptor
- `src/contexts/AuthContext.jsx` — auth state management
- `.env.example` — all required env vars

## Setup to Deploy
1. `psql $DATABASE_URL -f db/schema.sql` to create tables
2. Seed admin user (see schema.sql comment for bcrypt command)
3. Set all env vars in Netlify dashboard (copy from .env.example)
4. Push to GitHub → connect to Netlify → auto-deploy
5. Set JotForm webhook URL: `https://your-domain.com/api/families/webhook`
6. Add `X-Jotform-Secret` header in JotForm webhook settings

## JotForm Field Mapping (routes/families.js)
Field names expected: q3_childFirst, q3_childLast, q4_childDob, q5_parentName,
q6_email, q7_phone, q8_address (nested), q9_insurance, q10_hours, q11_urgency,
q12_diagnosis, q13_therapyType — adjust in routes/families.js if form fields differ
