# Theme Information

```
Theme Name: {{THEME_NAME}}
Theme Slug: {{THEME_SLUG}} 
Description: {{DESCRIPTION}}
Category: {{CATEGORY}}
Subcategory: {{SUBCATEGORY}}
Website Type: {{WEBSITE_TYPE}}
Version:{{VERSION}}  
Tags: {{TAGS}}
Author: {{AUTHOR}}
Author Email: {{AUTHOR_EMAIL}}
Author Website: {{AUTHOR_WEBSITE}}
Demo URL: {{DEMO_URL}}
```

## Component System

This theme uses a modular component system. Components are automatically extracted from your HTML files based on class names and stored in the `theme/components/` directory.

### Component Extraction:

- Direct children of the `<body>` element are extracted as components
- Component names are derived from the first class name of each element
- For example: `<div class="topbar">` becomes `topbar.mustache`

### Usage:

To use a component in your template, use the Mustache partial syntax:

```
{{>componentName}}
```

### Example:

```html
<!-- In your page template -->
{{>topbar}} {{>header}}
<main>{{>hero-section}} {{>content-area}}</main>
{{>footer}}
```

## File Structure

```
theme/
├── partials/          # Extracted reusable components
│   ├── topbar.mustache
│   ├── header.mustache
│   ├── footer.mustache
│   └── ...
├── shortcodes/          # Extracted reusable components
│   ├── hero-banner.mustache
│   ├── faq-section.mustache
│   ├── about-section.mustache
│   └── ...
├── layouts/            # Page layouts
│   └── default.mustache
├── assets/             # Static assets
│   ├── css/
│   ├── js/
│   └── img/
├── page.mustache       # Generic page template
└── 404.mustache        # 404 error page
└── README.md        # readme file
└── screenshot.webp

```
