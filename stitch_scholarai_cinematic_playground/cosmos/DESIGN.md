---
name: COSMOS
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#3a3939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1c1b1b'
  surface-container: '#201f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353534'
  on-surface: '#e5e2e1'
  on-surface-variant: '#bac9cc'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#313030'
  outline: '#849396'
  outline-variant: '#3b494c'
  surface-tint: '#00daf3'
  primary: '#c3f5ff'
  on-primary: '#00363d'
  primary-container: '#00e5ff'
  on-primary-container: '#00626e'
  inverse-primary: '#006875'
  secondary: '#f5fff3'
  on-secondary: '#003919'
  secondary-container: '#34ff8c'
  on-secondary-container: '#007239'
  tertiary: '#f2e9ff'
  on-tertiary: '#3c0090'
  tertiary-container: '#d9c8ff'
  on-tertiary-container: '#6c00f7'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#9cf0ff'
  primary-fixed-dim: '#00daf3'
  on-primary-fixed: '#001f24'
  on-primary-fixed-variant: '#004f58'
  secondary-fixed: '#60ff98'
  secondary-fixed-dim: '#00e478'
  on-secondary-fixed: '#00210c'
  on-secondary-fixed-variant: '#005227'
  tertiary-fixed: '#e9ddff'
  tertiary-fixed-dim: '#d1bcff'
  on-tertiary-fixed: '#23005b'
  on-tertiary-fixed-variant: '#5700c9'
  background: '#131313'
  on-background: '#e5e2e1'
  surface-variant: '#353534'
typography:
  display-lg:
    fontFamily: Playfair Display
    fontSize: 64px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-xl:
    fontFamily: Playfair Display
    fontSize: 48px
    fontWeight: '600'
    lineHeight: '1.2'
  headline-lg:
    fontFamily: Playfair Display
    fontSize: 32px
    fontWeight: '500'
    lineHeight: '1.3'
  headline-lg-mobile:
    fontFamily: Playfair Display
    fontSize: 28px
    fontWeight: '600'
    lineHeight: '1.3'
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1.0'
    letterSpacing: 0.08em
  terminal-code:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 24px
  margin-desktop: 64px
  margin-mobile: 20px
  container-max: 1440px
---

## Brand & Style

This design system is built upon the "Deep Space Anomaly" aesthetic—a sophisticated blend of high-fidelity cinematic visuals and rigorous editorial structure. It is designed to evoke a sense of wonder, intelligence, and cutting-edge discovery. The personality is authoritative yet ethereal, balancing the cold precision of space travel with the organic, fluid beauty of celestial phenomena.

The visual language draws heavily from **Glassmorphism** and **Minimalism**. It utilizes high-contrast typography and liquid-like translucent layers to create a sense of depth that feels infinite. The interface should feel less like a standard software application and more like a high-tech observatory console or a premium scientific journal from the future.

## Colors

The palette is anchored in **Absolute Black (#000000)** to represent the vacuum of space, providing the necessary contrast for the "aurora" accents. 

- **Primary (Electric Blue):** Used for critical actions, interactive states, and focal points. It represents the energy of propulsion and data.
- **Secondary (Emerald Aurora):** Used for success states, biological or environmental data, and soft ambient glows.
- **Surface Strategy:** Backgrounds are deep and void-like. UI surfaces are "Liquid Glass"—semi-transparent dark panels that use background blurs to let the underlying aurora gradients bleed through.
- **Accents:** Use thin, high-clarity white or cyan strokes (10-15% opacity) to define edges of glass panels, mimicking the way light catches on a lens.

## Typography

The typography in the design system follows an editorial hierarchy. **Playfair Display** provides a classical, sophisticated contrast to the technical environment, used exclusively for headlines and impactful statements. **Inter** handles all functional and body text to ensure maximum legibility at high speeds.

For data-heavy sections or logs, a monospaced font is introduced to maintain the "terminal" aesthetic. Headlines should prioritize generous tracking and tight line heights for a cinematic look. Labels are always uppercase with increased letter spacing to mimic instrumentation panels.

## Layout & Spacing

This design system employs a **Fluid Grid** model with a 12-column structure for desktop and a 4-column structure for mobile. 

- **Breathing Room:** High whitespace (negative space) is mandatory. It reinforces the theme of the "void" and prevents the high-fidelity glass elements from feeling cluttered.
- **Rhythm:** All spacing is based on a 4px baseline. Components should use generous internal padding (typically 24px or 32px) to support the "editorial" feel.
- **Centering:** Key marketing or storytelling sections should use a centered fixed-width container to maintain focus, while functional dashboard views should expand to fill the viewport width.

## Elevation & Depth

Depth is not created through traditional shadows, but through **Luminosity and Refraction**.

1.  **Backdrop Blur:** Glass surfaces must use a heavy backdrop blur (between 20px and 40px) to simulate thick, liquid glass.
2.  **Inner Glows:** Instead of drop shadows, use a 1px inner border with a slight top-down gradient (white at 20% to white at 5%) to simulate a light source from above hitting the edge of the glass.
3.  **Tonal Layers:** Objects closer to the user are lighter and more translucent; objects further away are darker and more opaque, blending into the #000000 background.
4.  **Aurora Underlays:** Place soft, blurred radial gradients of Emerald and Electric Blue behind glass cards to create an "anomaly" effect that shifts as the user scrolls.

## Shapes

The shape language is **Rounded (Level 2)**. This softens the technical "coldness" of the dark palette and aligns with the fluid, "liquid" nature of the glass elements. 

- **Standard Elements:** 8px (0.5rem) for inputs and smaller UI components.
- **Cards/Containers:** 16px (1rem) for primary content containers.
- **Interactive Orbs:** Elements like the main "anomaly" or primary CTA buttons can use full pill-rounding to feel more organic and touchable.

## Components

### Buttons
- **Primary:** Solid Electric Blue with a soft outer glow (bloom effect). Text is Inter Bold, uppercase.
- **Secondary:** Transparent background with a 1px white glass-outline. On hover, the inner glass fills slightly with a 10% white tint.
- **Ghost:** No border, Electric Blue text, used for low-priority navigation.

### Cards
- Surfaces must be `rgba(5, 5, 5, 0.6)` with a `backdrop-filter: blur(30px)`.
- Every card requires a `1px` stroke using the `glass_stroke` variable.
- Padding should be 32px to maintain the editorial look.

### Terminal Logs
- Containers are solid `#050505` with a subtle Electric Blue left-accent border.
- Text uses the `terminal-code` style in a dimmed grey or soft green.

### Input Fields
- Dark, recessed wells with a 1px bottom-only or full-outline stroke that glows Electric Blue when focused.

### Icons
- Lucide-style, thin-stroke (1.5px) icons. Use Electric Blue for active states and subtle white for inactive states. Icons should never be filled; they must remain linear to match the high-tech aesthetic.