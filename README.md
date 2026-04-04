# Existential Gateway™ — Where Technology Meets Consciousness

**Live Site:** [www.existentialgateway.com](https://www.existentialgateway.com)  
**Owner:** Existential Gateway™, LLC | Maegan Soria-Wiley  
**Stack:** HTML · CSS · JavaScript · GitHub Pages · Supabase · Stripe · Etsy

---

## Overview

Existential Gateway is a consumer-facing platform combining civic intelligence, Biblical prophecy analysis, monetary reset tracking, and handcrafted orgonite products. The platform serves citizens who want real answers — AI tools that engage faith and financial sovereignty frameworks without hedging, disclaimers, or secular reframing.

AI tools are hosted on [QuantusData.ai](https://quantusdata.ai) and accessible via The Gateway Plan subscription.

---

## Site Structure

```
www.existentialgateway.com (GitHub Pages)
    └── index.html          # Homepage
    └── tools.html          # Gateway Plan tools directory
    └── pricing.html        # Pricing page
    └── orgonite.html       # Orgonite shop (links to Etsy)
    └── about.html          # About page
    └── contact.html        # Contact page
    └── terms.html          # Terms of Service & Privacy Policy
```

---

## The Gateway Plan — $9.99/month

All 5 civic and faith intelligence tools included:

| Tool | Description |
|------|-------------|
| 💼 Investment Analyzer | Stocks, crypto, ETFs, and prediction markets including Polymarket and Kalshi |
| ✝️ End Times Prophecy Analyzer | 16-tab Biblical prophecy tracking — Matthew 24, Revelation seals, Jubilee calendar, Middle East watch, Rapture analysis, live solar data |
| 💰 Monetary Reset Tracker | XRP/Ripple, BRICS, FOREX revaluations, Gods vs Beast financial system, Metallicus, US Treasury policy |
| 💸 US Debt Clock Analyzer | Live Treasury debt data, paradigm shift analysis, gold/silver transition indicators |
| 📰 Media Bias Analyzer | Nonpartisan bias detection — equal scrutiny applied to all outlets regardless of political lean |
| 🏛️ Public Accountability Tracker | Elected official performance scoring sourced from .gov records only |

---

## What Makes Existential Gateway Different

**Faith-Forward Intelligence** — AI specifically instructed to engage Biblical prophecy, monetary reset, and spiritual frameworks without secular reframing or disclaimers.

**Decisive Analysis** — No hedging. Every tool delivers concrete findings, definitive conclusions, and actionable recommendations.

**Current Facts** — Updated with confirmed 2025-2026 facts: Pope Leo XIV, GENIUS Act, XRP regulatory clarity, Trump executive orders.

**Nonpartisan Civic Tools** — Democrats and Republicans held to identical standards. Only documented actions and outcomes matter.

**URL Ingestion** — Paste any news article or government report URL into any tool text box. The AI fetches the content and analyzes it through that tool's specialty framework.

---

## Orgonite Shop

Physical orgonite products sold through Etsy:  
**[etsy.com/shop/ExistentialGateway](https://www.etsy.com/shop/ExistentialGateway)**

- 293+ Sales · 5.0 ★ (48 Reviews)
- Handcrafted orgonite pocket pieces inspired by the US Debt Clock
- Collections: Quantum Leap, Eagle Rising, Golden Age, Golden Age Ultra Gold, Blackout X, Revolution, Silver Breakout
- Copper Triskelion Coils available separately

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Hosting | GitHub Pages (www.existentialgateway.com) |
| Auth & Subscriptions | Supabase (shared with QuantusData.ai) |
| Payments | Stripe |
| Product Sales | Etsy |
| AI Tools Backend | QuantusData.ai (DigitalOcean VPS) |
| DNS | Wix (A records pointing to GitHub Pages IPs) |

---

## Navigation

All 7 main pages feature:
- Golden City logo (gothic arch + city skyline + IXOYE + astrological clock)
- Hamburger menu with slide-in navigation
- Floating "Subscribe Now" button (links to Stripe Gateway Plan)
- SSL secured (Let's Encrypt via GitHub Pages)

---

## Branding

**Colors:** Deep navy (#0a1628) · Gold (#c9a84c) · White  
**Fonts:** Cinzel (serif headings) · Rajdhani (sans body) · Space Mono (monospace accents)  
**Logo:** Golden City — gothic arch with Earth/eye of consciousness, astrological clock ring, IXOYE inscription, crown at apex  
**Favicon:** Compact Golden City SVG

---

## Subscription Flow

```
User visits existentialgateway.com
    → Clicks "Subscribe Now" (floating button or pricing page)
    → Stripe checkout ($9.99/mo Gateway Plan)
    → Stripe webhook → Supabase Edge Function
    → Subscription saved to Supabase subscriptions table
    → User logs in at quantusdata.ai/dashboard.html
    → Magic link sent to email (Supabase auth)
    → Dashboard shows Gateway Plan tools
```

---

## Deployment

```bash
# All changes deployed via GitHub Pages
git add .
git commit -m "description"
git push origin main
# Site updates automatically within 2-3 minutes
```

---

## Related Repository

**QuantusData.ai** (B2B platform + tool backends): [github.com/soriamaegan-dev/quantusdata.ai](https://github.com/soriamaegan-dev/quantusdata.ai)

---

© 2026 Existential Gateway™, LLC · Grand Prairie, Texas · existentialgateway@gmail.com
