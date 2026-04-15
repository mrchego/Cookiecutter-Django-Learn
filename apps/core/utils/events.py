from django.db import transaction
# → Imports Django's transaction module for managing database transactions, ensuring data consistency by grouping multiple database operations into atomic units.

# What it does:
# Provides decorators and context managers to control database transactions, ensuring that a series of operations either all succeed or all fail together.
from ...checkout.fetch import CheckoutInfo
from ...checkout.models import Checkout
from ...webhook.event_types import WebhookEventAsyncType
from ...webhook.models import Webhook

# What is a Webhook?
# A webhook is an automated message sent from one application to another when a specific event happens. Think of it as a "reverse API" - instead of you asking for data, the app sends it to you automatically.
# What "Payload Should Be Deferred" Means
# "Payload should be deferred" means: Don't generate the webhook data right now. Instead, generate it later in a background task (Celery).

# Simple Explanation:
# Think of ordering food at a restaurant:

# Scenario	Action	When food is prepared
# Not Deferred	Restaurant prepares food immediately	Right when you order
# Deferred	Restaurant takes your order, but prepares it later	When kitchen is ready
def get_is_deferred_payload(event_name: str) -> bool:
#     What it does:
# Checks whether a webhook event has a deferred payload - meaning the payload data should be generated asynchronously in a Celery task rather than immediately during the request.
    """Return True if the event has deferred payload.

    When the event has deferred payload, the payload will be generated in the Celery
    task during webhook delivery. In such case, any additional sync calls needed to
    generated the payload are also run in this task, and we don't need to call them
    manually before.
    """
    return WebhookEventAsyncType.EVENT_MAP.get(event_name, {}).get(
#         → Looks up the event configuration in the async event map
# → Returns empty dict {} if event not found
# → EVENT_MAP contains configuration for each webhook event type
        "is_deferred_payload", False
#         → Extracts the is_deferred_payload flag from the event config
# → Returns False if the flag doesn't exist (default behavior: immediate payload)
# return ...
# → Returns True if payload should be deferred, False otherwise
    )
# Purpose: Determine if webhook payload should be generated asynchronously

# Returns: True = defer to Celery task, False = generate immediately

# Use case: Heavy payloads (exports, reports, invoices) that would slow down requests

# Benefits: Faster request responses, better scalability, background processing

# Configuration: Defined in WebhookEventAsyncType.EVENT_MAP

# Key Concept: This function enables a performance optimization where expensive payload generation (like creating large CSV files or generating PDF invoices) is moved from the request/response cycle to background Celery tasks. The request returns immediately, and the payload is generated asynchronously, preventing slow operations from blocking the user.

def any_webhook_has_subscription(
    events: list[str], webhook_event_map: dict[str, set["Webhook"]]
) -> bool:
#     → Defines a function that checks if any webhook in the provided events has a GraphQL subscription query defined.

# What it does:
# Checks through a list of event types and returns True if any webhook registered for those events has a subscription_query (a GraphQL query that defines what data to send).
    event_has_subscription = False
    # → Initialize flag to False (no subscription found yet)
    for event in events:
        # → Loop through each event type (e.g., "order_created", "product_updated")
        event_has_subscription = any(
            bool(webhook.subscription_query)
            for webhook in webhook_event_map.get(event, [])
#             webhook_event_map.get(event, [])
#             → Get all webhooks registered for this event
# → Returns empty list [] if event has no webhooks
        )
#         → Checks each webhook to see if it has a subscription_query
# → bool(webhook.subscription_query) = True if subscription query exists, False if None or empty
# → any() = Returns True if ANY webhook in this event has a subscription
        if event_has_subscription:
            break
        # → If found a subscription in this event, stop checking other events (optimization)
    return event_has_subscription
# Summary:
# Aspect	Explanation
# Purpose	Check if any webhook needs subscription-based payload
# Input	List of events + map of webhooks by event
# Output	True if any webhook has subscription_query, else False
# Optimization	Breaks early when finding first subscription
# Use case	Determine if expensive GraphQL execution is needed
# Key Concept: This function optimizes webhook delivery by checking whether any webhook requires a custom GraphQL subscription payload. If none do, the system can use a faster default payload generation path. If at least one does, it knows it needs to execute GraphQL queries to generate the custom payloads.


def any_webhook_is_active_for_events(
    events: list[str], webhook_event_map: dict[str, set["Webhook"]]
) -> bool:
#     → Defines a function that checks whether there are any active webhooks registered for the given event types.

# What it does:
# Determines if at least one webhook exists and is active for any of the provided event names.
    """Check if any webhook is active for given events."""

    active_webhook_events = {
        event for event, webhooks in webhook_event_map.items() if webhooks
    }
#     → Creates a set of event names that have at least one webhook registered
# → if webhooks = Only includes events that have a non-empty set of webhooks
# → Example result: {"order_created", "product_updated"}
    if not active_webhook_events.intersection(events):
        return False
    return True
