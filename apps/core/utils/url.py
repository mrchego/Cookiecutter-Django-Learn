from urllib.parse import urlparse, urlsplit

# → URL parsing utilities from Python standard library:

# urlparse() = Breaks a URL into components (scheme, netloc, path, etc.)

# urlsplit() = Similar to urlparse but doesn't split parameters (faster)
from django.conf import settings

# → Django settings object for accessing project configuration
from django.core.exceptions import ValidationError

# → Django's validation exception for form/model validation
from django.core.files.storage import default_storage

# → Default file storage system (handles file uploads, saving, deleting)
from django.http.request import split_domain_port, validate_host

# split_domain_port() = Separates domain name from port number

# validate_host() = Checks if a host is allowed in ALLOWED_HOSTS
from . import build_absolute_uri

# → Local import of build_absolute_uri function from current package


def validate_storefront_url(url):
    """Validate the storefront URL.

    Raise ValidationError if URL isn't in RFC 1808 format
    or it isn't allowed by ALLOWED_CLIENT_HOSTS in settings.
    """
    # RFC 1808 Format
    # RFC 1808 is a specification that defines the standard format for URLs (Uniform Resource Locators). It was published in 1995 and describes how URLs should be structured.

    # Basic URL Structure (RFC 1808):
    # text
    # scheme://netloc/path?query#fragment
    # Components Breakdown:
    # Component	Example	Required?	Description
    # scheme	https://	✅ Required	Protocol (http, https, ftp)
    # netloc	example.com	✅ Required	Network location (domain + optional port)
    # path	/products/shoes	❌ Optional	File/directory path
    # query	?id=123&sort=asc	❌ Optional	Query parameters
    # fragment	#section2	❌ Optional	Anchor/hash link
    # Storefront URL
    # A storefront URL is the web address where customers access your online store.
    # → Validates that a storefront URL is properly formatted and its domain is in the allowed hosts list.

    # What it does:
    # Checks a storefront URL for two things: 1) valid RFC 1808 format, 2) domain is whitelisted in ALLOWED_CLIENT_HOSTS setting.
    try:
        parsed_url = urlparse(url)
        #         What is "Parses"?
        # Parsing is the process of analyzing a string of text (like a URL, code, or sentence) and breaking it into meaningful components that a computer can understand.
        # → Parses the URL into components (scheme, netloc, path, etc.)
        # → Example: urlparse("https://store.example.com/shop") → ParseResult(scheme='https', netloc='store.example.com', path='/shop', ...)
        domain, _ = split_domain_port(parsed_url.netloc)
        #         → Separates domain name from port number
        # → Example: "store.example.com:8000" → domain="store.example.com", port="8000" (discarded with _)
        # → If no port, returns domain as-is
        if not parsed_url.netloc:
            raise ValidationError(
                "Invalid URL. Please check if URL is in RFC 1808 format."
            )
    #         → Checks if URL has a network location (domain)
    # → Example: "https://example.com" has netloc "example.com" → passes
    # → Example: "/just/path" has no netloc → fails (relative URL not allowed)
    except ValueError as e:
        raise ValidationError(str(e)) from e
    #     → Catches URL parsing errors (malformed URLs)
    # → Re-raises as Django ValidationError with original message
    if not validate_host(domain, settings.ALLOWED_CLIENT_HOSTS):
        #         → Checks if domain is allowed by the ALLOWED_CLIENT_HOSTS setting
        # → validate_host() matches domain against patterns (supports wildcards like *.example.com)
        error_message = (
            f"{domain or url} is not allowed. Please check "
            "`ALLOWED_CLIENT_HOSTS` configuration."
        )
        raise ValidationError(error_message)
    # → If domain not allowed, raises descriptive error with configuration hint


# Summary:
# Aspect	Explanation
# Purpose	Validate storefront URL format and domain
# Checks	RFC 1808 compliance + ALLOWED_CLIENT_HOSTS whitelist
# Requires	Scheme (http/https) + netloc (domain)
# Allows	Path, query, fragment (optional)
# Blocks	Relative URLs, disallowed domains
# Use case	Storefront configuration, external URL validation
# Key Concept: This function provides security-critical validation for storefront URLs by ensuring they're properly formatted (RFC 1808) and the domain is explicitly allowed by ALLOWED_CLIENT_HOSTS. This prevents open redirect vulnerabilities and SSRF attacks by rejecting relative URLs and external domains not on the whitelist. The use of split_domain_port() removes port numbers before validation, ensuring localhost:8000 is treated the same as localhost. The error messages include configuration hints to help developers fix issues quickly.


