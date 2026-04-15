import warnings

# → Imports Python's warnings module for issuing non-critical alerts (like deprecation warnings).
from typing import Any, Literal, TypedDict, cast, overload

# Any = Any type (disables type checking)

# Literal = Restrict to specific string values (e.g., Literal["html", "text"])

# TypedDict = Define dictionary with specific key types

# cast = Type assertion (tell type checker a value is a specific type)

# overload = Function that behaves differently based on argument types
import nh3

# → Imports nh3 - a Python binding for Amazon's HTML sanitizer (ammonia), used for cleaning HTML to prevent XSS attacks
from django.conf import settings

# → Django settings object for accessing project configuration.
from django.core.exceptions import ValidationError

# → Django's validation error exception.
from django.utils.html import strip_tags

# → Django utility to remove HTML tags from a string.
from urllib3.util import parse_url

# → URL parser from urllib3 library.
from ..cleaners import URL_SCHEME_CLEANERS, URLCleanerError

# → Imports from parent directory's cleaners module:

# URL_SCHEME_CLEANERS = Dictionary of cleaners for different URL schemes (http, https, ftp, etc.)

# URLCleanerError = Custom exception for URL cleaning errors
ALLOWED_TEXT_BLOCK_TYPES = ("paragraph", "header", "quote")
ITEM_TYPE_TO_CLEAN_FUNC_MAP = {
    # → Defines a dictionary constant that maps string keys to cleaning functions
    "image": lambda *params: clean_image_item(*params),
    #     → Maps the key "image" to a function that calls clean_image_item()
    # → lambda *params = Anonymous function that accepts any number of parameters
    # → Passes all parameters to clean_image_item()
    "embed": lambda *params: clean_embed_item(*params),
    # → Maps "embed" to clean_embed_item() for cleaning embedded content (videos, social media posts)
    "quote": lambda *params: clean_quote_item(*params),
    # → Maps "quote" to clean_quote_item() for cleaning quoted text content
}
# → Creates a mapping dictionary that associates item types with their corresponding cleaning functions.
# What it does:
# Provides a lookup table to find the appropriate cleaning function for different types of content items (images, embeds, quotes).


ALLOWED_URL_SCHEMES = {
    # → Defines a set (unique values, unordered) of allowed URL schemes
    # WARNING: do NOT add new schemes in directly to this list, only HTTP and HTTPS
    #          should be listed as they are cleaned by urllib3. Instead, add it to
    #          URL_SCHEME_CLEANERS and implement a cleaner that (at minimum) quotes
    #          special characters like "'<> and ASCII control characters
    #          (use urllib.util.parse.quote())
    "http",
    "https",
    # → Base allowed schemes that use urllib3 for cleaning
    *URL_SCHEME_CLEANERS.keys(),
    #     → Unpacks all keys from URL_SCHEME_CLEANERS dictionary
    # → Adds any custom schemes that have dedicated cleaners
    # → Example: if URL_SCHEME_CLEANERS has keys "ftp", "mailto", "tel", they get added
}
# → Defines a set of allowed URL schemes (protocols) for content sanitization.

# What it does:
# Creates a set containing HTTP, HTTPS, and all custom URL schemes that have registered cleaners.


def maybe_to_int(o: Any, *, name: str) -> int:
    #     → o: Any = The value to convert (could be string, int, etc.)
    # → * = All following parameters must be keyword arguments
    # → name: str = The field/parameter name (used in error messages)
    # → -> int = Returns an integer
    """Cast a given object to an integer if it's possible, otherwise it raises.

    It's a lenient parsing for backward compatibility.
    """

    if isinstance(o, str):
        # → Checks if the input is a string
        if o.isnumeric() is False:
            raise ValidationError(f"{name} must be an integer")
        #         → o.isnumeric() = Returns True if all characters are numeric digits
        # → If the string contains non-numeric characters, raises ValidationError
        # → Example: "123" passes, "123a" fails
        return int(o)
    # → Converts the valid numeric string to an integer
    if isinstance(o, int) is False:
        raise ValidationError(f"{name} must be an integer")
    #     → If input is not a string, check if it's an integer
    # → If it's neither string nor integer, raise error

    return o


# → Input is already an integer, return as-is
# → Defines a helper function that safely converts a value to an integer, with backward compatibility for strings.

# What it does:
# Converts a value to an integer if possible, raising a validation error if conversion fails. It's designed to be lenient with string inputs that contain only digits.
# Purpose: Safely convert values to integers with backward compatibility

# Input: Any value (string, int, etc.)

# Output: Integer if conversion possible

# Error: Raises ValidationError with field name if conversion fails

# Use cases: API endpoints, form data, database IDs, backward compatibility

# Key feature: Lenient with string numbers, strict with invalid formats

# Key Concept: This function provides backward compatibility for APIs and data processing by accepting both string and integer inputs for numeric fields, while still providing clear validation errors when invalid data is provided. It ensures that numeric fields are always treated as integers throughout the application.


