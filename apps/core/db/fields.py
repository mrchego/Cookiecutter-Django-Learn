from collections.abc import Callable

# → Imports the Callable type from collections.abc for type hints indicating callable objects (functions, methods, etc.).
from decimal import Decimal

# → Imports Python's Decimal type for high-precision decimal arithmetic (better than float for monetary values).
from functools import total_ordering

# → Imports a decorator that automatically generates comparison methods (__lt__, __le__, __gt__, __ge__) if you define __eq__ and one other comparison (like __lt__).
import orjson

# → Imports the orjson library - a fast, JSON library that's significantly faster than Python's built-in json module.
from django.core import validators

#  Imports Django's built-in validators for fields (email, URL, slug, etc.).
from django.db.models import Field, JSONField

# → Imports Django's base Field class and the JSONField for storing JSON data in PostgreSQL.
from django.db.models.expressions import Expression

# → Imports Expression for creating database expressions (e.g., F('field') + 1).
from prices import Money, TaxedMoney

# → Imports Money (monetary value with currency) and TaxedMoney (money with tax) from the prices library for e-commerce applications.


class SanitizedJSONField(JSONField):
    description = "A JSON field that runs a given sanitization method "
    "before saving into the database."
    # → Defines a custom Django JSON field that automatically sanitizes data before saving to the database.

    # What it does:
    # Extends Django's JSONField to apply a sanitizer function to JSON data before it's stored, ensuring data cleanliness, security, and consistency.
    def __init__(self, *args, sanitizer: Callable[[dict], dict], **kwargs):
        #         → Constructor that accepts a sanitizer function
        # → sanitizer: Callable[[dict], dict] = Function that takes a dict and returns a sanitized dict
        # → The sanitizer is the key customization for this field
        super().__init__(*args, **kwargs)
        # → Calls parent JSONField constructor with all other arguments
        self._sanitizer_method = sanitizer
        # → Stores the sanitizer function for later use

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["sanitizer"] = self._sanitizer_method
        return name, path, args, kwargs

    #     → Used by Django's migrations system to serialize the field
    # → Adds the sanitizer function to the migration's kwargs
    # → Allows migrations to recreate the field with the correct sanitizer

    def get_db_prep_save(self, value: dict, connection):
        #         → Overrides the method that prepares values for database storage
        # → Called when saving a model instance
        """Sanitize the value for saving using the passed sanitizer."""
        if isinstance(value, Expression):
            return value
        #         → If value is a database expression (like F('field')), pass through without sanitizing
        # → Allows database expressions to work (e.g., F('json_field__key'))
        return orjson.dumps(
            self._sanitizer_method(value), option=orjson.OPT_UTC_Z
        ).decode("utf-8")


#     → Calls the sanitizer on the value
# → Converts to JSON using orjson (fast JSON library)
# → orjson.OPT_UTC_Z = Output UTC timestamps with 'Z' suffix
# → Decodes bytes to UTF-8 string for database storage


