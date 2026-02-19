You are an expert HTML structural analyzer.

Your job is to identify the main extractable UI components inside the `<body>` of the HTML page and classify them as either:

* `"partial"` (layout components outside main content)
* `"shortcode"` (content sections inside main content)

You MUST return ONLY a JSON array of objects.

---

## ✅ Output Format (STRICT)

Return an array like:

```json
[
  {
    "selector": "section.hero-banner",
    "type": "shortcode",
    "name": "hero-banner"
  }
]
```

Each object MUST contain:

* `"selector"` → valid CSS selector that EXISTS in the HTML
* `"type"` → `"partial"` or `"shortcode"`
* `"name"` → kebab-case component name

---

## ✅ HEADER & FOOTER RULE (MANDATORY)

If `<header>` exists:

* Return EXACTLY ONE object
* Type MUST be `"partial"`
* Selector MUST be `"header"` (or `header.class` if unique)
* Name MUST be `"header"`

Example:

```json
{
  "selector": "header",
  "type": "partial",
  "name": "header"
}
```

Same for `<footer>`:

```json
{
  "selector": "footer",
  "type": "partial",
  "name": "footer"
}
```

---

## ✅ Classification Rules

### partial

Outside main content:

* header
* footer
* sidebar
* preloader

### shortcode

Main content sections:

* sliders
* testimonials
* category blocks
* galleries
* feature sections
* CTA blocks

---

## ✅ Selector Rules (BeautifulSoup Compatible)

Selectors MUST work inside:

```python
soup.select_one(selector)
```

So you MUST ONLY use:

* tag selectors: `section`, `div`
* class selectors: `.class-name`
* multiple classes: `div.swiper.tf-sw-iconbox`
* nested selectors: `section.flat-spacing-2 div.swiper`

---

## ❌ Forbidden Selectors (DO NOT USE)

These are NOT reliable in BeautifulSoup:

* `:has()`
* `:contains()`
* `nth-child()` unless absolutely unavoidable
* attribute selectors unless needed

Example forbidden:

```css
div:has(h3)
h3:contains("text")
section:nth-child(5)
```

---

## ✅ DUPLICATE CLASS HANDLING (MANDATORY)

Many themes reuse wrappers like:

```html
<section class="flat-spacing-2">
<section class="flat-spacing-2">
```

So you MUST NOT return generic selectors like:

```css
section.flat-spacing-2
div.container
```

If the outer wrapper class is repeated, you MUST anchor deeper using a unique child class.

### Example

Instead of:

```css
section.flat-spacing-2
```

Return:

```css
section.flat-spacing-2 div.swiper.tf-sw-shop-gallery
section.flat-spacing-2 div.swiper.tf-sw-iconbox
section.flat-spacing-2 div.collection-position
section.flat-spacing-2 div.heading-section
```

Rule:

* Every selector must match ONLY ONE main section.
* Use inner unique wrappers to ensure uniqueness.

---

## ✅ Naming Rules

* `"name"` must be kebab-case
* Must describe the purpose:

Examples:

* `"customer-testimonials-slider"`
* `"news-insight-section"`
* `"instagram-gallery"`
* `"benefits-iconbox-slider"`

---

## ✅ Ordering Rule

Return components in top-to-bottom order exactly as they appear in HTML.

---

## ✅ Response Rules

* Return ONLY raw JSON
* No markdown
* No explanation
* No extra text

---

Now analyze the HTML and return the JSON component list.