class NestedListItemType(TypedDict):
    """The EditorJS inner items of a nested list.

    Example:
        {
            "type" : "list",
            "data" : {
                "style": "ordered",
                "meta": {
                    "start": 2,
                    "counterType": "upper-roman",
                },
                "items" : [
                    {                              # <---
                        "content": "Apples",       # <---
                        "meta": {},                # <---
                        "items": [                 # <---
                            {
                                "content": "Red",
                                "meta": {},
                                "items": []
                            },
                        ]
                    },
                ]
            }
        }

    """

    content: str  # The text
    #     → The actual text content of the list item
    # → Example: "Apples", "Red", "3.14"
    meta: dict
    #     → Optional metadata for the list item (e.g., formatting, attributes, custom data)
    # → Example: {"bold": True, "color": "red"}
    items: list["NestedListItemType"]


#     → List of child items, allowing infinite nesting
# → Uses a string reference to itself ("NestedListItemType") for forward reference (supports recursion)
# Purpose: Type definition for nested list items in EditorJS

# Structure: Content text + metadata + recursive child items

# Use cases: Rich text editing, hierarchical data, menus, outlines

# Benefits: Type safety, IDE support, clear structure

# Pattern: Recursive TypedDict for nested data

# Key Concept: This TypedDict defines the structure for infinitely nested lists, which is essential for rich text editors like EditorJS. The recursive reference (items: list["NestedListItemType"]) allows for proper type checking of deeply nested structures, making it safe to work with complex, hierarchical content.


class NestedListBlockType(TypedDict):
    """The EditorJS outer block of a nested list.

    Example:
        {
            "type" : "list",
            "data" : {
                "style": "ordered",                 # <---
                "meta": {                           # <---
                    "start": 2,                     # <---
                    "counterType": "upper-roman",   # <---
                },                                  # <---
                "items" : [                         # <---
                    {
                        "content": "Apples",
                        "meta": {},
                        "items": [
                            {
                                "content": "Red",
                                "meta": {},
                                "items": []
                            },
                        ]
                    },
                ]
            }
        }

    """

    style: str
    #     → Defines the list type (ordered vs unordered)
    # → Values: "ordered" (numbered list) or "unordered" (bulleted list)
    meta: dict
    #     → Contains list-specific metadata and configuration
    # → Examples: start number for ordered lists, counter type (roman numerals, letters)
    items: list["NestedListItemType"]


#     → The actual list items, which are themselves nested structures
# → Uses the previously defined NestedListItemType
# Purpose: Type definition for EditorJS nested list outer block

# Structure: Style (ordered/unordered) + metadata + recursive items

# Use cases: Rich text editing, document storage, content management

# Relationship: Uses NestedListItemType for the recursive item structure

# Benefits: Complete type safety for complex nested list structures

# Key Concept: This TypedDict represents the complete EditorJS list block container. It separates the block-level properties (style, meta) from the recursive item structure, providing type safety for the entire list block while maintaining flexibility for various list configurations (ordered/unordered, different counter types, custom start numbers).

@overload
# → Decorator that allows a function to have multiple type signatures
# → The actual implementation has a single signature, but overloads tell type checkers about different calling patterns
def clean_editor_js(
    # → Function name: cleans EditorJS content
    definitions: dict | str | None,
    *,
    to_string: Literal[True],
    #     → definitions = The EditorJS content (can be dict, JSON string, or None)
    # → * = All following parameters must be keyword arguments
    # → Literal[True] means this overload only applies when to_string is exactly True
    # → Forces the return type to be str
) -> str: ...


# → Returns a string when to_string=True
# → ... = Placeholder (no implementation here)
# This is an @overload decorator that defines one possible signature for the clean_editor_js function. It indicates that when to_string=True is passed, the function returns a str.
# Purpose: Type-safe overload for EditorJS cleaning function

# Behavior: Returns str when to_string=True

# Benefits: Clear type information, better IDE support, fewer runtime errors

# Pattern: Multiple overloads for different parameter combinations

# Key Concept: The @overload decorator tells type checkers that when to_string=True is passed, the function always returns a string, not a dictionary. This provides precise type information to IDEs and type checkers, making the code safer and easier to use correctly.


@overload
# → Marks this as an alternate type signature for the function (no implementation)
# What "no implementation" means in @overload
# "No implementation" means the @overload decorated function is just a type hint - it doesn't contain any actual code that runs. The real code that executes lives in a separate, non-decorated version of the function below it.
def clean_editor_js(definitions: dict) -> dict: ...


# → When the input is a dictionary, the function returns a dictionary
# → The cleaned output is the same type as the input (dict → dict)
# ... Placeholder indicating this is just a type signature, not the actual implementation
# → Defines an overload signature for the clean_editor_js function when the input is a dictionary and no to_string parameter is provided (or to_string=False), indicating it returns a dictionary.


@overload
def clean_editor_js(definitions: None) -> None: ...


