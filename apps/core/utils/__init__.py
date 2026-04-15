import socket

# → Imports Python's built-in socket module for network communication.
# → socket = Low-level networking interface that provides:

# Creating client/server connections

# Sending/receiving data over networks

# DNS lookups (converting domain names to IPs)

# Working with TCP/UDP protocols
from collections.abc import Iterable

# → Imports the Iterable abstract base class from Python's collections module.
# → from collections.abc = Imports from Abstract Base Classes for container types
# → import Iterable = Brings in the Iterable type for type checking and isinstance() checks
# → Used to check if an object can be looped over (has __iter__() method)
# → Example: isinstance(my_list, Iterable) returns True for lists, tuples, strings, etc.
from typing import TYPE_CHECKING
from urllib.parse import urljoin, urlparse

# → Imports URL parsing utilities from Python's urllib module.

# → urljoin() = Joins a base URL with a relative path intelligently
# urljoin('https://example.com/api/', '/users')
# # Result: 'https://example.com/users'
# → urlparse() = Breaks a URL into components (scheme, netloc, path, etc.)
# parsed = urlparse('https://example.com/api/users?id=1')
# # parsed.scheme = 'https'
# # parsed.netloc = 'example.com'
# # parsed.path = '/api/users'
# # parsed.query = 'id=1'
from django.conf import settings
from django.contrib.sites.models import Site

# → Imports the Site model from Django's sites framework.
# → Site = Model representing a website/domain in a multi-site Django setup.

# Purpose: Manages multiple websites from one Django project.
from django.db.models import Model
from django.utils.encoding import iri_to_uri

# → Imports a utility function that converts International Resource Identifiers (IRIs) to URIs.
# → iri_to_uri() = Converts international characters to percent-encoded format safe for URLs.

# Purpose: Handles non-ASCII characters in URLs:
# ASCII (American Standard Code for Information Interchange) is a character encoding standard that uses numbers to represent text.
from django.utils.text import slugify

# → Imports a utility function that converts text into a URL-friendly "slug".
# → slugify() = Converts strings to lowercase, replaces spaces with hyphens, removes special chars.

# Purpose: Creates clean, readable URLs from titles/names:
from text_unidecode import unidecode

# → Imports the unidecode function from the text_unidecode library.
# → unidecode() = Converts Unicode text to the closest ASCII representation.

# Purpose: Transliterates non-English characters to English/ASCII equivalents:
# unidecode("café")
# # Result: "cafe"


if TYPE_CHECKING:
    from ...attribute.models import Attribute
# → Conditional import that only runs during type checking, not at runtime.
# → if TYPE_CHECKING: = Special condition from typing module that's True only when type checkers (mypy, Pyright) are running
# → from ...attribute.models import Attribute = Relative import from parent directories (../../attribute/models)

# Purpose:

# Avoids circular imports (models importing each other)

# Still provides type hints for IDE autocomplete

# Import doesn't actually run in production
if TYPE_CHECKING:
    from django.utils.safestring import SafeText
#     → Conditional import that only runs during type checking, not at runtime.
# → if TYPE_CHECKING: = Special condition that's True only when type checkers (mypy, Pyright) are running
# → from django.utils.safestring import SafeText = Imports SafeText type for type hints

# Purpose:

# Provides type information for IDE autocomplete

# Avoids circular imports at runtime


# SafeText = Django class for strings marked safe from HTML escaping
def get_domain(site: Site | None = None) -> str:
    #     → Defines a function that returns the domain name (e.g., "example.com").
    # → site: Site | None = None = Optional Site object parameter, defaults to None
    # → -> str = Returns a string
    if settings.PUBLIC_URL:
        return urlparse(settings.PUBLIC_URL).netloc
    #     → If PUBLIC_URL is set in Django settings (e.g., "https://example.com"):
    # → urlparse().netloc = Extracts just the domain part ("example.com")
    if site is None:
        site = Site.objects.get_current()
        # → If no site was provided, get the current site from database
    return site.domain


