# Documentation JavaScript

This directory contains JavaScript files for the MkDocs documentation site with full TypeScript-based type checking.

## Type Checking

### Setup

```bash
npm install
```

### Run Type Checking

```bash
# Run type checking once
npm run typecheck

# Watch mode (continuous type checking)
npm run typecheck:watch
```

### Configuration

- **jsconfig.json**: TypeScript configuration for JavaScript files with strict type checking enabled
- **package.json**: npm scripts and TypeScript dependency

## JavaScript Files

### `javascripts/extra.js`

Link enhancement script that:
- Opens external links in new tabs with `noopener noreferrer` security attributes
- Opens file downloads (PDF, ZIP, etc.) in new tabs
- Excludes navigation and footer links from external link processing

**Features:**
- Fully typed with JSDoc comments
- Strict TypeScript type checking
- Browser DOM API types
- Error handling for invalid URLs

## Type Checking Benefits

1. **Catch errors early**: TypeScript catches type errors before runtime
2. **Better IDE support**: Full autocomplete and inline documentation
3. **Self-documenting code**: JSDoc comments provide type information and documentation
4. **Refactoring safety**: Type checking ensures changes don't break existing code

## JSDoc Examples

The code uses comprehensive JSDoc annotations:

```javascript
/**
 * All anchor elements with href attributes in the document.
 * @type {NodeListOf<HTMLAnchorElement>}
 */
const links = document.querySelectorAll('a[href]');
```

## CI/CD Integration

You can add type checking to your CI/CD pipeline:

```yaml
- name: Type check JavaScript
  run: |
    cd docs
    npm ci
    npm run typecheck
```
