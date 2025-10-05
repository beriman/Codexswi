# Vercel Deployment Guide

This document explains how to deploy the Sensasiwangi.id application to Vercel.

## Project Structure

The application uses Vercel's modern serverless functions approach:
- `api/index.py` - Main entry point for the serverless function (exports `handler` via Mangum)
- `src/` - Application source code
- `vercel.json` - Vercel configuration using rewrites (not legacy builds)
- `mangum` - ASGI adapter that allows FastAPI to run on serverless platforms

## Required Environment Variables

Configure the following environment variables in your Vercel project settings:

### Required for Application to Function

1. **SESSION_SECRET** (Required)
   - Description: Secret key for session encryption
   - Minimum length: 32 characters (in production)
   - Example: Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`

2. **SUPABASE_URL** (Required)
   - Description: Your Supabase project URL
   - Example: `https://xxxxxxxxxxxxx.supabase.co`

3. **SUPABASE_ANON_KEY** (Required)
   - Description: Your Supabase anonymous/public key
   - Find in: Supabase Dashboard → Project Settings → API

4. **SUPABASE_SERVICE_ROLE_KEY** (Required for admin operations)
   - Description: Your Supabase service role key (keep secret!)
   - Find in: Supabase Dashboard → Project Settings → API

### Optional Environment Variables

5. **RAJAONGKIR_API_KEY** (Optional)
   - Description: API key for RajaOngkir shipping integration
   - Only needed if using shipping features

6. **ENVIRONMENT** (Optional, defaults to "development")
   - Set to "production" for production deployments
   - Example: `production`

## Deployment Steps

1. **Install Vercel CLI** (if not already installed)
   ```bash
   npm i -g vercel
   ```

2. **Link Your Project**
   ```bash
   vercel link
   ```

3. **Set Environment Variables**
   ```bash
   # Set production environment variables
   vercel env add SESSION_SECRET production
   vercel env add SUPABASE_URL production
   vercel env add SUPABASE_ANON_KEY production
   vercel env add SUPABASE_SERVICE_ROLE_KEY production
   vercel env add ENVIRONMENT production
   ```

4. **Deploy to Production**
   ```bash
   vercel --prod
   ```

## Important Notes

### Serverless Limitations

- **Scheduler Disabled**: The automated Sambatan lifecycle scheduler is disabled in Vercel's serverless environment. Use manual API triggers or set up external cron jobs.
- **Stateless**: Each request may be handled by a different serverless function instance. Don't rely on in-memory state.
- **Cold Starts**: First request after inactivity may be slower due to cold start.

### Static Files

Static files (CSS, JS, images) are served from the `/static` route. If the static directory is not found during deployment, the application will continue to work but static assets won't be available.

### Monitoring

Check application logs at: `https://your-deployment-url/_logs`

## Troubleshooting

### FUNCTION_INVOCATION_FAILED Error

If you see this error, it typically means the serverless function cannot start. Common causes and solutions:

1. **Python Version Mismatch**: 
   - Ensure `runtime.txt` specifies `python-3.11`
   - Vercel currently has best support for Python 3.9 and 3.11
   - Python 3.12+ may not be fully supported yet

2. **Missing Environment Variables**:
   - Check that all required environment variables are set in Vercel dashboard
   - Use `vercel env ls` to list configured variables
   - Ensure `SESSION_SECRET` is at least 32 characters in production

3. **Import Errors**:
   - Verify all dependencies in `requirements.txt` are compatible
   - Check Vercel build logs for import errors
   - Ensure `mangum` is included in dependencies

4. **Configuration Issues**:
   - Verify `vercel.json` has proper `functions` and `rewrites` configuration
   - Check that `api/index.py` exports a `handler` variable
   - Review logs at `/_logs` endpoint (if accessible)

5. **Supabase Credentials**:
   - Verify Supabase credentials are correct
   - The app will start without Supabase, but some features won't work

### Static Files Not Loading

If static files (CSS/JS) are not loading:
1. Verify the `src/app/web/static` directory exists in your repository
2. Check the `.vercelignore` file isn't excluding static files
3. Review the application logs for static mount warnings

### Python Version

The application requires Python 3.11 or later. Vercel uses Python 3.11 as specified in the `runtime.txt` file. This ensures compatibility with Vercel's serverless Python runtime.

### Mangum Handler

The application uses [Mangum](https://mangum.io/) as an adapter to run the FastAPI ASGI application on Vercel's serverless infrastructure. This is the standard way to deploy FastAPI applications to serverless platforms.

## Additional Resources

- [Vercel Python Documentation](https://vercel.com/docs/functions/serverless-functions/runtimes/python)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Supabase Documentation](https://supabase.com/docs)
