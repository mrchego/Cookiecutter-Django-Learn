from django.core.serializers.json import DjangoJSONEncoder

# → Imports Django's custom JSON encoder for handling Django-specific data types.

# → DjangoJSONEncoder = Extended JSON encoder that handles:

# datetime / date / time → ISO format strings

# decimal.Decimal → strings (preserves precision)

# uuid.UUID → strings

# Promise (lazy translation) → strings

# Purpose: Converts Django model data to JSON without losing information:
from django.core.serializers.json import Serializer as JsonSerializer

# → Imports Django's JSON serializer class and aliases it as JsonSerializer.
# → Serializer = Django's built-in serializer that converts model instances to JSON
# → as JsonSerializer = Creates alias "JsonSerializer" for easier use/understanding

# Purpose: Converts Django model querysets to JSON format:
from measurement.measures import Weight

# → Imports the Weight measurement class from the measurement library, which provides unit-aware objects for handling weight values and conversions.
# → This library is inspired by Django's django.contrib.gis.measure module and extends it to support additional measurement types.
from prices import Money

# → Imports the Money class from the prices library, which provides a robust way to handle monetary values with proper currency support.


MONEY_TYPE = "Money"


class Serializer(JsonSerializer):
    #     → Defines a custom serializer class that inherits from Django's built-in JsonSerializer.
    # → Serializer = Custom class name
    # → (JsonSerializer) = Inherits all functionality from Django's JSON serializer
    def _init_options(self):
        #         → Overrides the internal initialization method (private method with underscore)
        # → Runs when serializer is being set up
        super()._init_options()  # type: ignore[misc] # private method
        #         → Calls the parent class's initialization first (keeps original functionality)
        # → super() = Reference to parent JsonSerializer class
        # → # type: ignore[misc] = Tells type checker to ignore any errors (since it's a private method)
        self.json_kwargs["cls"] = CustomJsonEncoder


class CustomJsonEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Money):
            return {"_type": MONEY_TYPE, "amount": obj.amount, "currency": obj.currency}
        #         → If object is a Money instance (from prices library):
        # → Returns a dictionary with:
        # → _type: MONEY_TYPE = Marker identifying this as money data
        # → amount: obj.amount = The numeric value
        # → currency: obj.currency = Currency code (USD, EUR, etc.)
        # Mirror implementation of django_measurement.MeasurementField.value_to_string
        if isinstance(obj, Weight):
            return f"{obj.value}:{obj.unit}"
        #         → If object is a Weight instance (from measurement library):
        # → Returns string in format "value:unit" (e.g., "135:lb" or "61.23:kg")
        # → Matches how django_measurement field stores data
        return super().default(obj)


# → For any other object type, call parent's default method:
# → Parent (DjangoJSONEncoder) handles dates, decimals, UUIDs, etc.
# → If parent can't handle it, will raise TypeError

# Purpose: Enables JSON serialization of Money and Weight objects that aren't natively JSON-serializable.


#     → Defines a custom JSON encoder that extends Django's built-in JSON encoder.
# → CustomJsonEncoder = Class name
# → (DjangoJSONEncoder) = Inherits all Django JSON encoding functionality
# → Overrides the default method that handles objects not normally JSON-serializable
# → Called when encoder encounters an object it doesn't know how to serialize

#         → Modifies the JSON encoder to use custom encoder:
# → self.json_kwargs = Dictionary of arguments passed to json.dumps()
# → "cls" = The encoder class argument
# → CustomJsonEncoder = Your custom encoder that handles special types (dates, decimals, etc.)

# Purpose: Creates a serializer that uses CustomJsonEncoder instead of default, allowing proper serialization of Django-specific data types.


# ✔ Why was json_serializer.py created?

# To:

# Provide a single, consistent, extensible way to convert complex Django data into JSON

# ✔ What problem does it solve?

# JSON can’t handle Money, Weight, etc.

# avoids duplication across apps

# ensures consistent API/webhook output

# centralizes serialization logic

# ✔ Why in core/utils?

# Because:

# It’s a shared infrastructure tool used by the entire system