@total_ordering
class NonDatabaseFieldBase:
    """Base class for all fields that are not stored in the database."""

    # → Defines a base class for fields that exist only in Python code, not in the database. The @total_ordering decorator automatically generates comparison methods.
    # What it does:
    # Provides a foundation for creating Django-like fields that don't map to database columns. These fields exist only on model instances for logic, computed values, or UI purposes.
    empty_values = list(validators.EMPTY_VALUES)
    # → Defines what values are considered "empty" (None, '', [], etc.)
    # → Used for validation and form handling
    # Field flags
    auto_created = False  # Not auto-created by Django
    blank = True  # Can be blank in forms
    concrete = False  # Not a database column
    editable = False  # Not editable in admin/forms
    generated = True  # Value is generated, not stored
    unique = False  # Not a unique constraint
    # → These flags tell Django how to treat this field
    is_relation = False  # Not a foreign key/relationship
    remote_field = None  # No related model

    many_to_many = None  # Not many-to-many
    many_to_one = None  # Not many-to-one
    one_to_many = None  # Not one-to-many
    one_to_one = None  # Not one-to-one

    # → Indicates this field doesn't represent database relationships
    def __init__(self):
        self.column = None  # No database column
        self.primary_key = False  # Not a primary key

        self.creation_counter = Field.creation_counter
        Field.creation_counter += 1

    #         → Sets up field with a creation counter for ordering fields
    # → Counter ensures fields are processed in the order they're defined

    # What are __eq__, __lt__, and __hash__?
    # These are Python magic methods (dunder methods) that define how objects behave with operators and built-in functions.

    # 1. __eq__ - Equality Comparison
    # What it does:
    # Defines how objects compare with == (equality operator).
    #     __lt__ - Less Than Comparison
    # What it does:
    # Defines how objects compare with < (less than operator).
    #     3. __hash__ - Hash Value
    # What it does:
    # Returns a unique integer hash for the object, used in dictionaries and sets.
    def __eq__(self, other):
        if isinstance(other, Field | NonDatabaseFieldBase):
            return self.creation_counter == other.creation_counter
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, Field | NonDatabaseFieldBase):
            return self.creation_counter < other.creation_counter
        return NotImplemented

    # → Allow comparison based on creation order
    # → Works with both Django Field and NonDatabaseFieldBase
    def __hash__(self):
        return hash(self.creation_counter)

    def contribute_to_class(self, cls, name, **kwargs):
        self.attname = self.name = name
        self.model = cls
        cls._meta.add_field(self, private=True)
        setattr(cls, name, self)

    #         → Called when field is added to a model class
    # → Registers field with model's metadata
    # → Makes field accessible as a class attribute

    def clean(self, value, model_instance):
        # Shortcircut clean() because Django calls it on all fields with
        # is_relation = False
        return value


#     → Override Django's clean method (does nothing, just returns value)
# → Prevents Django from trying to validate non-database fields
# Why Non-Database Fields Are Useful:
# Use Case	Example
# Computed values	Total price, full name, age from birthdate
# UI helpers	Confirmation password, terms acceptance
# Caching	Expensive calculations that should persist on instance
# Virtual relations	Access related objects without FK
# Form fields	Fields that exist only in forms, not DB


class MoneyField(NonDatabaseFieldBase):
    #     → Defines a virtual field that combines two separate database fields (amount and currency) into a single Money object.

    # What it does:
    # Acts as a descriptor that transparently combines two database columns (amount and currency) into a single Money object, making it easier to work with monetary values.

    description = (
        "A field that combines an amount of money and currency code into Money"
        "It allows to store prices with different currencies in one database."
    )

    def __init__(
        self,
        amount_field="price_amount",
        currency_field="price_currency",
        verbose_name=None,
        **kwargs,
    ):
        #         What is a Constructor?
        # A constructor is a special method that automatically runs when you create a new instance of a class. It initializes the object's attributes and sets up its initial state.
        #         → Constructor that takes names of the actual database fields
        # → Default field names: price_amount and price_currency
        super().__init__(**kwargs)
        # → Calls parent NonDatabaseFieldBase initializer
        self.amount_field = amount_field
        self.currency_field = currency_field
        # Stores the names of the real database fields that store the amount and currency
        self.verbose_name = verbose_name

    #         What is verbose_name?
    # verbose_name is a human-readable name for a field or model, used in Django's admin interface, forms, and error messages instead of the technical field name.

    # Simple Explanation:
    # Technical name: price_amount (database column)

    # Verbose name: "Price Amount" (what users see)

    def __str__(self):
        return f"MoneyField(amount_field={self.amount_field}, currency_field={self.currency_field})"

    # String representation for debugging

    def __get__(self, instance, cls=None):
        if instance is None:
            return self

        amount = getattr(instance, self.amount_field)
        currency = getattr(instance, self.currency_field)
        if amount is not None and currency is not None:
            return Money(amount, currency)
        return self.get_default()

    #     → Called when accessing the field on a model instance
    # → Retrieves amount and currency from actual database fields
    # → Combines them into a Money object
    # → Returns default if values are None

    def __set__(self, instance, value):
        #         What is a Descriptor?
        # A descriptor is a Python object that defines how attribute access works. It's like a controller that intercepts getting, setting, and deleting attributes on other objects.

        # Simple Analogy:
        # Think of a descriptor as a security guard at a building entrance:

        # When you try to get something (__get__), the guard checks who you are and what you're taking

        # When you try to put something in (__set__), the guard validates it and puts it in the right place

        # When you try to remove something (__delete__), the guard makes sure it's safe to remove
        # print(f"self = {self}")      # The descriptor object
        #         print(f"instance = {instance}")  # The object being modified
        #         print(f"value = {value}")    # The value being assigned
        amount = None
        currency = None
        if value is not None:
            amount = value.amount
            currency = value.currency
        setattr(instance, self.amount_field, amount)
        setattr(instance, self.currency_field, currency)

    #         → Called when assigning a value to the field
    # → Extracts amount and currency from Money object
    # → Stores them in the separate database fields

    def get_default(self):
        default_currency = None
        default_amount = Decimal(0)
        if hasattr(self, "model"):
            default_currency = self.model._meta.get_field(
                self.currency_field
            ).get_default()
            default_amount = self.model._meta.get_field(self.amount_field).get_default()

        if default_amount is None:
            return None
        return Money(default_amount, default_currency)