# → intersection(events) = Finds events that exist in BOTH sets (active webhook events AND requested events)
# → If intersection is empty (no matching events), returns False
# → If there are matches, continues to return True
# Summary:
# Aspect	Explanation
# Purpose	Quick check if any webhooks exist for given events
# Input	List of event names + map of webhooks by event
# Output	True if at least one event has registered webhooks
# Key feature	Only counts events with non-empty webhook sets
# Use case	Skip expensive webhook preparation when no webhooks exist
# Key Concept: This function provides a fast, early check to determine if webhook processing is needed. By checking the webhook-event map (which can be cached in memory), it avoids expensive database queries or payload generation when no webhooks are actually registered for the events being processed.

def _validate_event_name(event_name, webhook_event_map):
#     → Defines a private helper function that validates whether an event name is valid for async webhook processing.

# What it does:
# Performs two critical validation checks:

# Ensures the event is an async event type (not sync)

# Ensures the event has registered webhooks in the map
    is_async_event = event_name in WebhookEventAsyncType.ALL
#     → Checks if the event exists in the list of async event types
# → WebhookEventAsyncType.ALL contains all events that can be processed asynchronously
# → Examples: "order_created", "product_updated", "customer_registered"
    if not is_async_event:
        raise ValueError(f"Event {event_name} is not an async event.")
# → Raises error if event is not async (e.g., sync events that need immediate response)
    if event_name not in webhook_event_map:
        raise ValueError(f"Event {event_name} not found in webhook_event_map.")
# → Checks if there are any webhooks registered for this event
# → Raises error if no webhooks exist for this event
# Check	Purpose	Error
# Is async event?	Ensure event can be processed in background	"not an async event"
# Has webhooks?	Ensure there are subscribers for this event	"not found in webhook_event_map"
# Key Concept: This validation function acts as a gatekeeper, preventing webhook processing for:

# Sync events - which need immediate responses and can't be deferred to background tasks

# Events without subscribers - which would waste resources processing nothing

# This "fail fast" approach catches configuration errors early and avoids unnecessary background task queuing.


def _validate_webhook_event_map(webhook_event_map, possible_sync_events):
#     → Defines a private helper function that validates that all required sync events are present in the webhook event map.

# What it does:
# Checks that every sync event (events that need immediate processing during a request) has an entry in the webhook event map, even if that entry is an empty set
    missing_possible_sync_events_in_map = set(possible_sync_events).difference(
        webhook_event_map.keys()
    )
#     → set(possible_sync_events) = Converts list of required sync events to a set
# → .difference(webhook_event_map.keys()) = Finds events that are in required list but NOT in map keys
# → Result: Events that MUST exist but are missing
    if missing_possible_sync_events_in_map:
        raise ValueError(
            f"Event {missing_possible_sync_events_in_map} not found in webhook_event_map."
        )
# → If there are any missing required sync events, raise error
# → Prevents runtime failures when those events are triggered
# Summary:
# Aspect	Explanation
# Purpose	Validate that all required sync events exist in webhook map
# Input	Webhook event map + list of required sync events
# Checks	Finds required events that are missing from map
# Empty sets	Allowed (means no webhooks, but key exists)
# Error	Raises ValueError with list of missing events
# Key Concept: This validation function ensures the webhook event map is properly initialized with all required sync event keys before the application starts. It allows empty sets (meaning no webhooks registered for that event) but requires the key to exist. This prevents KeyError crashes at runtime when sync events are triggered, enabling safe direct dictionary access without .get() fallbacks.


def webhook_async_event_requires_sync_webhooks_to_trigger(
    event_name: str,
    webhook_event_map: dict[str, set["Webhook"]],
    possible_sync_events: list[str],
) -> bool:
    """Check if calling the event requires additional actions.

    In case of having active webhook with the `event_name`, the function will return
    True, when any sync from `possible_sync_events`'s webhooks are active. `True`
    means that sync webhook should be triggered first, before calling async webhook.
    """
#     → Determines whether an async webhook event needs to wait for sync webhooks to be triggered first (like payment authorization before order confirmation).

# What it does:
# Checks multiple conditions to decide if sync webhooks must be processed before async webhooks for a given event.
    _validate_event_name(event_name, webhook_event_map)
    # → Validates event exists and is async type
    _validate_webhook_event_map(webhook_event_map, possible_sync_events)
# → Ensures all sync events have entries in map
    is_deferred_payload = get_is_deferred_payload(event_name)
    if is_deferred_payload:
        return False
    # → If payload is deferred (generated later in Celery), sync webhooks not needed

    if not webhook_event_map[event_name] and not webhook_event_map.get(
        WebhookEventAsyncType.ANY
    ):
        return False
    # → No async webhooks for this event → return False

    if not any_webhook_is_active_for_events(possible_sync_events, webhook_event_map):
        return False
    # → No active sync webhooks → return False

    async_webhooks_have_subscriptions = any_webhook_has_subscription(
        [event_name], webhook_event_map
    )
    if not async_webhooks_have_subscriptions:
        return False

    # → Async webhooks need custom GraphQL subscriptions

    sync_events_have_subscriptions = any_webhook_has_subscription(
        possible_sync_events, webhook_event_map
    )
    if not sync_events_have_subscriptions:
        return False
    # → Sync webhooks need custom GraphQL subscriptions
    return True
