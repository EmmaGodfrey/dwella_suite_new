"""Opt-in private S3-compatible uploads; local files remain the default."""

import os
import re
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured


def storage_settings():
    backend = os.getenv("STORAGE_BACKEND", "local").strip().lower()
    result = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    if backend == "local":
        return result
    if backend != "s3":
        raise ImproperlyConfigured("STORAGE_BACKEND must be local or s3.")
    required = ["STORAGE_S3_BUCKET", "STORAGE_S3_ACCESS_KEY", "STORAGE_S3_SECRET_KEY"]
    if any(not os.getenv(key, "").strip() for key in required):
        raise ImproperlyConfigured("S3 storage requires a bucket and dedicated credentials.")
    bucket = os.environ["STORAGE_S3_BUCKET"].strip()
    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]", bucket):
        raise ImproperlyConfigured("STORAGE_S3_BUCKET must be a valid S3 bucket name.")
    endpoint = os.getenv("STORAGE_S3_ENDPOINT_URL", "").strip()
    if endpoint:
        parsed = urlsplit(endpoint)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username
                or parsed.password or parsed.path not in ("", "/") or parsed.query
                or parsed.fragment):
            raise ImproperlyConfigured("STORAGE_S3_ENDPOINT_URL must be an HTTPS origin.")
    try:
        expiry = int(os.getenv("STORAGE_S3_URL_TTL", "900"))
    except ValueError as error:
        raise ImproperlyConfigured("STORAGE_S3_URL_TTL must be an integer.") from error
    if not 60 <= expiry <= 3600:
        raise ImproperlyConfigured("STORAGE_S3_URL_TTL must be between 60 and 3600 seconds.")
    result["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": bucket,
            "access_key": os.environ["STORAGE_S3_ACCESS_KEY"],
            "secret_key": os.environ["STORAGE_S3_SECRET_KEY"],
            "endpoint_url": endpoint or None,
            "region_name": os.getenv("STORAGE_S3_REGION", "auto"),
            "signature_version": "s3v4",
            "addressing_style": "path",
            "default_acl": None,
            "querystring_auth": True,
            "querystring_expire": expiry,
            "custom_domain": None,
            "file_overwrite": False,
            "object_parameters": {"CacheControl": "private, max-age=0, no-store"},
        },
    }
    return result
