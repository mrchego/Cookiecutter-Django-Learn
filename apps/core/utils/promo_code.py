import secrets

# → Imports Python's secrets module, which provides cryptographically strong random number generation for security-sensitive applications.

# What it does:
# Generates random numbers, tokens, and passwords that are secure for cryptographic use (unlike the regular random module which is predictable).
from django.core.exceptions import ValidationError

from ...discount.models import VoucherCode
from ...giftcard.error_codes import GiftCardErrorCode
from ...giftcard.models import GiftCard


class InvalidPromoCode(ValidationError):
    #     → Defines a custom validation exception specifically for invalid promo code errors, providing a default error message structure.

    # What it does:
    # Creates a specialized exception for promo code validation failures that automatically formats the error message for Django's validation system.
    def __init__(self, message=None, **kwargs):
        #         What is a Constructor?
        # A constructor is a special method that automatically runs when you create a new object from a class. It sets up the initial state of the object.

        # Simple Analogy:
        # Think of a constructor like moving into a new house:

        # The house blueprint = the class

        # Building the actual house = creating an object

        # Moving in furniture and setting up rooms = the constructor
        #         → Constructor with optional custom message
        # → **kwargs passes through additional arguments to parent
        if message is None:
            # → If no custom message provided, use default error structure
            message = {
                "promo_code": ValidationError(
                    "Promo code is invalid", code=GiftCardErrorCode.INVALID.value
                )
            }
        #             → Creates a dictionary with field-specific error
        # → "promo_code" key indicates error belongs to promo_code field
        # → Nested ValidationError with message and error code
        # → Uses GiftCardErrorCode.INVALID.value for consistent error codes
        super().__init__(message, **kwargs)


# → Calls parent ValidationError constructor with the message
# Summary:
# Aspect	Explanation
# Purpose	Specialized exception for promo code validation
# Default error	{"promo_code": "Promo code is invalid"} with error code
# Custom error	Can provide specific error messages
# Inheritance	Extends Django's ValidationError
# Use case	E-commerce promo/discount code validation
# Key Concept: This custom exception simplifies promo code validation by providing a consistent default error format while allowing overrides for specific cases. The dictionary structure with field name "promo_code" integrates seamlessly with Django's form and validation system, automatically mapping the error to the correct form field. The inclusion of GiftCardErrorCode.INVALID.value provides a machine-readable error code that frontend applications can use to display appropriate messages or take specific actions.


def generate_promo_code():
    """Generate a promo unique code that can be used as a voucher or gift card code."""
    #     → Defines a function that generates a unique promotional code (voucher/gift card code) by generating random codes until it finds one that isn't already in use.

    # What it does:
    # Creates a random promo code, checks if it's already used, and keeps generating new ones until it finds an available (unique) code.
    code = generate_random_code()
    #     → Generates a random code (likely using secrets.token_urlsafe() or similar)
    # → Example output: "X7K9M2P5" or "SALE-2024-ABC123"
    while not is_available_promo_code(code):
        #         → Checks if the generated code is already used in the database
        # → is_available_promo_code() returns True if code is available (not used)
        # → Loop continues while code is NOT available (already taken)
        code = generate_random_code()
    #         → If code is already taken, generate a new random code
    # → Repeat until a unique code is found
    return code


# → Returns the first unique promo code found


def generate_random_code():
#     → Defines a function that generates a random code in a human-readable format with hyphens every 4 characters.

# What it does:
# Creates a random 12-character hexadecimal code (12 chars = 6 bytes) and formats it with hyphens as "XXXX-XXXX-XXXX".
    # generate code in format "ABCD-EFGH-IJKL"
    code = secrets.token_hex(nbytes=6).upper()
#     → secrets.token_hex(6) = Generates 6 random bytes (48 bits) as a hex string
# → 6 bytes = 12 hex characters (each byte = 2 hex chars)
# → Example: token_hex(6) returns "a7f3c8d2e1b4" (12 characters)
# → .upper() converts to uppercase: "A7F3C8D2E1B4"
    return "-".join(code[i : i + 4] for i in range(0, len(code), 4))  # noqa: E203
# → Splits the 12-character code into 3 chunks of 4 characters each
# → range(0, len(code), 4) = 0, 4, 8 (start, stop, step)
# → Chunks: code[0:4], code[4:8], code[8:12]
# → "-".join() combines chunks with hyphens
# → Final format: "A7F3-C8D2-E1B4"
# Summary:
# Aspect	Explanation
# Purpose	Generate human-readable random codes
# Format	XXXX-XXXX-XXXX (12 hex chars + 2 hyphens)
# Characters	0-9, A-F only (no confusing letters)
# Security	secrets.token_hex() (cryptographically secure)
# Length	6 bytes = 48 bits = 281 trillion possibilities
# Use case	Promo codes, gift cards, vouchers, referral codes
# Key Concept: This function generates cryptographically secure random codes in a user-friendly format. The use of secrets.token_hex() ensures the codes are unpredictable, while the "XXXX-XXXX-XXXX" format with hyphens makes them easy for customers to read, type, and share. The 12-character hex format provides 281 trillion possible combinations, making brute-force attacks impractical while keeping codes short enough for manual entry. The restriction to hexadecimal characters (0-9, A-F) eliminates ambiguous characters like 'O', 'I', 'l' that could confuse users.

def is_available_promo_code(code):
    return not (promo_code_is_gift_card(code) or promo_code_is_voucher(code))
# → Checks if a promo code is available for use by verifying it's not already assigned to a gift card or voucher.

# What it does:
# Returns True if the code is available (not used as a gift card or voucher), False if it's already taken.
# Summary:
# Aspect	Explanation
# Purpose	Check if promo code is available for use
# Checks	Gift card table AND voucher table
# Returns True	Code NOT in either table
# Returns False	Code IN gift cards OR vouchers
# Logic	not (is_gift_card or is_voucher)
# Use case	Generate unique codes, validate new promotions
# Key Concept: This function ensures promo code uniqueness across multiple tables (gift cards and vouchers) by checking if the code already exists in either system. It's a critical validation function that prevents code collisions when generating new promotions. The function returns True only when the code is completely unused in both tables, making it safe to assign to a new promotion. The simple boolean logic (not (A or B)) makes the intention clear: a code is available only if it's neither a gift card nor a voucher.

def promo_code_is_voucher(code):
    return VoucherCode.objects.filter(code=code).exists()
VoucherCode.objects.filter(code=code)
# → Django ORM query that filters the VoucherCode table for records matching the provided code
# → Returns a QuerySet (list-like object) of matching records
# .exists()
# → Checks if the QuerySet contains any records
# → Returns True if at least one voucher exists with this code
# → Returns False if no voucher has this code
# → Checks if a given code already exists as a voucher in the database.

# What it does:
# Queries the VoucherCode database table to see if a code has already been used as a voucher.
# Summary:
# Aspect	Explanation
# Purpose	Check if a code exists in the voucher table
# Returns True	Code found in VoucherCode table
# Returns False	Code not found in VoucherCode table
# Query type	.exists() for efficiency (LIMIT 1 query)
# Use case	Preventing duplicate codes, validating voucher codes
# Performance	Very fast (database index on code field recommended)
# Key Concept: This function provides a simple, efficient check for voucher code existence in the database. It's a fundamental building block for promo code systems, used to prevent duplicate codes when creating new vouchers and to validate codes when customers try to apply them. The use of .exists() instead of .get() or .count() ensures optimal performance by only checking for existence rather than loading full objects. This function works in conjunction with promo_code_is_gift_card() to provide complete promo code availability checking.