# → Defines an overload signature for the clean_editor_js function when the input is None, indicating it returns None (no content to clean).

# What it does:
# This overload tells type checkers that when None is passed as input, the function returns None, meaning there's no content to process or return.


def clean_editor_js(definitions, *, to_string=False) -> dict | str | None:
    #     → Main function that sanitizes EditorJS content to prevent XSS attacks and clean URLs.

    # What it does:
    # Processes EditorJS JSON content, cleans all text and URLs, optionally returns plain text instead of JSON.
    """Sanitize a given EditorJS JSON definitions.

    Look for not allowed URLs, replaced them with `invalid` value, and clean valid ones.

    `to_string` flag is used for returning concatenated string from all blocks
     instead of returning json object.
    """
    if definitions is None:
        return "" if to_string else definitions
    #     → If input is None:
    # → Returns empty string "" if to_string=True (plain text mode)
    # → Returns None if to_string=False (JSON mode)

    blocks = definitions.get("blocks")
    #     → Extracts the list of content blocks from EditorJS structure
    # → Example: {"blocks": [{"type": "paragraph", ...}]}

    if not blocks or not isinstance(blocks, list):
        return "" if to_string else definitions
    # → If no blocks or invalid format, return empty or original
    plain_text_list: list[str] = []
    # → Accumulates plain text for when to_string=True is requested

    for index, block in enumerate(blocks):
        # → Loops through each content block with its index
        block_type = block.get("type")
        # → Gets the block type (paragraph, image, list, etc.)

        if not block_type or isinstance(block_type, str) is False:
            raise ValidationError("Missing required key: 'type'")
        # → Validates that each block has a type string

        data = block.get("data")
        if not data or not isinstance(data, dict):
            continue
        # → Gets block's data (text, image URL, etc.), skip if invalid

        params = [blocks, block, plain_text_list, to_string, index]
        # → Packages common parameters for cleaner functions
        if clean_func := ITEM_TYPE_TO_CLEAN_FUNC_MAP.get(block_type):
            for field in ("width", "height"):
                if (field_value := data.get(field)) is not None:
                    data[field] = maybe_to_int(field_value, name=field)
            clean_func(*params)
        #             → Uses walrus operator (:=) to get cleaner function
        # → If found (image, embed, quote):
        # → Converts width/height fields to integers
        # → Calls the specific cleaner function

        elif block_type == "list":
            clean_list_item(
                block=block,
                to_string=to_string,
                plain_text_list=plain_text_list,
                max_depth=settings.EDITOR_JS_LISTS_MAX_DEPTH,
            )
            # → Handles nested list blocks specially
        else:
            clean_text_items(*params, block_type=block_type)
            # → Default: clean text items (paragraphs, headers, etc.)

    return " ".join(plain_text_list) if to_string else definitions


# → If to_string=True: returns plain text (joined with spaces)
# → If to_string=False: returns cleaned JSON structure
# Feature	Purpose
# to_string parameter	Extract plain text for previews, meta descriptions
# Recursive cleaning	Sanitize all nested content
# Type-based dispatch	Different cleaning for different block types
# Integer conversion	Ensure numeric fields are actually numbers
# Safe defaults	Handle missing/invalid data gracefully

def clean_legacy_list(items: list[str], *, to_string: bool, plain_text_list: list[str]):
    #     → Defines a function that cleans legacy (old format) list items in EditorJS content, handling both plain text extraction and HTML sanitization.

    # What it does:
    # Processes a list of strings (legacy list format) by either:

    # Extracting plain text for concatenation (if to_string=True)

    # Sanitizing HTML content and replacing items in-place (if to_string=False)

    for item_index, item in enumerate(items):
        #         → Loops through each list item with its index position
        # → enumerate() provides both the index and the value
        if isinstance(item, str) is False:
            # Mixing types or version (legacy vs new lists) isn't allowed by Saleor,
            # nor by EditorJS.
            raise ValidationError("Invalid EditorJS list: items must be strings")
        # → Validates that every item in the list is a string
        # → Legacy lists should contain only string items (not nested objects)
        # → Raises error if mixed types are found

        if to_string:
            # Only appends the text if it's not empty as we do a `' '.join(...)`
            # i.e., otherwise it will create unneeded (and ugly) whitespaces.
            if item:
                plain_text_list.append(strip_tags(item))
        #                OO
        else:
            new_text = clean_text_data_block(item)
            items[item_index] = new_text


#             → When to_string=False (returning JSON):
# → clean_text_data_block(item) = Sanitizes HTML, removes dangerous content
# → Replaces the original item with the cleaned version (in-place)
# Legacy format detection - Identifies old-style simple string arrays

# Dual purpose - Works for both text extraction and JSON cleaning

# In-place modification - Updates items directly in the original list

# Empty string handling - Skips empty items to avoid extra spaces

# Validation - Ensures all items are strings to prevent corruption

# Key Concept: This function bridges the gap between old and new list formats in EditorJS, ensuring backward compatibility while maintaining security through HTML sanitization. It's designed to work seamlessly with the main cleaning pipeline, whether the output is needed as JSON or plain text.

