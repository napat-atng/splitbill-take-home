---
name: SplitBill
description: A task-first workspace for precise shared expenses.
colors:
  ground: "#f3f6f3"
  surface: "#fff"
  ink: "#20392e"
  muted: "#5f7066"
  line: "#dbe4dd"
  green: "#246448"
  green-light: "#eaf3ed"
  red: "#a23730"
  red-light: "#fff1ef"
  field-border: "#c7d5cb"
  field-hover: "#72927e"
  focus: "#4d9170"
  primary-hover: "#184c34"
  toolbar: "#e7eee7"
  disabled-field: "#edf1ee"
  avatar-ground: "#edf2ed"
  avatar-ink: "#4d7057"
  success-ground: "#e1efe5"
  success-ink: "#214f37"
  error-ink: "#8a2b24"
typography:
  headline:
    fontFamily: "Arial, Helvetica, sans-serif"
    fontSize: "clamp(27px, 3vw, 36px)"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.03em"
  title:
    fontFamily: "Arial, Helvetica, sans-serif"
    fontSize: "20px"
    fontWeight: 600
    lineHeight: 1.5
    letterSpacing: "-0.02em"
  item-title:
    fontFamily: "Arial, Helvetica, sans-serif"
    fontSize: "16px"
    fontWeight: 600
    lineHeight: 1.5
  body:
    fontFamily: "Arial, Helvetica, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Arial, Helvetica, sans-serif"
    fontSize: "13px"
    fontWeight: 600
    lineHeight: 1.5
  metadata:
    fontFamily: "Arial, Helvetica, sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.5
  money:
    fontFamily: "Arial, Helvetica, sans-serif"
    fontSize: "19px"
    fontWeight: 600
    lineHeight: 1.5
rounded:
  panel: "14px"
  control: "7px"
  badge: "6px"
  split-group: "8px"
  split-option: "5px"
  avatar: "50%"
spacing:
  step-4: "4px"
  step-7: "7px"
  step-8: "8px"
  step-10: "10px"
  step-12: "12px"
  step-16: "16px"
  step-19: "19px"
  step-20: "20px"
  step-21: "21px"
  step-24: "24px"
  step-26: "26px"
components:
  button-primary:
    backgroundColor: "{colors.green}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
    padding: "12px 18px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-text:
    backgroundColor: "transparent"
    textColor: "{colors.green}"
    padding: "6px"
  button-danger:
    backgroundColor: "{colors.red}"
    textColor: "{colors.surface}"
    rounded: "{rounded.badge}"
    padding: "9px 12px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "10px 12px"
  panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.panel}"
    padding: "26px"
  expense-count:
    backgroundColor: "{colors.green-light}"
    textColor: "{colors.green}"
    rounded: "{rounded.badge}"
    padding: "4px 9px"
  split-option-selected:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.green}"
    rounded: "{rounded.split-option}"
    padding: "10px 8px"
---

# Design System: SplitBill

## Overview

**Creative North Star: "Task-first expense workspace"**

SplitBill uses a task-first expense workspace: mist green ground, white work areas, deep green text and actions, and restrained borders. Compact hierarchy supports repeated form entry and financial comparison without imagery.

Visible allocation, aligned numbers and explicit balance labels make precision legible. Plain-language feedback keeps loading, errors and safe retries within the working context.

**Key Characteristics:**
- Quiet green surfaces and bordered work areas.
- Tabular money with explicit direction labels.
- Visible allocation and safe retry states.

## Colors

The primary palette is deep green on mist green and white; muted red distinguishes payable money and destructive feedback. Frontmatter values are normative.

### Primary
- **Deep green:** actions, wordmark, receivable balances, selected split choice and interactive text.
- **Light green:** informational expense-count background.

### Secondary
- **Muted red:** payable balances, invalid inputs and delete actions; pale red backs errors and destructive confirmation.

### Neutral
- **Mist ground / white surface:** page and work areas.
- **Deep ink / muted ink:** main content and supporting text.
- **Soft line:** panel boundaries and row dividers. Toolbar and avatar tones quietly group content.
- **Field border / field hover / focus:** visible field boundaries and keyboard navigation.
- Success and error ink/background pairs support plain-language feedback.

**The Direction Label Rule.** Pair balance color with the written state: To receive, To pay, or Settled up.

## Typography

**Display Font:** No separate display family; page headings use Arial, Helvetica, sans-serif.
**Body Font:** Arial, Helvetica, sans-serif.

