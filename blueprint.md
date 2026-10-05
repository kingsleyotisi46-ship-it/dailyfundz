# DailyFundzBoost Deployment

## Render

This repository contains a Render Blueprint in `render.yaml`. Create or update the Render service from that file, then set the environment variables marked `sync: false` in the Render dashboard before deploying.

Required secrets and service credentials are intentionally not stored in this repository. Configure fresh values for:

- `SECRET_KEY`
- `DATABASE_URL`
- `CLOUDINARY_URL`, `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, and `CLOUDINARY_API_SECRET`
- `SMM_PROVIDER_KEY`
- `GRIZZLY_API_KEY`
- `EMAIL_HOST_PASSWORD`

The deployment runs `collectstatic` during build, applies migrations before deploy, then starts Gunicorn. Provider-service imports are not part of the build; run the management command explicitly after deployment when provider credentials and service data are ready.

## Secret handling

Do not commit `.env` files, database exports, browser cookies, API keys, passwords, or production credentials. If a credential was previously stored in source or shared, revoke or rotate it with its provider before deploying.

## Domains and email

Update `ALLOWED_HOSTS`, `SITE_URL`, `CSRF_TRUSTED_ORIGINS`, and the email variables in `render.yaml` to match the actual production domain and mail provider. Keep production `DEBUG=False`.
