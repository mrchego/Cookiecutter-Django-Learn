from typing import TYPE_CHECKING, Optional

from ...account.models import Address
from ...channel.models import Channel

if TYPE_CHECKING:
    from ...graphql.account.types import AddressInput


def get_active_country(
    channel: "Channel",
    shipping_address: Optional["Address"] = None,
    billing_address: Optional["Address"] = None,
    address_data: Optional["AddressInput"] = None,
):
#     → Defines a function that determines which country to use for tax calculations based on available address information.

# What it does:
# Implements a priority-based logic to determine the active country for tax calculations in e-commerce orders and checkouts.
    """Get country code for orders, checkouts and tax calculations.

    For checkouts and orders, there are following rules for determining the country
    code that should be used for tax calculations:
    - use country code from shipping address if it's provided in the first place
    - use country code from billing address if shipping address is not provided
    - if both shipping and billing addresses are not provided use the default country
    from channel

    To get country code from address data from mutation input use address_data parameter
    """
    if address_data is not None and address_data.country:
        return address_data.country
#     → First priority: Check if there's address data from a mutation input
# → Used when creating/updating an order/checkout via GraphQL mutation
# → Returns the country code from the input data

    if shipping_address:
        return shipping_address.country.code
# → Second priority: Use shipping address if available
# → Most accurate for tax calculation (where the product is being delivered)
    if billing_address:
        return billing_address.country.code
# → Third priority: Fall back to billing address if no shipping address
# → Used for digital goods or when shipping isn't required
    return channel.default_country.code
# → Final fallback: Use the channel's default country
# → Ensures there's always a country for tax calculation


# Aspect	Description
# Purpose	Determine active country for tax calculations
# Priority	Address input > Shipping > Billing > Channel default
# Use cases	Tax calculation, shipping restrictions, order creation
# Benefits	Consistent tax logic, handles edge cases, flexible
# Inputs	Channel, addresses, optional address data
# Key Concept: In e-commerce, tax calculation depends on where the product is shipped (or where the customer is located for digital goods). This function implements a priority-based system to determine the correct country for tax calculation, ensuring that taxes are always calculated correctly even when addresses are missing or when creating orders via API mutations.