**Character:** Familiar, compact interface type prioritizes labels and financial values. Arial is the accepted system choice for this Operate surface.

### Hierarchy
- **Headline:** responsive page heading, semibold and tightly tracked, with balanced wrapping.
- **Title:** semibold section headings, with slightly tightened tracking.
- **Item title:** expense descriptions, allowed to wrap anywhere.
- **Body:** normal interface copy.
- **Label:** semibold field labels and split choices.
- **Metadata:** supporting copy and actions; member descriptors and footer use a smaller 11px tier.
- **Money:** semibold balance amounts; amount entry uses the same size at weight 500. Expense totals use 17px, reducing to 15px at the narrow breakpoint.

**The Aligned Money Rule.** Use tabular numerals for entered amounts, allocation values, balance amounts, expense totals and share details.

## Layout

The centered shell has maximum width 1184px and 36px horizontal padding. The desktop header is at least 96px tall. The selector toolbar uses 180px, minmax(220px, 340px), and remaining-space tracks. The workspace uses minmax(0, 1.35fr) and minmax(0, 1fr) with a 24px gap: form left, balances right. History follows below with 24px separation. Panels use the frontmatter padding; form fields use 20px vertical gaps and paired fields use 16px gaps.

At 760px and below, workspace areas stack form-first, shell padding becomes 18px, panels use 21px padding, and workspace/history separation becomes 19px. The selector toolbar retains two tracks at 1:1.4. Header note, currency tag and group hint hide; delete confirmation stacks. At 380px and below, shell padding becomes 12px, panels use 17px, and paired fields use 12px gaps.

## Elevation & Depth

Resting panels are flat, separated by tone and pale borders. The selected split option uses the only box shadow: `0 2px 4px #1e3b2910`. Keyboard focus is a `3px solid #4d9170` outline offset by 3px.

**The Quiet Surface Rule.** Use surface color and borders for resting panels; the selected split option alone carries the small selection shadow.

## Shapes

Soft rectangular panels contain smaller rounded fields, actions and badges; the exact radius vocabulary is in the frontmatter. Member avatars are circles. One-pixel borders structure containers and rows. Split controls nest small rounded options within a rounded group.

## Components

### Buttons
Primary actions use solid green, white semibold text and minimum height 46px. The save action spans the form and separates its label from an inline SVG arrow. Hover darkens the fill over 150ms. Underlined text actions have minimum height 36px; delete text is red. Filled destructive confirmation has minimum height 38px. All controls use the shared focus outline. Disabled buttons and selects use opacity 0.55 and a not-allowed cursor. No custom active-state treatment is defined.

### Cards / Containers
White bordered panels use responsive padding and the panel radius. The tinted selector toolbar groups identity and group choices. Resting panels have no shadow.

### Inputs / Fields
White fields use a one-pixel field border, minimum height 45px and a 120ms border-color transition. Hover shifts the border; invalid inputs use red. Disabled inputs have a muted background. Labels stay visible above fields. Exact-share inputs are right aligned, 112px wide and at least 38px tall. Checkboxes and radios use the green accent at 16px dimensions.

### Split selector and allocation
Equal/exact modes are native radio choices in a two-column segmented surface. Selection adds white fill, green text and the small selection shadow. Allocation rows are at least 68px tall, with dividers, member checkboxes, circular initials and right-aligned values. Excluded avatars and preview values fade to opacity 0.55. The live summary names unallocated or overallocated money. Exact saving remains disabled until valid selected shares equal the total.

### Balance and expense rows
Balances pair identity with a right-aligned signed amount and direction label. Expenses separate description/details from total/actions. Native details disclose per-person shares. The pale green expense-count badge is informational. Only the payer sees deletion; inline confirmation explains balance recalculation.

### Feedback
Muted copy conveys loading and empty states inside work areas. Pale green success notices have dismiss actions; pale red errors expose retry where applicable. Saving and uncertain responses lock relevant controls, preserve the pending expense and expose saving/retry labels. Reduced-motion preference removes transitions and animations.

## Do's and Don'ts

### Do:
- **Do** retain visible labels, keyboard focus and plain-language status messages.
- **Do** show allocation before saving and distinguish money to receive from money to pay.
- **Do** preserve entries and expose safe retry when the save result is uncertain.

### Don't:
- **Don't** use balance color as the only indicator of money direction.
- **Don't** enable exact-split saving before selected shares equal the total.
- **Don't** turn the page heading into a decorative display treatment.
