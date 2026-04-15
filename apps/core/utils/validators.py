import datetime

# → Imports Python's built-in datetime module for working with dates, times, and timestamps.
from typing import Any

# → Imports the Any type hint from Python's typing module for values that can be of any type (disables type checking).
import micawber

# Micawber is a Python library that implements the oEmbed protocol. It takes a URL (like a YouTube video) and returns embed code that can be inserted into HTML.
from ...product import ProductMediaTypes
from ..exceptions import UnsupportedMediaProviderException

SUPPORTED_MEDIA_TYPES = {
    "photo": ProductMediaTypes.IMAGE,
    "video": ProductMediaTypes.VIDEO,
}
# Maps oEmbed's generic media type names ("photo", "video") to the application's specific product media types (ProductMediaTypes.IMAGE, ProductMediaTypes.VIDEO).
MEDIA_MAX_WIDTH = 1920
MEDIA_MAX_HEIGHT = 1080
# This code is typically used in e-commerce platforms where products can have media (images, videos) from external sources like YouTube, Vimeo, etc.


def get_oembed_data(url: str) -> tuple[dict[str, Any], str]:
    #     → Defines a function that fetches oEmbed data from a URL and returns it with the mapped media type.

    # What it does:
    # Takes a media URL (YouTube, Vimeo, etc.), fetches its oEmbed data from the provider, validates it, and returns the data along with the mapped internal media type.
    """Get the oembed data from URL or raise an ValidationError."""
    providers = micawber.bootstrap_basic()
    # → Initializes micawber with standard oEmbed providers (YouTube, Vimeo, Twitter, etc.)

    try:
        oembed_data = providers.request(
            url, maxwidth=MEDIA_MAX_WIDTH, maxheight=MEDIA_MAX_HEIGHT
        )
        #         → Requests oEmbed data from the provider
        # → maxwidth and maxheight = Limits embed dimensions (1920x1080 from previous constants)
        return oembed_data, SUPPORTED_MEDIA_TYPES[oembed_data["type"]]
    #      Returns a tuple containing:
    # oembed_data: The full oEmbed response dictionary
    # SUPPORTED_MEDIA_TYPES[oembed_data["type"]]: Mapped media type (IMAGE or VIDEO)
    except (micawber.exceptions.ProviderException, KeyError) as e:
        raise UnsupportedMediaProviderException() from e


#     ProviderException: URL not supported by any oEmbed provider
# KeyError: Media type not in SUPPORTED_MEDIA_TYPES (e.g., "rich" or "link")
# → Raises custom exception with the original error as cause
# Aspect	Description
# Purpose	Fetch oEmbed data from media URLs and validate support
# Input	URL string (YouTube, Vimeo, Flickr, etc.)
# Output	Tuple of (oEmbed data dict, mapped media type)
# Errors	Raises UnsupportedMediaProviderException for unsupported URLs/types
# Dimensions	Automatically limits to 1920x1080
# Use cases	Adding product videos/images from external sources
# Key Concept: This function provides a clean, unified interface for integrating external media (videos, images) into products. It handles all oEmbed providers, enforces dimension limits, and maps generic media types to application-specific types, making it easy to add YouTube videos, Vimeo clips, Flickr images, and other external media to products with consistent handling.


def is_date_in_future(given_date):
    """Return true when the date is in the future."""
    # → Defines a function that takes a date object and returns whether it's in the future
    return given_date > datetime.datetime.now(tz=datetime.UTC).date()


# → Gets current UTC time:

# datetime.datetime.now(tz=datetime.UTC) = Current UTC datetime with timezone

# .date() = Extracts just the date part (year, month, day)
# → Example: datetime.date(2024, 1, 15) for January 15, 2024
# What it does:
# Checks if a given date is in the future compared to the current UTC date.
# Aspect	Description
# Purpose	Check if a date is in the future
# Input	datetime.date object
# Output	Boolean (True if future, False otherwise)
# Comparison	Uses UTC date for consistency
# Common uses	Launch dates, promotions, subscriptions, scheduling
# Key Concept: This simple utility function is essential for date-based business logic. It ensures consistent future/past checks using UTC date, which is important for e-commerce applications where launch dates, promotions, and subscriptions need to be validated across different timezones.