def clean_meta_block(block: NestedListItemType | dict) -> None:
    #     → Defines a function that sanitizes the meta property of an EditorJS block, preventing XSS attacks and enforcing data type constraints.

    # What it does:
    # Retrieves the meta dictionary from a block

    # Ensures it's a valid dictionary (not a string, list, etc.)

    # Validates each key is a string

    # Sanitizes string values (removes HTML/scripts)

    # Allows only strings, numbers, booleans, or None as values

    # Limits the total number of meta fields to 10
    """Clean the meta property of a given block.

    Args:
        block: the EditorJS block to clean which contains (or may contain) the 'meta' key
               at the root of the object.

    """

    key_count = 0
    # → Counter to track number of fields in the meta dictionary

    meta = block.get("meta") or {}
    # → Safely retrieves the 'meta' key, defaults to empty dict if missing
    if isinstance(meta, (dict)) is False:
        #         → Ensures meta is a dictionary
        # → Raises error if meta is string, list, number, etc.
        raise ValidationError(
            "Invalid meta block for EditorJS: meta property must be an object"
        )

    for k, v in meta.items():
        # → Iterates through each key-value pair in the meta dictionary
        # Validate the key
        if isinstance(k, str) is False:
            #             → Validates that every key is a string
            # → Prevents using numbers, booleans, or objects as keys
            raise ValidationError(
                "Invalid property for a meta member for EditorJS: must a string"
            )

        # Validate the value
        if isinstance(v, str):
            #             → If value is a string, sanitizes it with clean_text_data_block()
            # → Removes any HTML tags or JavaScript
            meta[k] = clean_text_data_block(v)
        elif isinstance(v, int | float | bool) is False and v is not None:
            #             → Allows numbers (int/float), booleans, and None
            # → Rejects lists, dictionaries, or other objects
            raise ValidationError(
                "Invalid meta block for EditorJS: value of a meta must either "
                "a string, an integer, or a float"
            )

        # Stop processing if an excessive key count is found
        key_count += 1
        if key_count > 10:
            #             → Counts each meta field
            # → Rejects meta objects with more than 10 fields (DoS protection)
            raise ValidationError("Invalid meta block for EditorJS: too many fields")
# Purpose: Sanitizes EditorJS block metadata

# Cleans: String values (removes HTML/scripts)

# Validates: Keys must be strings, values must be string/number/bool/None

# Limits: Maximum 10 fields per meta block

# Security: Prevents XSS, DoS, and type injection attacks

# Key Concept: This function ensures that user-provided metadata in rich text content is safe, properly typed, and limited in size, preventing both injection attacks and resource exhaustion while preserving legitimate data.

def clean_nested_list(
    items: list[NestedListItemType],
    *,
    current_depth: int,
    max_depth: int,
    to_string: bool,
    plain_text_list: list[str],
):
    #     → Defines a recursive function that cleans nested list items in EditorJS content, handling both plain text extraction and HTML sanitization.

    # What it does:
    # Recursively traverses a nested list structure, cleaning each item's content and metadata, while respecting maximum depth limits.
    # Note: this already validated by ``clean_list_item()`` however, we still need
    #       to perform this check as we are doing recursive checks which thus weren't
    #       checked yet.
    if isinstance(items, list) is False:
        raise ValidationError("Invalid EditorJS list: items must be inside an array")
    # → Ensures items is a list (not None, dict, string, etc.)
    if current_depth > max_depth:
        raise ValidationError("Invalid EditorJS list: maximum nesting level exceeeded")
    # → Prevents infinite recursion / DoS attacks by limiting nesting depth
    # → Example: max_depth=3 allows 3 levels of nesting
    for item in items:
        if isinstance(item, dict) is False:
            # Mixing types or version (legacy vs new lists) isn't allowed by Saleor,
            # nor by EditorJS.
            raise ValidationError("Invalid EditorJS list: items must be objects")
        # → Each list item must be a dictionary (not a string like legacy lists)
        text = item.get("content", "")
        if isinstance(text, str) is False:
            raise ValidationError(
                "Invalid EditorJS list: the text contents must be a string"
            )
        #  Ensures each item has a string content field

        if to_string:
            # Only append the text if it's not empty as we do a `' '.join(...)`
            # i.e., otherwise it will create unneeded (and ugly) whitespaces.
            if text:
                plain_text_list.append(strip_tags(text))
        else:
            item["content"] = clean_text_data_block(text)
            clean_meta_block(item)
        #             → to_string=True: Extracts plain text (no HTML tags) for previews
        # → to_string=False: Sanitizes HTML and cleans metadata in-place

        # Cleans the children (if any)
        clean_nested_list(
            items=item.get("items", []),
            current_depth=current_depth + 1,
            max_depth=max_depth,
            to_string=to_string,
            plain_text_list=plain_text_list,
        )


