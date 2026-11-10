---
version: alpha
name: APEX Telemetry
description: High-density biometric and kinematic roller coaster telemetry cockpit contrasting the slow mechanical climb with the breathless vertical drop.
colors:
  primary: '#BE123C'
  on-primary: '#FFFFFF'
  secondary: '#B45309'
  on-secondary: '#FFFFFF'
  background: '#09090B'
  on-background: '#FAFAFA'
  surface: '#18181B'
  on-surface: '#F4F4F5'
  muted: '#A1A1AA'
  outline: 'rgba(255, 255, 255, 0.08)'
typography:
  display:
    fontFamily: Space Grotesk
    fontSize: 3.5rem
    fontWeight: '700'
    lineHeight: 1.05
    letterSpacing: -0.03em
  body:
    fontFamily: Space Grotesk
    fontSize: 1rem
    fontWeight: '400'
    lineHeight: 1.6
    letterSpacing: 0em
  mono:
    fontFamily: JetBrains Mono
    fontSize: 0.875rem
    fontWeight: '600'
    lineHeight: 1.4
    letterSpacing: -0.01em
rounded:
  sm: 4px
  md: 8px
  lg: 16px
  card: 24px
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  container: 1400px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.md}"
    padding: 12px
  button-secondary:
    backgroundColor: "{colors.secondary}"
    textColor: "{colors.on-secondary}"
    rounded: "{rounded.md}"
    padding: 12px
  badge:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.muted}"
    rounded: "{rounded.full}"
    padding: 6px
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.card}"
    padding: 24px
---

# Design System: APEX Telemetry

## Overview

A cockpit-dense, dark-mode kinematic and biometric telemetry interface built around the dual nature of a hyper-coaster: the tense, mechanical anticipation of the slow chain-lift climb contrasted against the violent, breathless freefall of an 89.5-degree vertical drop.

### Configuration Dials
- **Creativity**: `9` (Asymmetric dual-phase split, kinetic spline visualizations, dramatic scale contrast)
- **Density**: `8` (Cockpit telemetry with monospace numeric readouts and 1px hairline dividers)
- **Variance**: `8` (Asymmetric Bento architecture contrasting Phase I and Phase II)
- **Motion Intent**: `7` (Real-time telemetry scrubbing and spring-physics gauge needles)

## Colors

- **Background (#09090B):** "Obsidian Track" — deep Zinc-950 void canvas providing maximum contrast for telemetry readouts.
- **Surface (#18181B):** "Cockpit Carbon" — elevated instrument panels with 1px translucent hairline borders.
- **Primary (#BE123C):** "Adrenaline Crimson" — used for Phase II (The Breathless Drop), peak G-force alerts, and heart-rate spikes.
- **Secondary (#B45309):** "Chain-Lift Amber" — used for Phase I (The Slow Climb), mechanical tension gauges, and potential energy accumulation.
- **On-Surface (#F4F4F5):** "Titanium Readout" — crisp primary typography and numeric telemetry.
- **Muted (#A1A1AA):** "Sensor Slate" — axis labels, units, and secondary telemetry metadata.

## Typography

- **Display Headlines:** Space Grotesk Bold (`700`) with tight tracking (`-0.03em`) for phase headers and peak telemetry callouts.
- **Body Copy:** Space Grotesk Regular (`400`) for narrative annotations and ride physics summaries.
- **Monospace Telemetry:** JetBrains Mono Semi-Bold (`600`) for all numeric counters (`4.9G`, `186 BPM`, `420 FT`, `0.0 L/MIN`).

## Layout

- **Asymmetric Dual-Phase Split:** The viewport divides into two distinct kinetic zones: Phase 01 (The Slow Climb) on the left and Phase 02 (The Breathless Drop) on the right, bridged by a full-width interactive 3D track elevation spline.
- **Containment:** Max-width 1400px container with 1px structural hairline borders and compact 16px grid gaps.

## Elevation & Depth

- **Instrument Panels:** Elevated Cockpit Carbon (`#18181B`) cards with 1px translucent borders (`rgba(255, 255, 255, 0.08)`) and subtle ambient shadows.

## Shapes

- **Telemetry Cards:** `24px` (`1.5rem`) corner radius on primary Bento containers.
- **Controls & Triggers:** `8px` corner radius on interactive segmented controls.
- **Status Pills:** `9999px` full pill badges for live sensor indicators.

## Components

- **Track Profile Spline:** Interactive SVG/Canvas elevation curve highlighting the slow 45-degree chain-lift ascent in Amber and the 89.5-degree vertical plunge in Crimson.
- **Biometric Vital Cards:** High-contrast monospace readouts for Heart Rate (`186 BPM`), Vertical Acceleration (`+4.9G` / `-1.2G Airtime`), and Respiration Rate (`0.0 L/min — Breathless Zone`).

## Do's and Don'ts

- Do contrast the slow mechanical climb (Amber) against the breathless drop (Crimson).
- Do render all telemetry numbers, speeds, angles, and biometrics in monospace typography.
- Don't use pure black (`#000000`) or neon purple gradients.
- Don't use circular loading spinners or generic 3-equal-card rows.