#     → Gets default values from the underlying fields
# → Returns a Money object with default amount and currency


class TaxedMoneyField(NonDatabaseFieldBase):
    description = "A field that combines net and gross fields values into TaxedMoney."
    # → Defines a virtual field that combines three database fields (net amount, gross amount, and currency) into a single TaxedMoney object.

    # What it does:
    # Acts as a descriptor that transparently combines three separate database columns into a single TaxedMoney object, which represents a monetary value with tax breakdown.

    #         TaxedMoney Explained:
    # TaxedMoney represents a price with tax included:

    # net amount: Price without tax (excl. tax)

    # gross amount: Price with tax (incl. tax)

    # currency: Currency code (USD, EUR, etc.)

    # Example: A product with 20% tax:

    # Net: $100.00 (before tax)

    # Gross: $120.00 (after tax)

    def __init__(
        self,
        net_amount_field="price_amount_net",
        gross_amount_field="price_amount_gross",
        currency_field="currency",
        verbose_name=None,
        **kwargs,
    ):
        # → Constructor that takes names of the three database fields
        # → Default names: price_amount_net, price_amount_gross, currency
        super().__init__(**kwargs)
        self.net_amount_field = net_amount_field
        self.gross_amount_field = gross_amount_field
        self.currency_field = currency_field
        self.verbose_name = verbose_name

    def __str__(self):
        return f"TaxedMoneyField(net_amount_field={self.net_amount_field}, gross_amount_field={self.gross_amount_field}, currency_field={self.currency_field})"

    def __get__(self, instance, cls=None):
        if instance is None:
            return self
        net_amount = getattr(instance, self.net_amount_field)
        gross_amount = getattr(instance, self.gross_amount_field)
        currency = getattr(instance, self.currency_field)
        if net_amount is None or gross_amount is None:
            return None
        return TaxedMoney(Money(net_amount, currency), Money(gross_amount, currency))

    # → Called when reading product.price
    # → Retrieves net, gross, and currency from database fields
    # → Combines them into a single TaxedMoney object
    # → Returns None if any component is missing
    def __set__(self, instance, value):
        net_amount = None
        gross_amount = None
        currency = None
        if value is not None:
            net_amount = value.net.amount
            gross_amount = value.gross.amount
            currency = value.currency
        setattr(instance, self.net_amount_field, net_amount)
        setattr(instance, self.gross_amount_field, gross_amount)
        setattr(instance, self.currency_field, currency)


# → Called when assigning product.price = TaxedMoney(...)
# → Extracts net amount, gross amount, and currency from the TaxedMoney object
# → Stores each component in its respective database field
