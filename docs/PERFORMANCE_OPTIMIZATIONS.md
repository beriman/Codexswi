# Performance Optimizations

This document outlines the performance optimizations implemented for the Sensasiwangi.id web application.

## Overview

The application uses HTMX, vanilla JavaScript, and CSS with Supabase as the database. All optimizations focus on reducing bundle size, improving load times, and enhancing the user experience without compromising the tech stack.

## Implemented Optimizations

### 1. Asset Minification

**Location**: `scripts/minify_assets.py`

All CSS and JavaScript files are now minified for production use:

- **CSS Reduction**: ~18-20% size reduction (128KB → ~105KB)
- **JavaScript Reduction**: ~20-25% size reduction (30KB → ~24KB)

**Files Minified**:
- `base.css`: 47.5KB → 38.8KB (18.4% reduction)
- `brand.css`: 15KB → 12KB (20.1% reduction)
- `dashboard.css`: 12.3KB → 9.9KB (19.3% reduction)
- All other CSS and JS files similarly optimized

**Usage**:
```bash
python3 scripts/minify_assets.py
```

### 2. Resource Hints

**Location**: `src/app/web/templates/base.html`

Added DNS prefetch and preconnect hints for external resources:

```html
<!-- Resource Hints for Performance -->
<link rel="dns-prefetch" href="https://fonts.googleapis.com" />
<link rel="dns-prefetch" href="https://fonts.gstatic.com" />
<link rel="dns-prefetch" href="https://unpkg.com" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
```

**Benefits**: Reduces DNS lookup time and establishes early connections to external domains.

### 3. Optimized Font Loading

**Location**: `src/app/web/templates/base.html`

Implemented non-blocking font loading strategy:

```html
<link
  href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap"
  rel="stylesheet"
  media="print"
  onload="this.media='all'"
/>
```

**Benefits**: 
- Prevents font loading from blocking page render
- Uses `media="print"` trick for async loading
- Includes `font-display: swap` in Google Fonts URL

### 4. GZip Compression

**Location**: `src/app/core/application.py`

Added GZip compression middleware to compress responses:

```python
if settings.enable_compression:
    app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=6)
```

**Benefits**: 
- Typical 60-80% reduction in transfer size
- Enabled by default (configurable via `ENABLE_COMPRESSION` env var)

### 5. Aggressive Caching Headers

**Location**: `src/app/core/static_files.py`

Custom static file serving with optimized cache headers:

```python
class CachedStaticFiles(StaticFiles):
    """Static files middleware with aggressive caching for immutable assets."""
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # Add cache headers for static assets
        headers[b"Cache-Control"] = b"public, max-age=31536000, immutable"
        headers[b"Vary"] = b"Accept-Encoding"
```

**Benefits**:
- 1-year cache for versioned static assets
- Immutable flag tells browsers to never revalidate
- Assets are versioned via query string (`?v=2024051901`)

### 6. Deferred JavaScript Loading

**Location**: All templates

All JavaScript files load with `defer` attribute:

```html
<script src="..." defer></script>
```

**Benefits**:
- Scripts don't block HTML parsing
- Scripts execute in order after DOM is ready
- Better perceived page load time

### 7. Conditional Minified Assets

**Location**: `src/app/core/config.py`, `src/app/web/templates/__init__.py`

Added configuration to toggle between development and production assets:

```python
# In config.py
use_minified_assets: bool = False

# In templates
{{ url_for('static', path='css/base.min.css') if use_minified else url_for('static', path='css/base.css') }}
```

**Benefits**:
- Easy switching between dev and prod builds
- Maintains readable code in development
- Optimized delivery in production

### 8. Extracted Inline Scripts

**Location**: `src/app/web/static/js/newsletter.js`

Moved inline JavaScript to separate cacheable files:

- Newsletter form handling → `newsletter.js`
- Other inline scripts can be extracted similarly