# → All conditions met: sync webhooks must trigger before async
# Summary:
# Aspect	Explanation
# Purpose	Determine if sync webhooks must trigger before async
# Return True when	Async event has webhooks AND sync events have webhooks AND both need custom subscriptions
# Return False when	No webhooks, deferred payload, or no subscriptions needed
# Use case	Payment authorization before order processing
# Key insight	Ensures critical sync operations happen before async notifications
# Key Concept: This function solves a critical ordering problem in event-driven systems. For events like "order_created", you might need to authorize payment (sync webhook) before notifying fulfillment systems (async webhook). This function detects when this ordering is required based on which webhooks are active and whether they need custom GraphQL subscriptions.


def call_event_including_protected_events(func_obj, *func_args, **func_kwargs):
    """Call event without additional validation.

    This function triggers the event without any additional validation. It should be
    used when all additional actions are already handled. Additional actions like
    triggering all existing sync webhooks before calling async webhooks.
    """
#     → Defines a helper function that safely calls an event handler, ensuring it runs after the current database transaction commits if inside an atomic block.

# What it does:
# Executes an event function (like a webhook trigger) either immediately or after the current database transaction commits, depending on whether we're inside a transaction.
    connection = transaction.get_connection()
#     → Gets the current database connection
# → Used to check if we're inside an atomic transaction block
    if connection.in_atomic_block:
#         → Checks if we're currently inside a transaction (atomic() block)
# → in_atomic_block = True when inside with transaction.atomic():
        transaction.on_commit(lambda: func_obj(*func_args, **func_kwargs))
#         → Schedules the event function to run AFTER the transaction commits
# → If transaction rolls back, function never runs
# → Prevents calling event with uncommitted (potentially rolled back) data
    else:
        func_obj(*func_args, **func_kwargs)
# → If not in a transaction, call the function immediately
# Summary:
# Aspect	Explanation
# Purpose	Safely call event functions with transaction awareness
# Inside transaction	Defer execution until after commit
# Outside transaction	Execute immediately
# On rollback	Never executes (scheduled call discarded)
# Use case	Webhooks, notifications, side effects after data changes
# Key Concept: This function ensures that event handlers (like webhooks) only receive data that has been successfully committed to the database. If called inside a transaction, it defers execution until after commit. If the transaction rolls back, the event


def call_event(func_obj, *func_args, **func_kwargs):

    """Call webhook event with given args.

    Ensures that in atomic transaction event is called on_commit.
    """
#     → Defines a wrapper function that safely calls webhook events, with special handling for checkout-related events in PluginsManager.

# What it does:
# Acts as a gatekeeper that:

# Detects if the event involves Checkout data being passed to PluginsManager

# Blocks checkout events (currently unsupported) with clear error

# Passes through all other events to the protected caller
    is_protected_instance = any(
        isinstance(arg, Checkout | CheckoutInfo) for arg in func_args
    )
#     → Checks if ANY argument passed to the event is a Checkout or CheckoutInfo object
# → any() = Returns True if at least one argument matches
# → Used to detect if this is a checkout-related event
    func_obj_self = getattr(func_obj, "__self__", None)
#     → Gets the self instance from a bound method
# → For PluginsManager.method, this returns the PluginsManager instance
# → For regular functions, returns None
    is_plugin_manager_method = "PluginsManager" in str(
        getattr(func_obj_self, "__class__", "")
    )
#     → Checks if the method belongs to PluginsManager class
# → Converts class to string and looks for "PluginsManager" in the name
# → Example: "<class 'plugins.manager.PluginsManager'>" → True
    if is_protected_instance and is_plugin_manager_method:
        raise NotImplementedError("`call_event` doesn't support checkout events.")
    # → If BOTH conditions are True:

# Event has Checkout/CheckoutInfo argument

# Method belongs to PluginsManager
# → Raises NotImplementedError - checkout events not supported
    call_event_including_protected_events(func_obj, *func_args, **func_kwargs)
# → For all other events (non-checkout), delegate to the safe caller
# → Handles transaction-aware execution (on_commit if needed)
# Summary:
# Aspect	Explanation
# Purpose	Safe webhook event calling with checkout event blocking
# Blocks	Any event with Checkout/CheckoutInfo argument
# Allows	Events without checkout arguments
# Why block	Checkout events are complex and would cause inconsistent webhooks
# Alternative	Use order events after checkout completion
# Key Concept: This function prevents calling webhook events that involve Checkout objects because checkout is a temporary, multi-step process. Webhooks triggered during checkout could send incomplete or intermediate data. Instead, developers should use order events (after checkout completes) or handle checkout webhooks separately. This design prevents subtle bugs and inconsistent webhook payloads.