# → Returns the domain from the Site object (e.g., "example.com")

# Purpose: Gets the current website domain from either:

# Settings (if PUBLIC_URL defined)

# Django sites framework (fallback)


def get_public_url(domain: str | None = None) -> str:
    #     → Defines a function that returns the full public URL (e.g., "https://example.com").
    # → domain: str | None = None = Optional domain parameter, defaults to None
    # → -> str = Returns a string URL
    if settings.PUBLIC_URL:
        return settings.PUBLIC_URL
    # → If PUBLIC_URL is set in Django settings, return it directly
    host = domain or Site.objects.get_current().domain
    #     → If domain provided, use it; otherwise get domain from current Site
    # → host = Just the domain part (e.g., "example.com")
    protocol = "https" if settings.ENABLE_SSL else "http"
    #     → Determines protocol based on SSL setting:
    # → https if SSL enabled, otherwise http
    return f"{protocol}://{host}"


# → Combines protocol and host into full URL
# → Example: "https://example.com" or "http://localhost:8000"

# Purpose: Builds the complete public URL for the website from configuration.


def is_ssl_enabled() -> bool:
    #     → Defines a function that checks if SSL/HTTPS is enabled for the website.
    # → -> bool = Returns True or False
    if settings.PUBLIC_URL:
        return urlparse(settings.PUBLIC_URL).scheme.lower() == "https"
    #     → If PUBLIC_URL is set in settings:
    # → urlparse().scheme = Extracts the protocol part ("http" or "https")
    # → .lower() = Converts to lowercase for consistent comparison
    # → == "https" = Returns True if scheme is https, False otherwise
    return settings.ENABLE_SSL


# → If PUBLIC_URL not set, falls back to the ENABLE_SSL setting
# → Returns whatever value is in settings.ENABLE_SSL (True/False)

# Purpose: Determines if the site should use HTTPS based on either:

# PUBLIC_URL setting (checks if it starts with https://)

# ENABLE_SSL boolean setting (fallback)


def build_absolute_uri(location: str, domain: str | None = None) -> str:
    """Create absolute uri from location.

    If provided location is absolute uri by itself, it returns unchanged value,
    otherwise if provided location is relative, absolute uri is built and returned.
    """
    #     → Defines a function that builds a complete absolute URL from a relative path.
    # → location: str = The path or URL to convert (e.g., "/products/123" or "https://other.com")
    # → domain: str | None = Optional specific domain to use
    # → -> str = Returns complete absolute URL
    current_uri = get_public_url(domain)
    # → Gets base URL (e.g., "https://example.com") from settings or Site
    location = urljoin(current_uri, location)
    #     → Joins base URL with location path intelligently:
    # → If location is full URL: urljoin("https://example.com", "https://other.com/page") = "https://other.com/page"
    # → If relative: urljoin("https://example.com", "/products/123") = "https://example.com/products/123"
    return iri_to_uri(location)


# → Converts any international characters to safe URL encoding
# → Example: "https://example.com/café" → "https://example.com/caf%C3%A9"

# Purpose: Creates absolute URLs for use in emails, APIs, redirects, etc.


def get_client_ip(request):
    """Retrieve the IP address from the request data.

    Tries to get a valid IP address from X-Forwarded-For, if the user is hiding behind
    a transparent proxy or if the server is behind a proxy.

    If no forwarded IP was provided or all of them are invalid,
    it fallback to the requester IP.
    """
    #     → Defines a function to get the real IP address of the client making the request.
    # → request = Django request object containing metadata
    ip = request.META.get("HTTP_X_FORWARDED_FOR", "")
    #     → Gets X-Forwarded-For header (contains original client IP when behind proxy)
    # → Returns empty string if header doesn't exist
    ips = ip.split(",")
    #     → Splits multiple IPs (proxies can add to this list)
    # → Format: "client_ip, proxy1_ip, proxy2_ip"

    for ip in ips:
        if is_valid_ipv4(ip) or is_valid_ipv6(ip):
            return ip
    #         → Loops through IPs and returns first valid IP (client's real IP)
    # → is_valid_ipv4/ipv6 = Validates IP format (not shown here)
    return request.META.get("REMOTE_ADDR", None)


