---
name: Lumina Gastronomy
colors:
  surface: '#051424'
  surface-dim: '#051424'
  surface-bright: '#2c3a4c'
  surface-container-lowest: '#010f1f'
  surface-container-low: '#0d1c2d'
  surface-container: '#122131'
  surface-container-high: '#1c2b3c'
  surface-container-highest: '#273647'
  on-surface: '#d4e4fa'
  on-surface-variant: '#e0bfbd'
  inverse-surface: '#d4e4fa'
  inverse-on-surface: '#233143'
  outline: '#a78a88'
  outline-variant: '#584140'
  surface-tint: '#ffb3b0'
  primary: '#ffb3b0'
  on-primary: '#68000f'
  primary-container: '#ff6b6b'
  on-primary-container: '#6d0010'
  inverse-primary: '#ae2f34'
  secondary: '#ddb7ff'
  on-secondary: '#490080'
  secondary-container: '#6f00be'
  on-secondary-container: '#d6a9ff'
  tertiary: '#4edea3'
  on-tertiary: '#003824'
  tertiary-container: '#00b17b'
  on-tertiary-container: '#003b26'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffdad8'
  primary-fixed-dim: '#ffb3b0'
  on-primary-fixed: '#410006'
  on-primary-fixed-variant: '#8c1520'
  secondary-fixed: '#f0dbff'
  secondary-fixed-dim: '#ddb7ff'
  on-secondary-fixed: '#2c0051'
  on-secondary-fixed-variant: '#6900b3'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#051424'
  on-background: '#d4e4fa'
  surface-variant: '#273647'
typography:
  display-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 48px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '700'
    lineHeight: '1.2'
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '500'
    lineHeight: '1.2'
    letterSpacing: 0.04em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  container-max-width: 1280px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 48px
---

## Brand & Style
The design system is centered on a high-end, AI-driven restaurant discovery experience. The brand personality is sophisticated, forward-thinking, and atmospheric, designed to evoke the feeling of stepping into a premier, dimly lit cocktail lounge or an exclusive dining room.

The aesthetic utilizes **Glassmorphism** as its primary structural driver. Surfaces are not solid but translucent, creating a sense of depth and layers that suggest a digital "concierge" hovering over a world of culinary content. The UI relies on vibrant accents and soft glows to guide the user's eye toward AI-generated insights and high-priority recommendations.

## Colors
This design system utilizes a "Midnight Spectrum" palette. The background is a deep, immersive midnight blue to ensure the vibrant accents feel luminous rather than overwhelming.

- **Primary (Coral):** Used for primary actions, hearting favorites, and branding elements. It provides a warm, appetizing contrast to the cool backgrounds.
- **Secondary (Electric Purple):** Reserved for AI-specific features, "Magic" recommendations, and sophisticated gradients.
- **Tertiary (Emerald):** Used for success states, high ratings, and "Open Now" indicators.
- **Surface Strategy:** Surfaces use a semi-transparent Slate (#0F172A at 60-80% opacity) to maintain the glassmorphic effect against the Midnight (#020617) base.

## Typography
The typography utilizes **Plus Jakarta Sans** for its modern, geometric character and excellent legibility in dark environments. 

- **Headlines:** Use tighter letter spacing and heavy weights to create a "premium editorial" feel.
- **Body Text:** Uses a slightly increased line height (1.6) to ensure comfort when reading restaurant reviews and descriptions against dark backgrounds.
- **AI Insights:** Use the Secondary (Purple) color for labels or small headlines to denote "Intelligence."

## Layout & Spacing
The layout follows a fluid 12-column grid for desktop and a single-column stack for mobile. 

- **Rhythm:** Spacing is strictly based on an 8px scale.
- **Depth Hierarchy:** Larger gaps (48px+) should be used between major sections to allow the glassmorphic background blurs to "breathe."
- **Margins:** Desktop views should maintain generous 48px side margins to focus the user's attention on the high-fidelity imagery of the food and venues.

## Elevation & Depth
Elevation is communicated through **translucency and blur** rather than traditional opaque shadows.

1.  **Level 1 (Base):** Deep Midnight Blue (#020617).
2.  **Level 2 (Cards):** Glassmorphic panels. Background: `rgba(15, 23, 42, 0.6)`, Backdrop Blur: `12px`, Border: `1px solid rgba(255, 255, 255, 0.1)`.
3.  **Level 3 (Modals/Overlays):** Background: `rgba(15, 23, 42, 0.9)`, Backdrop Blur: `24px`.
4.  **Glows:** High-priority items (like "AI Matches") feature a soft outer glow using the Primary or Secondary color with 20% opacity and 40px blur.

## Shapes
The design system uses a "Rounded" language to feel approachable and sophisticated.

- **Cards/Containers:** 1rem (16px) corner radius.
- **Buttons:** Fully pill-shaped (3rem) for a sleek, modern touch.
- **Input Fields:** 0.75rem (12px) corner radius.
- **Visuals:** Restaurant photography should always feature rounded corners to match the UI containers.

## Components

- **Glowing Buttons:** Primary buttons use a linear gradient (Coral to Purple) with a soft shadow of the same color. Text is always white for maximum contrast.
- **Glass Cards:** Feature a subtle top-down lighting effect via a thin 1px white border at 10% opacity. This defines the edge against dark backgrounds.
- **Sleek Sliders:** Price and distance sliders use the Secondary (Purple) for the track and a high-contrast white thumb with a 4px coral "core" glow.
- **High-Contrast Badges:** Small labels for "Michelin Star," "Trending," or "AI Match" use solid fills of Primary or Tertiary colors with black text for instant readability.
- **AI Concierge Bubble:** A floating, glassmorphic element in the bottom right corner with a continuous, slow-pulse purple glow to indicate it is "listening" or "processing."
- **Interactive Lists:** List items feature a subtle hover state where the background opacity increases by 10% and the border brightens.