def prepare_url(params: str, redirect_url: str) -> str:
    """Add params to redirect url."""
    #     → Adds query parameters to a redirect URL, preserving any existing parameters.

    # What it does:
    # Takes a redirect URL and query parameters, then returns the URL with the new parameters appended. If the URL already has parameters, it merges them with &.
    split_url = urlsplit(redirect_url)
    #     → Parses the redirect URL into its components
    # → urlsplit is like urlparse but faster (doesn't split params)
    # → Example: urlsplit("https://example.com/path?id=123") → SplitResult(scheme='https', netloc='example.com', path='/path', query='id=123', fragment='')
    current_params = split_url.query
    #     → Extracts existing query parameters from the URL
    # → Example: If URL has ?id=123&sort=asc, current_params = "id=123&sort=asc"
    # → If no parameters, current_params = "" (empty string)
    if current_params:
        params = f"{current_params}&{params}"
    #         → If URL already has parameters, append new ones with &
    # → Example: current_params = "id=123", params = "sort=asc" → params = "id=123&sort=asc"
    split_url = split_url._replace(query=params)
    #     → Creates a new URL object with updated query string
    # → _replace() returns a new SplitResult with the specified field changed
    # → Doesn't modify the original split_url
    return split_url.geturl()


# → Reconstructs the full URL string from the components
# → Returns the final URL with merged parameters


def get_default_storage_root_url():
    """Return the absolute root URL for default storage."""
#     → Returns the base/root URL where files are stored (e.g., the CDN or media URL root).

# What it does:
# Gets the absolute URL of the default storage system (like S3, Azure, or local media) by creating a temporary file path and stripping it away to get just the root.
    # We cannot do simple `storage.url("")`, as the `AzureStorage` url method requires
    # at least one printable character that is not a slash or space.
    # Because of that, the `url` method is called for a `path` value, and then
    # `path` is stripped to get the actual root URL
    tmp_path = "path"
#     → Creates a dummy/temporary path string
# → Needs to be something simple that can be stripped from the URL later
    return build_absolute_uri(default_storage.url(tmp_path)).rstrip(tmp_path)
# build_absolute_uri(default_storage.url(tmp_path))
# → Converts the storage URL to an absolute URI
# → Ensures it's a complete URL with scheme and domain
# rstrip(tmp_path)
# → Removes the temporary "path" from the end of the URL
# → Leaves just the root URL
# Summary:
# Aspect	Explanation
# Purpose	Get root URL of default storage system
# Why workaround	Some storage backends (Azure) fail with empty path
# Method	Use dummy path → get URL → strip dummy path
# Returns	Root URL like "https://cdn.example.com/media/"
# Use case	Building absolute file URLs, API responses
# Storage support	Works with all Django storage backends
# Key Concept: This function provides a storage-backend-agnostic way to get the root URL where files are stored. It works around limitations in some storage backends (like Azure) that require a non-empty path by using a temporary dummy path and stripping it away. The result is the absolute root URL that can be prepended to file paths to get complete, publicly accessible URLs for stored files. This is essential for building file URLs in API responses or generating direct links to uploaded content across different storage systems (local, S3, Azure, GCS).


def sanitize_url_for_logging(url: str) -> str:
    """Remove sensitive data from a URL to make it safe for logging."""
#     → Redacts usernames and passwords from URLs so sensitive credentials aren't exposed in log files.

# What it does:
# Takes a URL, checks if it contains a username or password in the format https://user:pass@example.com, and replaces the credentials with ***:*** for safe logging.
    url_parts = urlparse(url)
#     → Parses URL into components (scheme, netloc, path, etc.)
# → netloc contains domain and optionally username/password
    if url_parts.username or url_parts.password:
#         → Checks if the URL contains authentication credentials
# → username and password are extracted from netloc by urlparse
        url_parts = url_parts._replace(
            netloc=f"***:***@{url_parts.hostname}:{url_parts.port}"
            if url_parts.port
            else f"***:***@{url_parts.hostname}"
        )
#         → Creates new URL with redacted credentials
# → If port exists: ***:***@hostname:port
# → If no port: ***:***@hostname
    return url_parts.geturl()
#  Reconstructs URL with redacted credentials
# Summary:
# Aspect	Explanation
# Purpose	Remove credentials from URLs for safe logging
# Redacts	Username and password in user:pass@host format
# Preserves	Scheme, hostname, port, path, query, fragment
# Output	URL with ***:*** instead of credentials
# Use case	Logging API calls, debug output, error messages
# Security	Prevents credential leakage in logs
# Key Concept: This function prevents sensitive authentication credentials from appearing in log files by replacing them with ***:***. It's a critical security utility for any application that logs URLs containing Basic Authentication credentials. The function preserves all other URL components (path, query parameters, fragment) while only redacting the sensitive netloc credentials. This allows developers to debug API calls and request flows without exposing passwords, API keys, or other secrets in plain text logs.
