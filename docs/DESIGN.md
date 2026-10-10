# Inspyred Dev Design Principles

Author: **Taylor B. | Inspyre-Softworks.**

## Product character

Inspyred Dev should feel deliberately designed rather than merely functional. It should be fast,
quiet, modern, and comfortable enough to leave open all day. Visual polish must not come at the
expense of discoverability.

## Controls own their help contract

Reusable interactive components should carry the information needed to explain themselves.
Where practical, a control has:

- a semantic action/label;
- an icon or glyph;
- a tooltip;
- contextual help text or a help ID;
- an accessible name/description;
- an optional keyboard shortcut.

Help is part of the control contract, not documentation bolted on later.

## Icons do not become a guessing game

Icons may be used for compactness, but important controls must support persistent text labels.
The appearance setting must allow at least:

- **Icons + text**
- **Icons only**

When text labels are enabled, icons remain visible. Tooltips remain available in either mode.

## Tooltips by default

Interactive controls should expose a tooltip wherever practical. A useful tooltip may explain the
action and include its shortcut rather than merely parroting a visible label. Tooltips should also
appear for keyboard focus where the toolkit permits it.

## Themes are structural

System, light, and dark modes are first-class behavior. Colors should come from a centralized theme
controller/design-token layer rather than being scattered as literals throughout individual views.
This is intentionally compatible with richer themes later without requiring them in the MVP.

## Capture must preserve flow

The core interaction is deliberately short:

1. Notice something.
2. Invoke capture.
3. Type a sentence.
4. Press Enter.
5. Return to work.

Classification and implementation planning must never become prerequisites to capturing a thought.
The local inbox exists so network availability and GitHub latency cannot block capture.

## The UI does not own business logic

QML owns presentation and interaction composition. Python owns domain models, persistence, provider
integration, capture services, and future AI handoff. UI components invoke services; they do not
become the services.
