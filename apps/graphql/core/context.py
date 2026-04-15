import datetime
# → Imports Python's datetime module for date and time operations.
from dataclasses import dataclass
# → Imports the dataclass decorator for creating classes that primarily store data.
from typing import TYPE_CHECKING, Any, Generic, TypeVar
# TYPE_CHECKING = Constant that's True during type checking (mypy/pyright), False at runtime. Used for conditional imports that only type checkers need.
# Any = Type that accepts any Python value (disables type checking)
# Generic = Base class for creating generic types
# TypeVar = Creates type variables for generics
from django.conf import settings
# → Django settings object with all project configuration.
from django.db.models import Model, QuerySet
# Model = Base class for Django database models
# QuerySet = Represents a collection of database objects
from django.http import HttpRequest
# → Django's HTTP request object containing metadata about the request.
from django.utils.functional import empty
# → Special marker object used internally by Django to detect if a value is missing (like a sentinel value).

if TYPE_CHECKING:
    from ...account.models import User
    from ...app.models import App
    from .dataloaders import DataLoader

# → A conditional import block that only runs during static type checking (by tools like mypy, Pyright), not at runtime.

# What it does:
# TYPE_CHECKING is a constant that is True when type checkers are analyzing the code, but False during normal execution

# These imports are only for type hints and IDE autocomplete

# They prevent circular import issues at runtime

class SaleorContext(HttpRequest):
    # → Defines a custom context class that extends Django's HttpRequest for GraphQL operations in Saleor (an e-commerce platform). This combines HTTP request data with additional context needed for GraphQL execution.
    _cached_user: "User | None"
    # → Private attribute storing cached user object to avoid repeated database queries.
    decoded_auth_token: dict[str, Any] | None
    # → Stores the decoded JWT authentication token payload (contains user ID, permissions, etc.).
    allow_replica: bool = True
    # → Flag indicating whether read operations can use database replicas (for load balancing).
    dataloaders: dict[str, "DataLoader"]
    # → Dictionary of DataLoader instances for batching and caching database queries (prevents N+1 queries).
    app: "App | None"
    # → OAuth/App authentication context (for API access via apps).
    user: "User | None"  # type: ignore[assignment]
    # → Currently authenticated user (from session or token). The # type: ignore suppresses type checker warnings.
    requestor: "App | User | None"
    # → Generic identifier of who made the request (either a user or an app).
    request_time: datetime.datetime
# → Timestamp when the request was received (for logging and performance tracking).

    def __init__(self, *args, **kwargs):
        # → Defines the constructor method for the SaleorContext class that initializes the context object.
        if "dataloaders" in kwargs:
            # An argument is a value passed to a function, method, or class when it's called. In Django, arguments are used everywhere to pass data, configure behavior, and control logic
#             → Checks if a 'dataloaders' keyword argument was passed to the constructor.
# → kwargs = Dictionary of all keyword arguments (e.g., dataloaders={...})
            self.dataloaders = kwargs.pop("dataloaders")
            # pop() is a Python dictionary method, not Django-specific, but heavily used in Django to remove and return a key-value pair from a dictionary. It's commonly used in Django for processing keyword arguments (**kwargs).
#             → Extracts the dataloaders from kwargs and assigns to instance attribute.
# → pop() = Removes the 'dataloaders' key from kwargs (so it's not passed to parent)
# → self.dataloaders = Stores DataLoader dictionary on the instance
        super().__init__(*args, **kwargs)
#         → Calls the parent class constructor (HttpRequest) with remaining arguments.
# → *args = Positional arguments (unchanged)
# → **kwargs = Remaining keyword arguments (dataloaders removed)


def disallow_replica_in_context(context: SaleorContext) -> None:
    """Set information in context to use database replicas or not.

    Part of the database read replicas in Saleor.
    When Saleor builds a response for mutation `context` stores information
    `allow_replica=False`. That means that all data should be provided from
    the master database.
    When Saleor builds a response for query, set `allow_replica`=True in `context`.
    That means that all data should be provided from reading replica of the database.
    Database read replica couldn't be used to save any data.
    """
    context.allow_replica = False
#     → Defines a function that disables the use of database replicas for a given request context.

# What it does:
# Sets allow_replica = False on the context object, forcing all subsequent database operations to use the master (primary) database instead of read replicas.

def get_database_connection_name(context: SaleorContext) -> str:
    """Retrieve connection name based on request context.

    Part of the database read replicas in Saleor.
    Return proper connection name based on `context`.
    For more info check `disallow_replica_in_context`
    Add `.using(connection_name)` to use connection name in QuerySet.
    Queryset to main database: `User.objects.all()`.
    Queryset to read replica: `User.objects.using(connection_name).all()`.
    """
    allow_replica = getattr(context, "allow_replica", True)
#     → Safely retrieves the allow_replica attribute from the context object.
# → getattr() = Gets attribute if exists, otherwise returns default
# → True = Default value (assume replicas are allowed unless specified otherwise)
    if allow_replica:
        return settings.DATABASE_CONNECTION_REPLICA_NAME
#     → If replicas are allowed, return the replica database connection name.
# → Used for read operations (queries) where eventual consistency is acceptable.
    return settings.DATABASE_CONNECTION_DEFAULT_NAME
#    VVV
# → Defines a function that returns the appropriate database connection name based on the request context.

