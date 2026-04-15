import functools

# → Imports Python's functools module for higher-order functions (functions that operate on or return other functions)
from collections.abc import Callable

# → Imports the Callable type hint for objects that can be called like functions.
from typing import Any

# → Imports the Any type hint for values that can be any type (disables type checking)
from django.utils.functional import LazyObject, SimpleLazyObject, empty


# → Imports Django's lazy loading utilities:
# LazyObject: Base class for creating lazy-loaded objects
# SimpleLazyObject: Simple wrapper that delays object creation until first access
# empty: Special sentinel value indicating "not yet loaded"
def lazy_no_retry(func: Callable) -> SimpleLazyObject:
    #     → Defines a function that creates a lazy wrapper that never retries a failed operation.

    # What it does:
    # Wraps a function in a SimpleLazyObject that caches the result, but if the function fails, it remembers the error and never tries again (prevents repeated expensive failures).
    """Wrap SimpleLazyObject while ensuring it is never re-evaluated on failure.

    Wraps a given function into a ``SimpleLazyObject`` class while ensuring
    if ``func`` fails, then ``func`` is never invoked again.

    This mitigates an issue where an expensive ``func`` can be rerun for
    each GraphQL resolver instead of flagging it as rejected/failed.
    """
    error: Exception | None = None

    # → Creates a closure variable to store any exception that occurred
    # → Starts as None (no error yet)
    # → nonlocal error inside the wrapper allows modifying this variable
    @functools.wraps(func)
    def _wrapper():
        #         → Decorator that preserves the original function's metadata (name, docstring, etc.)
        # → Makes debugging easier (wrapper looks like the original function)
        nonlocal error
        # → Allows modifying the error variable from the outer scope
        # → Required because we're inside a nested function
        # If it was already evaluated, and it crashed, then do not re-attempt.
        if error:
            raise error
        #         → If an error was stored from a previous attempt, immediately raise it
        # → Prevents re-executing the function

        try:
            return func()
        #         → Execute the wrapped function
        # → If successful, return its result (which gets cached by SimpleLazyObject)
        except Exception as exc:
            error = exc
            raise

    #         → If function fails, store the exception in the closure
    # → Re-raise the same exception
    # → Future attempts will immediately raise the stored error

    return SimpleLazyObject(_wrapper)


# → Wrap the wrapper in Django's SimpleLazyObject
# → This ensures the function is only called once (on first access)
# → The result is cached for subsequent accesses
# Aspect	Description
# Purpose	Create a lazy wrapper that never retries on failure
# Problem	SimpleLazyObject retries failed functions repeatedly
# Solution	Cache exceptions and re-raise them without re-executing
# Use cases	GraphQL resolvers, API clients, config loading, expensive operations
# Benefits	Prevents wasted work, consistent error behavior, better performance
# Key Concept: In GraphQL and other systems, a single request might access the same lazy value multiple times. If that value is expensive to compute and fails, re-attempting it for every access is wasteful. lazy_no_retry solves this by caching the exception, ensuring that a failed expensive operation is never attempted again within the same context.


def unwrap_lazy(obj: LazyObject) -> Any:
    #     → Defines a function that forces a lazy object to be evaluated and returns its actual value.

    # What it does:
    # Checks if a LazyObject is already loaded; if not, forces it to load (_setup()), then returns the wrapped value
    """Return the value of a given ``LazyObject``."""
    if obj._wrapped is empty:  # type: ignore[attr-defined] # valid attribute
        #         → Checks if the lazy object's wrapped value is the special empty sentinel
        # → empty = Django's marker meaning "not yet loaded"
        obj._setup()  # type: ignore[attr-defined] # valid attribute
    #         → Forces the lazy object to load its actual value
    # → Calls the _setup() method that initializes _wrapped
    return obj._wrapped  # type: ignore[attr-defined] # valid attribute


# → Returns the actual value stored in the lazy object
# → Defines a function that forces a lazy object to be evaluated and returns its actual value.

# What it does:
# Checks if a LazyObject is already loaded; if not, forces it to load (_setup()), then returns the wrapped value.