# → Fallback: If no valid forwarded IP, use direct connection IP
# → REMOTE_ADDR = IP of immediate connection (proxy or client)

# Purpose: Gets real client IP even when behind proxies/load balancers.


def is_valid_ipv4(ip: str) -> bool:
    """Check whether the passed IP is a valid V4 IP address."""
    #     → Defines a function that checks if a string is a valid IPv4 address.
    # → ip: str = The IP address string to validate (e.g., "192.168.1.1")
    # → -> bool = Returns True if valid, False if not
    try:
        socket.inet_pton(socket.AF_INET, ip)
    #         → socket.inet_pton() = Converts IP string to binary format
    # → socket.AF_INET = Specifies IPv4 address family
    # → If conversion succeeds → IP is valid
    # → Example valid: "192.168.1.1", "8.8.8.8"
    # → Example invalid: "999.999.999.999", "abc.def.ghi.jkl", "256.1.2.3"
    except OSError:
        return False
    # → If conversion fails (OSError), IP is invalid → return False
    return True


# → If no error, IP is valid → return True

# Purpose: Validates IPv4 addresses before using them (security, logging, geolocation).


def is_valid_ipv6(ip: str) -> bool:
    """Check whether the passed IP is a valid V6 IP address."""
    #     → Defines a function that checks if a string is a valid IPv6 address.
    # → ip: str = The IP address string to validate (e.g., "2001:db8::1")
    # → -> bool = Returns True if valid, False if not
    try:
        socket.inet_pton(socket.AF_INET6, ip)
    #         → socket.inet_pton() = Converts IP string to binary format
    # → socket.AF_INET6 = Specifies IPv6 address family
    # → If conversion succeeds → IP is valid
    # → Example valid: "2001:db8::1", "::1", "fe80::1"
    # → Example invalid: "xyz::abc", "2001:::1", "invalid"
    except OSError:
        return False
    # → If conversion fails (OSError), IP is invalid → return False
    return True


# → If no error, IP is valid → return True

# Purpose: Validates IPv6 addresses before using them (security, logging, geolocation).


def generate_unique_slug(
    instance: Model,
    slugable_value: str,
    slug_field_name: str = "slug",
    *,
    additional_search_lookup=None,
) -> str:
    #     → Defines a function that creates a unique URL slug for a model instance.
    # → instance: Model = The Django model object (e.g., a Product instance)
    # → slugable_value: str = Text to base slug on (e.g., product name)
    # → slug_field_name: str = "slug" = Name of the slug field (defaults to "slug")
    # → additional_search_lookup = Extra filter conditions for uniqueness
    # → -> str = Returns unique slug string
    """Create unique slug for model instance.

    The function uses `django.utils.text.slugify` to generate a slug from
    the `slugable_value` of model field. If the slug already exists it adds
    a numeric suffix and increments it until a unique value is found.

    Args:
        instance: model instance for which slug is created
        slugable_value: value used to create slug
        slug_field_name: name of slug field in instance model
        additional_search_lookup: when provided, it will be used to find the instances
            with the same slug that passed also additional conditions

    """
    slug = slugify(unidecode(slugable_value))
    #     → Converts text to URL-friendly slug:
    # → unidecode() = Transliterates "café" → "cafe"
    # → slugify() = "Hello World!" → "hello-world"
    # in case when slugable_value contains only not allowed in slug characters, slugify
    # function will return empty string, so we need to provide some default value
    if slug == "":
        slug = "-"
    # → Fallback: If slug is empty (e.g., input was "!!!") use "-" instead
    ModelClass = instance.__class__
    # → Gets the model class of the instance (e.g., Product)
    search_field = f"{slug_field_name}__iregex"
    pattern = rf"{slug}-\d+$|{slug}$"
    lookup = {search_field: pattern}
    #     → Creates regex pattern to find existing slugs:
    # → rf"{slug}-\d+$" = Matches "slug-1", "slug-2", etc.
    # → | = OR
    # → {slug}$ = Matches exact "slug"
    # → Example: pattern = "hello-world-\d+$|hello-world$"
    if additional_search_lookup:
        lookup.update(additional_search_lookup)
        # → Adds extra filters if provided (e.g., filter by category)

    slug_values = (
        ModelClass._default_manager.filter(**lookup)
        .exclude(pk=instance.pk)
        .values_list(slug_field_name, flat=True)
    )
    #     → Queries database for existing slugs:
    # → .filter(**lookup) = Find matching slugs
    # → .exclude(pk=instance.pk) = Exclude current instance
    # → .values_list(slug_field_name, flat=True) = Get list of existing slug strings
    unique_slug = prepare_unique_slug(slug, slug_values)
    # → Calls helper to add number suffix if needed:
    # → If "hello-world" exists, try "hello-world-1", "hello-world-2", etc.
    return unique_slug