# → Processes child items recursively, incrementing depth counter
# Purpose: Recursively clean nested list structures in EditorJS

# Modes:

# JSON mode (to_string=False): Sanitize HTML in-place

# Text mode (to_string=True): Extract plain text

# Validation: Type checking, depth limiting, structure validation

# Security: Prevents XSS, DoS, and malformed data

# Recursion: Processes unlimited nesting levels (up to max_depth)

# Key Concept: This function handles the recursive nature of nested lists in rich text editors, ensuring every level is properly sanitized whether the output is HTML-safe JSON or plain text for previews. The depth limit prevents malicious deeply-nested lists from causing stack overflows.

def clean_list_item(
    block: dict,
    plain_text_list,
    to_string: bool,
    *,
    max_depth: int,
):
#     → Defines a function that cleans EditorJS list blocks, handling both legacy (flat) and modern (nested) list formats.

# What it does:
# Processes a list block from EditorJS, determines whether it's legacy or modern format, and applies the appropriate cleaning function.
    """Clean EditorJS lists, both legacy (non-nested) and the latest format (nested).

    Args:
        blocks: the list of blocks inside the EditorJS data that we are currently
                cleaning.

        block: the block to clean (`type: list`)

        to_string: whether the results should be exported to plaintext instead of
                   EditorJS format.

        plain_text_list: array of plaintext values to append into when ``to_string``
                         is set to ``True``.

        index: the block's position in the ``blocks`` array.

        max_depth: the maximum level of the list nesting. Limits the amount of recursions
                   done. Must not be set too high (recommended value: 10)

        current_depth: should be set to 0 on the first call, then it gets automatically
                       incremented during the recursive calls in order to keep track of
                       the call depth.

    """

    data = block["data"]
#     → Extracts the data portion of the list block
# → Structure: {"style": "unordered", "items": [...]}
    clean_meta_block(data)
    # → Cleans metadata in the list data (max 10 fields, string values sanitized)

    items = data.get("items", [])
    if isinstance(items, list) is False:
        raise ValidationError("Invalid EditorJS list: items property must be an array")
    items = cast(list, items)
    # → Ensures items is a list (not None, string, dict, etc.)

    # Cleans the list style (unordered|ordered|checklist)
    # It's valid both for legacy and new (nested) list formats
    style: None | str
    if style := data.get("style"):
        if isinstance(style, str) is False:
            raise ValidationError(
                "Invalid EditorJS list: style property must be a string"
            )
        data["style"] = clean_text_data_block(style)
#         → Cleans the list style property (unordered, ordered, checklist)
# → Removes any HTML/scripts from the style value

    # List empty
    if not items:
        return
    # → Nothing to clean if list is empty
    # Looks at the first item to determine whether it's legacy or nested (the new type).
    # We do not do this in a loop as we shouldn't allow users to mix legacy and
    # non-legacy within a block, this isn't valid EditorJS and thus should be rejected
    # by `clean_legacy_list()` and `clean_nested_list()` but this validation is deferred
    # to these functions in order to not iterate multiple times the lists.
    if isinstance(items[0], str):
        # Support for **legacy** lists (https://github.com/editor-js/list-legacy/blob/381254443234ebbec9cc508fa8a7b982b6a79418/README.md#output-data)
        clean_legacy_list(items, to_string=to_string, plain_text_list=plain_text_list)
    elif isinstance(items[0], dict):
        # Support for the new format (nested lists, https://github.com/editor-js/list/blob/f8cde313224499ed5bcf3e93864fc11c45fe7efb/README.md#output-data)
        clean_nested_list(
            items,
            max_depth=max_depth,
            current_depth=0,
            to_string=to_string,
            plain_text_list=plain_text_list,
        )
    else:
        raise ValidationError(
            "Invalid EditorJS list: items must be either a string or an object"
        )
#     → Checks the first item to determine list format:

# String = Legacy (flat list of strings)

# Dictionary = Modern (nested list with content/meta/items)

# Other = Invalid
# Purpose: Clean EditorJS list blocks supporting both legacy and modern formats

# Detection: Determines format by checking type of first item

# Legacy format: Simple array of strings → clean_legacy_list()

# Modern format: Nested objects → clean_nested_list()

# Security: Cleans metadata, style, and content based on format

# Flexibility: Works with both to_string=True (text extraction) and to_string=False (JSON cleaning)

# Key Concept: EditorJS has two different list formats (legacy simple arrays and modern nested objects). This function intelligently detects which format is being used and routes to the appropriate cleaner, maintaining backward compatibility while supporting newer features. The detection is done by examining the first item's type, assuming all items in a list block are consistently formatted.

def clean_image_item(blocks, block, plain_text_list, to_string, index):
#     → Defines a function that cleans image blocks in EditorJS content, handling both URL sanitization and caption cleaning.

# What it does:
# Processes image blocks by cleaning image URLs (preventing malicious links) and sanitizing caption text (removing XSS attacks).
    data = block["data"]
