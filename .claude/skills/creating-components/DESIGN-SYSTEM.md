# Complete Design System Reference

**Source**: `/Users/franklindickinson/Projects/gym-bro/src/ui/styles.py` (611 LOC)

## Typography Scale

```css
/* Headings */
.text-h1 { font-size: 2.5rem; font-weight: 700; line-height: 1.2; }
.text-h2 { font-size: 2rem; font-weight: 600; line-height: 1.3; }
.text-h3 { font-size: 1.5rem; font-weight: 600; line-height: 1.4; }

/* Body */
.text-emphasis { font-size: 1.125rem; font-weight: 600; }
.text-body { font-size: 1rem; line-height: 1.6; }
.text-small { font-size: 0.875rem; line-height: 1.5; }
.text-caption { font-size: 0.75rem; line-height: 1.4; }
```

**Mobile Adjustments** (max-width: 768px):
- h1: 2.5rem → 2rem
- h2: 2rem → 1.75rem
- emphasis: 1.125rem → 1rem

---

## Color System

### Primary Colors
```css
--color-primary-500: #4CAF50   /* Main green */
--color-primary-600: #45A049   /* Darker green */
--color-primary-400: #66BB6A   /* Lighter green */
```

### Text Colors
```css
--color-text-primary: #FFFFFF     /* Main text */
--color-text-secondary: #B0B0B0   /* Muted text */
--color-text-tertiary: #808080    /* Very muted */
```

### Background Colors
```css
--color-bg-primary: #0E1117     /* Page background */
--color-bg-secondary: #1A1A1A   /* Card background */
--color-bg-tertiary: #2A2A2A    /* Hover states */
```

### Semantic Colors
```css
--color-success: #4CAF50
--color-error: #F44336
--color-warning: #FF9800
--color-info: #2196F3
```

### Borders
```css
--color-border: #2A2A2A
--color-border-light: #3A3A3A
```

---

## Spacing System (8pt Grid)

```css
--space-1: 0.25rem    /* 4px */
--space-2: 0.5rem     /* 8px */
--space-3: 0.75rem    /* 12px */
--space-4: 1rem       /* 16px */
--space-5: 1.25rem    /* 20px */
--space-6: 1.5rem     /* 24px */
--space-8: 2rem       /* 32px */
--space-10: 2.5rem    /* 40px */
```

**Usage**:
- `padding: var(--space-4)` → 16px padding
- `margin-top: var(--space-6)` → 24px top margin

---

## Component Classes

### Cards
```css
.card {
    background: var(--color-bg-secondary);
    padding: var(--space-4);
    border-radius: 8px;
    border: 1px solid var(--color-border);
}
```

### Activity Items
```css
.activity-item {
    background: var(--color-bg-secondary);
    padding: var(--space-4);
    border: 1px solid var(--color-border);
    border-radius: 8px;
    margin-bottom: var(--space-3);
}

.activity-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-2);
}

.activity-title {
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--color-text-primary);
}

.activity-date {
    font-size: 0.875rem;
    color: var(--color-text-secondary);
}
```

### Exercise Display
```css
.exercise-banner {
    background: var(--color-primary-500);
    color: white;
    padding: var(--space-3);
    border-radius: 6px;
    font-weight: 600;
}

.set-row {
    display: flex;
    gap: var(--space-4);
    padding: var(--space-2);
    border-bottom: 1px solid var(--color-border);
}
```

### Stats
```css
.stat-card {
    background: var(--color-bg-secondary);
    padding: var(--space-4);
    border-radius: 8px;
    text-align: center;
}

.stat-label {
    font-size: 0.75rem;
    color: var(--color-text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.stat-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--color-text-primary);
    margin-top: var(--space-2);
}
```

---

## Layout Classes

### Container
```css
.container {
    max-width: 800px;
    margin: 0 auto;
    padding: var(--space-4);
}

@media (max-width: 768px) {
    .container {
        padding: var(--space-2);
    }
}
```

### Flex Utilities
```css
.flex { display: flex; }
.flex-col { flex-direction: column; }
.items-center { align-items: center; }
.justify-between { justify-content: space-between; }
.gap-2 { gap: var(--space-2); }
.gap-4 { gap: var(--space-4); }
```

---

## Mobile Navigation

```css
.bottom-nav {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 60px;
    background: var(--color-bg-secondary);
    border-top: 1px solid var(--color-border);
    display: none;  /* Hidden by default */
}

@media (max-width: 768px) {
    .bottom-nav {
        display: flex;  /* Show on mobile */
    }
}

.nav-item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: var(--color-text-secondary);
    text-decoration: none;
    font-size: 0.75rem;
}

.nav-item.active {
    color: var(--color-primary-500);
}
```

---

## Button Styles

```css
.button-primary {
    background: var(--color-primary-500);
    color: white;
    padding: var(--space-3) var(--space-6);
    border-radius: 8px;
    border: none;
    font-weight: 600;
    cursor: pointer;
    min-height: 44px;  /* Touch target */
}

.button-primary:hover {
    background: var(--color-primary-600);
}

.button-secondary {
    background: transparent;
    color: var(--color-text-primary);
    border: 1px solid var(--color-border);
    padding: var(--space-3) var(--space-6);
    border-radius: 8px;
    cursor: pointer;
    min-height: 44px;
}
```

---

## Accessibility

### Touch Targets
- Minimum 44px height for tappable elements
- Adequate spacing between interactive elements

### Contrast Ratios
- Primary text (#FFFFFF) on dark bg: 21:1
- Secondary text (#B0B0B0) on dark bg: 7.6:1
- All meet WCAG AA standards

### Focus States
```css
:focus-visible {
    outline: 2px solid var(--color-primary-500);
    outline-offset: 2px;
}
```

---

See [COMPONENT-EXAMPLES.md](COMPONENT-EXAMPLES.md) for usage examples.
