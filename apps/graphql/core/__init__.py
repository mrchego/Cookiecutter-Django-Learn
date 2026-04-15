import graphene
# → Imports the Graphene library for building GraphQL APIs in Python.
# What this code does:
# This defines a custom GraphQL resolver info class that extends Graphene's ResolveInfo to use the custom SaleorContext type.
from . import fields  # noqa: F401
# → Imports the fields module from the current package
# → # noqa: F401 = Suppresses flake8 warning about unused import
# → Likely registers custom GraphQL field types (e.g., JSON, DateTime, Money)
# → Even though not used directly, importing it has side effects (registers custom types)
from .context import SaleorContext

__all__ = ["SaleorContext"]
# → Defines what gets exported when someone does from module import *
# → Only SaleorContext is exposed publicly from this module

class ResolveInfo(graphene.ResolveInfo):
#     → Creates a custom resolver info class inheriting from Graphene's ResolveInfo
# → This class contains metadata about the GraphQL query execution
    context: SaleorContext
# → Type hint for the context attribute
# → Overrides the default context type with SaleorContext
# → This enables type checking and IDE autocomplete for the custom context