#     → Extracts the image data from the block
# → Structure: {"file": {"url": "..."}, "caption": "..."}

    for obj in (
        # data.file.url -> support for newer versions of Edjs (2.x)
        data.get("file", {}),
        # data.url -> support for older version (1.x)
        data,
    ):
#         → Checks two possible locations for image URL:

# Newer version (2.x): URL stored in data.file.url

# Older version (1.x): URL stored directly in data.url
# → Provides backward compatibility with different EditorJS versions
        if file_url := obj.get("url"):
#             → Uses walrus operator to check if URL exists and assign it to file_url
# → Only proceeds if URL is present
            if to_string:
                plain_text_list.append(strip_tags(file_url))
            else:
                file_url = clean_url(file_url)
                obj["url"] = file_url
#                 → to_string=True: Strips HTML tags from URL and adds to plain text list
# → to_string=False: Sanitizes URL (removes malicious schemes, JavaScript, etc.)

    if caption := data.get("caption"):
        if to_string:
            plain_text_list.append(strip_tags(caption))
        else:
            caption = clean_text_data_block(caption)
            data["caption"] = caption
# → Checks if caption exists
# → to_string=True: Strips HTML and adds to plain text list
# → to_string=False: Sanitizes caption content (removes scripts, dangerous HTML)

# Purpose: Clean image blocks in EditorJS content

# Handles: URL sanitization, caption cleaning, backward compatibility

# Versions supported: EditorJS 1.x (direct URL) and 2.x (nested file.url)

# Modes:

# JSON mode: Sanitizes in-place

# Text mode: Extracts plain text

# Security: Prevents XSS, malicious URLs, HTML injection

# Key Concept: Image blocks can contain dangerous content in two places: the image URL (could be javascript: or data: schemes) and the caption (could contain scripts). This function cleans both while maintaining backward compatibility with different EditorJS versions, ensuring safe rendering regardless of which version created the content.


def clean_embed_item(blocks, block, plain_text_list, to_string, index):
#     → Defines a function that cleans embedded content blocks (YouTube, Twitter, etc.) in EditorJS, sanitizing URLs and metadata.

# What it does:
# Processes embed blocks by cleaning source URLs, embed URLs, captions, and service names to prevent XSS and malicious content.
    for field in ["source", "embed"]:
#         → Iterates over two possible URL fields in embed blocks:

# source: Original source URL (e.g., YouTube video page)

# embed: Embedded iframe URL (e.g., YouTube embed link)
        data = block["data"].get(field)
        if not data:
            continue
#         → Retrieves the URL for current field
# → Skips if field doesn't exist or is empty
        if to_string:
            plain_text_list.append(strip_tags(data))
        else:
            data = clean_url(data)
            blocks[index]["data"][field] = data
#             → to_string=True: Strips HTML and adds URL to plain text list
# → to_string=False: Sanitizes URL and updates in-place

    caption = block["data"].get("caption")
    if caption:
        if to_string:
            plain_text_list.append(strip_tags(caption))
        else:
            blocks[index]["data"]["caption"] = clean_text_data_block(caption)
#             → Processes caption text (like image captions)
# → Text mode: Strips HTML and appends
# → JSON mode: Sanitizes HTML/scripts

    if service := block["data"].get("service"):
        block["data"]["service"] = clean_text_data_block(service)
#         → Cleans the service identifier (e.g., "youtube", "twitter", "vimeo")
# → Always sanitized (even in text mode, as it's metadata not displayed)
# Why Clean Both Source and Embed:
# Field	Purpose	Risk
# source	Original content URL	Malicious redirects, XSS
# embed	Embedded player URL	Iframe injection, malicious embeds
# caption	User-provided text	XSS, HTML injection
# service	Service identifier	HTML injection, spoofing
# Security Features Summary:
# Component	Cleaning Method	Prevents
# source URL	clean_url()	XSS, malicious schemes
# embed URL	clean_url()	Iframe injection, XSS
# caption	clean_text_data_block()	XSS, HTML injection
# service	clean_text_data_block()	Service spoofing, XSS
# Purpose: Clean embedded content blocks in EditorJS

# Handles: Source URLs, embed URLs, captions, service names

# Modes:

# JSON mode: Sanitizes in-place

# Text mode: Extracts plain text

# Security: Prevents XSS, malicious URLs, service spoofing

# Flexibility: Supports various embed services (YouTube, Twitter, etc.)

# Key Concept: Embed blocks can contain dangerous content in multiple fields - the source URL (could be malicious), embed URL (could inject iframes), caption (could contain scripts), and service name (could spoof legitimate services). This function sanitizes each field appropriately while maintaining backward compatibility and supporting both plain text extraction and JSON cleaning modes.


def clean_quote_item(blocks, block, plain_text_list, to_string, index):
#     → Defines a function that cleans quote blocks in EditorJS, sanitizing all text fields to prevent XSS attacks.