**Benefits**:
- Better caching (inline scripts can't be cached)
- Reduced HTML size
- Easier maintenance and testing

### 9. HTMX Optimization

**Location**: `src/app/web/templates/base.html`

Added module preload for HTMX:

```html
<link rel="modulepreload" href="https://unpkg.com/htmx.org@1.9.10" />
<script src="https://unpkg.com/htmx.org@1.9.10" defer></script>
```

**Benefits**:
- Browser preloads HTMX while parsing HTML
- HTMX executes after DOM is ready (defer)
- Maintains full HTMX functionality

## Performance Metrics

### Before Optimizations
- Total CSS: ~128KB uncompressed
- Total JS: ~30KB uncompressed
- No caching headers
- No compression
- Blocking font loading
- Inline scripts

### After Optimizations
- Total CSS: ~105KB minified (~60KB gzipped)
- Total JS: ~24KB minified (~14KB gzipped)
- 1-year cache for static assets
- GZip compression enabled
- Non-blocking font loading
- Extracted, cached scripts

### Estimated Improvements
- **Initial Load**: 30-40% faster (reduced payload + compression)
- **Repeat Visits**: 70-80% faster (aggressive caching)
- **Time to Interactive**: 20-30% improvement (deferred scripts)
- **Largest Contentful Paint**: 15-25% improvement (font optimization)

## Configuration

### Environment Variables

```bash
# Enable minified assets (production)
USE_MINIFIED_ASSETS=true

# Enable GZip compression (default: true)
ENABLE_COMPRESSION=true

# Static asset version (for cache busting)
STATIC_ASSET_VERSION=2024051901
```

### Production Deployment

1. Minify assets:
   ```bash
   python3 scripts/minify_assets.py
   ```

2. Set environment variables:
   ```bash
   export USE_MINIFIED_ASSETS=true
   export ENABLE_COMPRESSION=true
   ```

3. Deploy application

### Development Mode

Keep `USE_MINIFIED_ASSETS=false` for easier debugging with readable source files.

## Future Optimizations

### Potential Improvements

1. **Critical CSS Extraction**: Extract above-the-fold CSS and inline it
2. **Image Optimization**: Add WebP support, lazy loading, responsive images
3. **HTTP/2 Server Push**: Push critical assets before they're requested
4. **Service Worker**: Implement offline-first caching strategy
5. **Brotli Compression**: Add Brotli for even better compression than GZip
6. **CSS Purging**: Remove unused CSS rules in production
7. **Code Splitting**: Split CSS/JS by route for smaller initial bundles
8. **Preload Key Requests**: Preload critical API calls
9. **Resource Prioritization**: Use `fetchpriority` for critical resources
10. **CDN Integration**: Serve static assets from CDN

### Monitoring

Consider adding:
- Web Vitals tracking (Core Web Vitals)
- Real User Monitoring (RUM)
- Lighthouse CI for automated performance testing
- Bundle size tracking in CI/CD

## Testing

### Verify Optimizations

1. **Check minified files exist**:
   ```bash
   ls -lh src/app/web/static/css/*.min.css
   ls -lh src/app/web/static/js/*.min.js
   ```

2. **Test compression**:
   ```bash
   curl -H "Accept-Encoding: gzip" -I http://localhost:8000/static/css/base.min.css
   # Should include: Content-Encoding: gzip
   ```

3. **Verify cache headers**:
   ```bash
   curl -I http://localhost:8000/static/css/base.min.css?v=2024051901
   # Should include: Cache-Control: public, max-age=31536000, immutable
   ```

4. **Lighthouse audit**:
   ```bash
   lighthouse http://localhost:8000 --view
   ```

## Troubleshooting

### Minification Issues

If minified assets cause issues:
1. Set `USE_MINIFIED_ASSETS=false`
2. Check browser console for errors
3. Verify minified files exist and are valid
4. Re-run minification script

### Cache Issues

If changes aren't reflected:
1. Update `STATIC_ASSET_VERSION` in config
2. Clear browser cache
3. Use incognito/private browsing
4. Check Network tab for cache hits

### Compression Issues

If compression causes problems:
1. Set `ENABLE_COMPRESSION=false`
2. Check client Accept-Encoding headers
3. Verify middleware order in application.py

## Maintainers

When modifying CSS or JavaScript:
1. Edit source files (non-minified versions)
2. Run minification script: `python3 scripts/minify_assets.py`
3. Test both minified and non-minified versions
4. Update `STATIC_ASSET_VERSION` if deploying

## References

- [Web.dev Performance Guide](https://web.dev/performance/)
- [MDN Web Performance](https://developer.mozilla.org/en-US/docs/Web/Performance)
- [HTMX Documentation](https://htmx.org/docs/)
- [FastAPI Performance](https://fastapi.tiangolo.com/advanced/middleware/)