# What it does:
# Determines whether to use the master database or a read replica based on the allow_replica flag in the context.


def setup_context_user(context: SaleorContext) -> None:
#     → Defines a function that ensures the user object in the context is fully loaded and resolved, not a lazy proxy.

# What it does:
# Checks if context.user is a lazy-loaded proxy object (using Django's LazyObject) and forces it to load the actual user object.
    if hasattr(context.user, "_wrapped") and (
#         → Checks if the user object has a _wrapped attribute.
# → _wrapped indicates this is a Django LazyObject (lazy-loading wrapper) rather than a real user instance.
# → Only lazy objects have this attribute.
        context.user._wrapped is empty or context.user._wrapped is None  # type: ignore[union-attr]
#         → Checks if the wrapped value is still empty/uninitialized.
# → empty = Special Django sentinel value meaning "not yet loaded"
# → None = No user (anonymous)
# → If either is true, the lazy object hasn't been resolved yet.
    ):
        context.user._setup()  # type: ignore[union-attr]
#         → Calls the internal _setup() method that forces the lazy object to load.
# → This resolves the proxy to the actual user instance.
# → # type: ignore = Suppresses type checker warnings (internal Django method).
        context.user = context.user._wrapped  # type: ignore[union-attr]
#         → Replaces the lazy proxy with the actual user object.
# → After this, context.user is the real User instance (or None).


N = TypeVar("N")
# → Creates a generic type variable named "N" that can be used for type hints, allowing functions and classes to work with any type while maintaining type safety.

# What it does:
# TypeVar defines a placeholder type that can be substituted with any concrete type when the code is used. This enables generics - code that works with multiple types while still providing type checking.


@dataclass
# → Decorator that automatically generates common methods like __init__, __repr__, __eq__ for the class.
# → Saves writing boilerplate code.
class BaseContext[N]:
#     → Defines a generic class with a type parameter N.
# → N can be any type that will be specified when using the class.
# → Similar to List[T] or Optional[T] in Python type hints.
    node: N
#     → Class attribute that holds the node of type N.
# → The actual type is determined when the class is instantiated.
# → Defines a generic dataclass that can hold any type of node, with the type specified as a generic parameter N.


@dataclass
class SyncWebhookControlContext(BaseContext[N]):
    # Webhooks are automated messages sent from one application to another when a specific event happens. They're like "reverse APIs" - instead of one app asking for data, the app sends data automatically when something occurs.
#     → Defines a dataclass that inherits from BaseContext[N], adding webhook control functionality.
# → BaseContext[N] = Parent class with node: N attribute
# → N = Generic type parameter (the node can be any type)
# → Adds control over whether synchronous webhooks should be triggered

# What it does:
# This context class controls whether synchronous webhooks (real-time webhook calls that must complete before the response) should be executed during operations
    allow_sync_webhooks: bool = True
# → Class attribute (dataclass field) that determines if sync webhooks are allowed
# → Default is True (webhooks will fire by default)
    def __init__(self, node: N, allow_sync_webhooks: bool = True):
#         → Constructor that explicitly defines parameters
# → node: N = The node object (can be User, Product, Order, etc.)
# → allow_sync_webhooks = Optional parameter, defaults to True
        self.node = node
        # → Sets the node attribute (inherited from BaseContext)
        self.allow_sync_webhooks = allow_sync_webhooks
        # → Sets whether sync webhooks are allowed
# Why Explicit init?
# Even though @dataclass auto-generates __init__, this class explicitly defines it to:

# Show clear parameter order

# Add custom initialization logic (if needed later)

# Make it obvious that node is required

@dataclass
# → Automatically generates __init__, __repr__, __eq__ methods
class ChannelContext(BaseContext[N]):
#     → Inherits from BaseContext[N], which has node: N attribute
# → N = Generic type (can be any node type)
    channel_slug: str | None
#     → Adds a channel_slug attribute
# → str | None = Can be a string (channel identifier) or None (no channel specified)
# → A "slug" is a URL-friendly identifier (e.g., "default-channel", "us-store", "eu-store")
# → Defines a dataclass that extends BaseContext[N] to add channel/sales channel information to the context.

# What it does:
# Adds channel (sales channel) context to any node, allowing operations to know which sales channel (e.g., online store, mobile app, physical store) the operation belongs to.


M = TypeVar("M", bound=Model)
# → Creates a generic type variable M that is constrained to only Django Model classes or their subclasses.
# What it does:
# bound=Model means this type variable can only be used with classes that are Django Models (inherit from django.db.models.Model).


@dataclass
# → Automatically generates __init__, __repr__, __eq__ methods
class ChannelQsContext(Generic[M]):
#     → Generic class where M is a Django Model type
# → M = TypeVar("M", bound=models.Model) (defined elsewhere)
# → Holds a queryset of type QuerySet[M]
    qs: QuerySet[M]
#     → The QuerySet containing models of type M
# → Type-safe - type checker knows what models are in the queryset
    channel_slug: str | None
# → Sales channel identifier (e.g., "us-store", "eu-store", "mobile-app")
# → None means no channel filtering
# → Defines a generic dataclass that combines a Django QuerySet with channel/sales channel context.

# What it does:
# Holds a type-safe QuerySet of Django Models along with a channel slug, allowing channel-aware database queries and filtering.