# What it does:
# Processes quote blocks by sanitizing the quoted text, caption, and alignment fields, while supporting both JSON cleaning and plain text extraction modes.
    """Clean a EditorJS `quote` block.

    Follows the specs from https://github.com/editor-js/quote/blob/78f70cf2391cc8aaf2d2e59615de3ad833d180c3/README.md#output-data
    """

    # Cleans all EditorJS fields from the data block
    for field in ["text", "caption", "alignment", "align"]:
#         → Iterates through all possible fields in a quote block:

# text: The quoted content

# caption: Attribution or source of quote

# alignment: Text alignment (left, center, right) - modern format

# align: Text alignment - legacy format (older versions)
        data = block["data"].get(field)
        if not data:
            continue
#         → Retrieves the field value
# → Skips if field doesn't exist or is empty
        blocks[index]["data"][field] = clean_text_data_block(data)
#         → Sanitizes the field content (removes HTML/scripts)
# → Updates the block in-place (regardless of to_string mode)

    if text := block["data"].get("text"):
        plain_text_list.append(strip_tags(text))
#         → If to_string=True, extracts the quote text for plain text output
# → Uses strip_tags() to remove HTML (but already cleaned by clean_text_data_block)
# Purpose: Clean quote blocks in EditorJS content

# Handles: Quote text, caption, alignment (both modern and legacy)

# Modes:

# JSON mode: Sanitizes all fields in-place

# Text mode: Sanitizes fields and extracts quote text

# Security: Removes XSS, scripts, and dangerous HTML from all fields

# Backward compatibility: Supports both 'alignment' and 'align' field names

# Key Concept: Quote blocks can contain dangerous content in the quoted text, attribution, and alignment fields. This function comprehensively sanitizes all possible fields while supporting both modern and legacy EditorJS versions. The cleaning happens regardless of output mode to ensure the stored data is always safe, with text extraction optionally providing plain text for previews.

def clean_text_items(
    blocks,
    block,
    plain_text_list,
    to_string,
    index,
    *,
    block_type: str,
):
#     → Defines a function that cleans text-based blocks (paragraphs, headers, etc.) in EditorJS, sanitizing content and metadata.

# What it does:
# Processes text blocks by validating block type, sanitizing text content, cleaning alignment fields, and converting heading levels to integers.
    if block_type not in ALLOWED_TEXT_BLOCK_TYPES:
        raise ValidationError(f"Unsupported block type: {block_type!r}")
# → Validates that the block type is allowed (e.g., "paragraph", "header", "delimiter")
# → Prevents processing of unknown or malicious block types
    data = block["data"]
# → Extracts the data portion of the text block
    text = data.get("text")
    if text:
        if to_string:
            plain_text_list.append(strip_tags(text))
        else:
            new_text = clean_text_data_block(text)
            data["text"] = new_text
# → to_string=True: Strips HTML and adds to plain text list
# → to_string=False: Sanitizes HTML content (removes scripts, dangerous tags)
    for field in ("alignment", "align"):
        if value := data.get(field):
            data[field] = clean_text_data_block(value)
# → Handles both modern (alignment) and legacy (align) field names
# → Sanitizes alignment values (removes any HTML/scripts)
    if heading_level := data.get("level"):
        data["level"] = maybe_to_int(heading_level, name="Heading level")
# → Converts heading level (e.g., "1", "2") to integer
# → Validates it's a proper number (handles both string and int input)
# Purpose: Clean text-based EditorJS blocks (paragraphs, headers, etc.)

# Handles: Text content, alignment (modern/legacy), heading levels

# Modes:

# JSON mode: Sanitizes content in-place

# Text mode: Extracts plain text for previews

# Validation: Block type whitelist, type conversion for numbers

# Security: Removes XSS, scripts, and dangerous HTML from all fields

# Key Concept: Text blocks are the most common content type in EditorJS and can contain XSS attacks in multiple fields. This function provides a centralized cleaning mechanism that sanitizes text content, normalizes alignment fields (supporting both modern and legacy naming), and ensures heading levels are proper integers. The block type whitelist prevents processing of unsupported or malicious block types.


def clean_text_data_block(text: str) -> str:
    """Sanitize the text using nh3 to remove malicious tags and attributes."""
#     → Defines a function that sanitizes HTML text content using the nh3 library (Rust-based HTML sanitizer) to prevent XSS attacks.

# What it does:
# Uses nh3 (Amazon's Ammonia HTML sanitizer Python binding) to remove dangerous HTML tags, attributes, and JavaScript while preserving safe formatting.
    if not text:
        return text