# → Returns the unique slug


def prepare_unique_slug(slug: str, slug_values: Iterable):
    #     → Defines a helper function that makes a slug unique by adding numbers.
    # → slug: str = The base slug (e.g., "hello-world")
    # → slug_values: Iterable = List of existing slugs from database
    """Prepare unique slug value based on provided list of existing slug values."""
    unique_slug: SafeText | str = slug
    #     → Initializes unique_slug as the original slug
    # → SafeText | str = Type hint (can be either SafeText or string)
    extension = 1
    # → Starts counter at 1 for suffix
    while unique_slug in slug_values:
        extension += 1
        unique_slug = f"{slug}-{extension}"
    # → Loop while slug already exists:
    # → while unique_slug in slug_values = Check if current slug is taken
    # → extension += 1 = Increment counter (1,2,3...)
    # → unique_slug = f"{slug}-{extension}" = Create new slug with number suffix
    # → Example: "hello-world-1", "hello-world-2", etc.
    return unique_slug


# → Returns the first available unique slug

# Purpose: Ensures URL slugs are unique by adding incrementing numbers when needed.


def prepare_unique_attribute_value_slug(attribute: "Attribute", slug: str):
    #     → Defines a function that creates a unique slug for an attribute value.
    # → attribute: "Attribute" = The Attribute object this value belongs to
    # → slug: str = The base slug to make unique
    value_slugs = attribute.values.filter(slug__startswith=slug).values_list(
        "slug", flat=True
    )
    #     → Gets all existing slugs for this attribute's values:
    # → .values.filter(slug__startswith=slug) = Find all values where slug starts with base slug
    # → .values_list("slug", flat=True) = Returns list of slug strings (not objects)
    # → Example: If base slug is "red", finds "red", "red-1", "red-2", etc.
    return prepare_unique_slug(slug, value_slugs)


# → Calls generic prepare_unique_slug with the list of existing slugs
# → Returns unique slug (e.g., "red-3" if "red", "red-1", "red-2" exist)

# Purpose: Creates unique slugs for product attribute values (like colors, sizes) within the same attribute.


# ✔ Why functions are used before defined?

# Because:

# Python loads function definitions first, executes them later

# ✔ Why core/utils/__init__.py exists?

# To:

# centralize reusable helper logic used across the entire system

# ✔ What problem it solves?

# avoids duplication

# ensures consistency
# Imagine 3 different ways to generate slugs:
# product slug → "hello-world"
# blog slug → "hello_world"
# user slug → "HelloWorld"
# With central utils generate_unique_slug() Used everywhere → consistent behavior


# simWith core/utils

# Everything lives in ONE place:

# from saleor.core.utils import get_client_ip


# improves maintainability
# Hard-to-maintain codebase

# If logic is scattered:

# bug fixes = painful

# updates = risky

# debugging = slow
#  With utils module

# You fix one place:

# core/utils/__init__.py

# And entire system improves.