# → Early return for empty or None text (optimization)
    return nh3.clean(
        # → Calls nh3's HTML sanitizer (fast, memory-safe Rust implementation)
        text,
        # → The HTML string to sanitize
        url_schemes=ALLOWED_URL_SCHEMES | settings.HTML_CLEANER_PREFS.allowed_schemes,
#         ALLOWED_URL_SCHEMES: Base schemes (http, https, plus custom cleaners)

# settings.HTML_CLEANER_PREFS.allowed_schemes: Project-specific schemes
# → | = Union operator (combines both sets)
        attributes=settings.HTML_CLEANER_PREFS.allowed_attributes,
        # → Specifies which HTML attributes are allowed (e.g., href, src, class)
        tag_attribute_values=settings.HTML_CLEANER_PREFS.allowed_attribute_values,
        # → Controls allowed values for specific attributes (e.g., target="_blank" only)
        link_rel=settings.HTML_CLEANER_PREFS.link_rel,
        #  Adds rel="noopener noreferrer" to links for security (prevents tab-nabbing)
    )
# Performance Benefits of nh3:
# Aspect	nh3	Alternative (bleach)
# Language	Rust (compiled)	Python
# Speed	Very fast (10-100x)	Slower
# Memory	Efficient	Higher overhead
# Security	Memory-safe	Memory-safe
# Purpose: Sanitize HTML to prevent XSS attacks

# Library: nh3 (Rust-based, fast, secure)

# Removes: Script tags, event handlers, dangerous schemes, malicious attributes

# Preserves: Safe formatting (bold, italic, links, images)

# Security features: URL scheme whitelist, attribute filtering, link security (rel)

# Performance: Much faster than Python-based sanitizers

# Key Concept: This function provides a secure, fast HTML sanitizer that removes all potentially dangerous content while preserving safe formatting. It uses nh3 (a Python binding for Amazon's Ammonia sanitizer written in Rust) for memory safety and performance. The configuration allows project-specific customization of allowed URLs, attributes, and values while maintaining strong security defaults.


def clean_url(dirty_url: str) -> str:
    """Check if URL scheme is allowed."""
#     → Defines a function that validates and sanitizes URLs, blocking dangerous schemes and applying scheme-specific cleaning.

# What it does:
# Validates URL format, checks if scheme is allowed, applies scheme-specific cleaning (e.g., quoting special characters), and returns a safe URL or #invalid for unsafe ones.
    if not dirty_url:
        return ""
    # → Returns empty string for empty/None input

    try:
        parsed_url = parse_url(dirty_url.strip())
    except ValueError:
        parsed_url = None
#         → Attempts to parse URL using urllib3's parser
# → Returns None if URL is malformed (e.g., missing scheme, invalid characters)

    if (
        parsed_url is None
        or parsed_url.scheme
        not in ALLOWED_URL_SCHEMES | settings.HTML_CLEANER_PREFS.allowed_schemes
    ):
        warnings.warn(
            f"An invalid url or disallowed URL was sent: {dirty_url}",
            stacklevel=3,
        )
        return "#invalid"
#     → Checks if URL parsed successfully AND scheme is allowed
# → If invalid or disallowed scheme, logs warning and returns #invalid

    # If the scheme is HTTP(S), then urllib3 already took care of normalization
    # and thus quoted everything that should be quoted (such as dangerous characters
    # like `"`)
    # See https://github.com/urllib3/urllib3/blob/bd37a23af4552548f55d3c723fcb604f9a4983ca/src/urllib3/util/url.py#L415-L446
    if parsed_url.scheme in ("https", "http"):
        return parsed_url.url
#     → Returns normalized URL as-is (urllib3 already sanitized it)
# → Example: "https://example.com/../path" → "https://example.com/path"

    url_cleaner = URL_SCHEME_CLEANERS.get(parsed_url.scheme, None)

    if url_cleaner is None:
        if parsed_url.scheme in settings.HTML_CLEANER_PREFS.allowed_schemes:
            # Deprecated: this is only for backward compatibility - it doesn't define
            #             a cleaner which is dangerous.
            return dirty_url
        # NOTE: this exception should never happen unless a maintainer didn't read the
        #       comment in ALLOWED_URL_SCHEMES
        raise KeyError("No URL cleaner defined", parsed_url.scheme)
# → Looks for scheme-specific cleaner (e.g., for ftp, mailto, tel)
# → If no cleaner but scheme is allowed (legacy config), returns unchanged (⚠️ dangerous)
# → Otherwise raises KeyError (should never happen with proper setup)
    try:
        return url_cleaner(dirty_url=dirty_url)
    except URLCleanerError as exc:
        # Note: InvalidUsage must NOT be handled (should return "Internal Error")
        #       it indicates a code bug if it's raised
        raise ValidationError(str(exc)) from exc
    except ValueError as exc:
        # Note: we do not do str(exc) as may reveal sensitive information
        raise ValidationError("Invalid URL") from exc
# → Calls scheme-specific cleaner (e.g., clean_ftp_url, clean_mailto_url)
# → Catches custom errors and re-raises as validation errors
# → Hides internal error details for security

# Security Features:
# Attack Type	How It's Blocked
# JavaScript injection	javascript: scheme not allowed
# Data URI attacks	data: scheme not allowed
# Malformed URLs	parse_url() fails, returns #invalid
# Unquoted characters	Scheme cleaners quote dangerous chars
# Path traversal	urllib3 normalizes .. and .
