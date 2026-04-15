from django.db import models, transaction

# → Imports Django's database modules for models and transactions.
# → models = Provides base classes and fields for defining database models
# → transaction = Provides tools for database transactions (atomic operations)
import datetime

# → Imports Python's built-in datetime module for working with dates and times.
# → datetime = Module containing classes for:

# datetime.date = Dates (year, month, day)

# datetime.time = Times (hour, minute, second)

# datetime.datetime = Both date and time combined

# datetime.timedelta = Time differences/durations

# datetime.timezone = Time zone handling
# Create your models here.
from collections.abc import Iterable

# → Imports the Iterable abstract base class from Python's collections module.
# → from collections.abc = Imports from Abstract Base Classes for container types
# → import Iterable = Brings in the Iterable type for type checking and isinstance() checks
# → Used to check if an object can be looped over (has __iter__() method)
# → Example: isinstance(my_list, Iterable) returns True for lists, tuples, strings, etc.
from typing import Any, TypeVar

# → Imports type hinting utilities from Python's typing module.

# → Any = Special type that matches any Python value (disables type checking)
# → TypeVar = Creates a generic type variable for reusable type hints
# Generic means writing code that works with any data type while still keeping type safety.
from django.contrib.postgres.indexes import GinIndex, PostgresIndex

# → Imports PostgreSQL-specific database index classes for Django models.

# → GinIndex = Generalized Inverted Index - optimized for:

# Full-text search

# Array fields

# JSON fields

# Multiple columns together

# → PostgresIndex = Base class for all PostgreSQL-specific indexes
from django.core.files.base import ContentFile

# → Imports ContentFile class from Django's file handling system.
# → ContentFile = Creates a file-like object from string or bytes content (without actual file on disk)
# Purpose: Lets you create files in memory and save them to model fields without having actual files on disk.
from django.db.models import F, JSONField, Max, Q

# → F = References a model field value in queries (avoids race conditions)
# → JSONField = Field type for storing JSON data in database
# → Max = Aggregation function to get maximum value
# → Q = Complex lookups with OR/AND conditions
from django.utils.crypto import get_random_string

# → Imports a utility function for generating secure random strings.
from storages.utils import safe_join

#  Securely combines paths by preventing ../ attacks where users try to access files outside intended directories.
from . import EventDeliveryStatus, JobStatus, private_storage

# → Imports local modules/objects from the current package (relative import).
# → from . = Import from the same directory (current package)
# → import EventDeliveryStatus = Imports the EventDeliveryStatus class/constants
# → import JobStatus = Imports the JobStatus class/constants
# → import private_storage = Imports the private_storage instance
# Purpose: Brings in related constants and utilities from the same module folder for:
# Event status tracking
# Job processing status
# Private file storage handling
from .utils.json_serializer import CustomJsonEncoder


class SortableModel(models.Model):
    sort_order = models.IntegerField(editable=False, db_index=True, null=True)

    #     → Defines an abstract model that adds sorting capability to any model.
    # → sort_order = Integer field storing the order position (null if not sorted)
    # → editable=False = Not shown in forms (managed automatically)
    # → db_index=True = Indexed for faster ordering queries
    class Meta:
        abstract = True

    # → Makes this an abstract model (not created in database, only inherited)
    def get_ordering_queryset(self):
        raise NotImplementedError("Unknown ordering queryset")

    # → Abstract method that child classes must implement
    # → Should return queryset of objects that should be ordered together
    # → Example: For categories, return all categories under same parent
    @staticmethod
    def get_max_sort_order(qs):
        existing_max = qs.aggregate(Max("sort_order"))
        existing_max = existing_max.get("sort_order__max")
        return existing_max

    #     → Static method to find highest sort order in a queryset
    # → aggregate(Max("sort_order")) = Get maximum value
    # → Returns None if no objects exist

    def save(self, *args, **kwargs):
        if self.pk is None:
            qs = self.get_ordering_queryset()
            existing_max = self.get_max_sort_order(qs)
            self.sort_order = 0 if existing_max is None else existing_max + 1
        super().save(*args, **kwargs)

    #         → Overrides save method to set sort_order for new objects:
    # → if self.pk is None = Only for new objects (not updates)
    # → Gets ordering queryset and finds max sort_order
    # → Sets new object's sort_order to max+1 (or 0 if none exist)
    # → Then calls parent save
    @transaction.atomic
    def delete(self, *args, **kwargs):
        if self.sort_order is not None:
            qs = self.get_ordering_queryset()
            qs.filter(sort_order__gt=self.sort_order).update(
                sort_order=F("sort_order") - 1
            )
        super().delete(*args, **kwargs)


# → Overrides delete to reorder remaining items:
# → @transaction.atomic = All-or-nothing database operation
# → If object had a sort_order:
# → Gets ordering queryset
# → Decreases sort_order by 1 for all items after deleted one
# → Example: Delete item 3 → items 4,5 become 3,4
# → Then calls parent delete

T = TypeVar("T", bound="PublishableModel")
# → Creates a generic type variable for use with PublishableModel
# → T = Type placeholder
# → bound="PublishableModel" = T must be or inherit from PublishableModel

# Purpose: Provides automatic sorting functionality for any model that inherits from it.


class PublishedQuerySet(models.QuerySet[T]):
    #     → Defines a custom QuerySet class that adds publishing-related methods.
    # → models.QuerySet[T] = Inherits from Django's QuerySet with generic type T
    # → [T] = Generic type for the model this queryset works with
    def published(self):
        today = datetime.datetime.now(tz=datetime.UTC)
        return self.filter(
            Q(published_at__lte=today) | Q(published_at__isnull=True),
            is_published=True,
        )


#     → Adds a published() method to filter only published items:
# → today = datetime.datetime.now(tz=datetime.UTC) = Current UTC time
# → Q(published_at__lte=today) = Published date is in the past or now
# → | Q(published_at__isnull=True) = OR no publication date set (always published)
# → is_published=True = Must be marked as published
# → Returns filtered queryset of published items only

PublishableManager = models.Manager.from_queryset(PublishedQuerySet)
# → Creates a custom manager class from the custom queryset.
# → models.Manager.from_queryset() = Django utility that creates a Manager class with all queryset methods
# → PublishableManager = New manager class that includes:

# All default manager methods (all(), filter(), etc.)

# Plus the custom published() method from PublishedQuerySet

# Purpose: Provides a reusable way to filter published content across models:


class PublishableModel(models.Model):
    published_at = models.DateTimeField(blank=True, null=True)
    is_published = models.BooleanField(default=False)
    # → Defines an abstract model that adds publishing functionality to any model.
    # → published_at = When the item becomes visible (null = immediately)
    # → is_published = Whether the item is marked as published
    objects: Any = PublishableManager()

    # → Sets the default manager to the custom PublishableManager
    # → : Any = Type hint (skips type checking)
    # → PublishableManager() = Manager that adds .published() method
    class Meta:
        abstract = True

    # → Makes this an abstract model (not created in database, only inherited)
    @property
    def is_visible(self):
        return self.is_published and (
            self.published_at is None
            or self.published_at <= datetime.datetime.now(tz=datetime.UTC)
        )


#     → Property that checks if item should be visible to users:
# → self.is_published = Must be marked as published
# → self.published_at is None = OR no publish date set (visible immediately)
# → self.published_at <= now() = OR publish date has passed
# → Returns True if both conditions met

# Purpose: Reusable publishing logic for any model (articles, products, events)


class ModelWithMetadata(models.Model):
    private_metadata = JSONField(
        blank=True, db_default={}, default=dict, encoder=CustomJsonEncoder
    )
    metadata = JSONField(
        blank=True, db_default={}, default=dict, encoder=CustomJsonEncoder
    )

    # → Defines an abstract model that adds flexible metadata storage to any model.
    # → metadata = Public metadata (visible to everyone)
    # → private_metadata = Private metadata (internal use only)
    # → JSONField = Stores JSON data in database
    # → default=dict = Default empty dict {}
    # → encoder=CustomJsonEncoder = Handles special types like Money, Weight
    class Meta:
        indexes: list[PostgresIndex] = [
            GinIndex(fields=["private_metadata"], name="%(class)s_p_meta_idx"),
            GinIndex(fields=["metadata"], name="%(class)s_meta_idx"),
        ]
        abstract = True

    # → Adds PostgreSQL GIN indexes for faster JSON field queries
    # → %(class)s = Replaced with actual class name (e.g., "product_meta_idx")
    def get_value_from_private_metadata(self, key: str, default: Any = None) -> Any:
        return self.private_metadata.get(key, default)

    # → Retrieves a value from private metadata by key
    # → Returns default if key doesn't exist
    def store_value_in_private_metadata(self, items: dict):
        if not self.private_metadata:
            self.private_metadata = {}
        self.private_metadata.update(items)

    # → Stores multiple key-value pairs in private metadata
    # → Initializes as dict if empty
    def clear_private_metadata(self):
        self.private_metadata = {}

    # → Removes all private metadata
    def delete_value_from_private_metadata(self, key: str) -> bool:
        if key in self.private_metadata:
            del self.private_metadata[key]
            return True
        return False

    # → Deletes a specific key from private metadata
    # → Returns True if deleted, False if key didn't exist
    def get_value_from_metadata(self, key: str, default: Any = None) -> Any:
        return self.metadata.get(key, default)

    # → Retrieves a value from public metadata
    def store_value_in_metadata(self, items: dict):
        if not self.metadata:
            self.metadata = {}
        self.metadata.update(items)

    # → Stores multiple key-value pairs in public metadata
    def clear_metadata(self):
        self.metadata = {}

    # → Removes all public metadata
    def delete_value_from_metadata(self, key: str):
        if key in self.metadata:
            del self.metadata[key]


# → Deletes a specific key from public metadata

# Purpose: Adds flexible key-value storage to any model without changing database schema:


class ModelWithExternalReference(models.Model):
    external_reference = models.CharField(
        max_length=250,
        unique=True,
        blank=True,
        null=True,
        db_index=True,
    )

    # → Defines an abstract model that adds a field for storing external system references.
    # → external_reference = String field storing ID/reference from external system
    # → max_length=250 = Maximum 250 characters
    # → unique=True = No two records can have same external reference
    # → blank=True = Can be empty in forms
    # → null=True = Can be NULL in database
    # → db_index=True = Indexed for faster lookups by external reference
    class Meta:
        abstract = True


# → Makes this an abstract model (not created in database, only inherited)
# → Makes this an abstract model (not created in database, only inherited)

# Purpose: Provides a standardized way to link Django models with records in external systems:

# ERP systems

# Legacy databases

# Third-party APIs

# External services


class Job(models.Model):
    status = models.CharField(
        max_length=50, choices=JobStatus.CHOICES, default=JobStatus.PENDING
    )
    #     → Defines an abstract model for tracking background jobs/tasks.
    # → status = Current state of the job (pending, success, failed, deleted)
    # → max_length=50 = Status string up to 50 chars
    # → choices=JobStatus.CHOICES = Restricts to predefined status values
    # → default=JobStatus.PENDING = New jobs start as "pending"
    message = models.CharField(max_length=255, blank=True, null=True)
    #     → Stores result message or error details
    # → max_length=255 = Message up to 255 chars
    # → blank=True = Can be empty in forms
    # → null=True = Can be NULL in database
    created_at = models.DateTimeField(auto_now_add=True)
    #     → Timestamp when job was created
    # → auto_now_add=True = Automatically set on creation only
    updated_at = models.DateTimeField(auto_now=True)

    # → Timestamp when job was last updated
    # → auto_now=True = Automatically updates on every save
    class Meta:
        abstract = True


# → Makes this an abstract model (not created in database, only inherited)


# Purpose: Provides reusable job tracking for background tasks:

# Export generation

# Email sending

# Data processing

# Report generation

# What is a Payload?
# Payload is the actual data/content being transmitted in a message or request, excluding metadata/headers.

# Simple Analogy:
# Think of sending a package:

# Envelope/Box = HTTP request/response

# Address/Labels = Headers/metadata


# The actual item inside = PAYLOAD
class EventPayloadManager(models.Manager["EventPayload"]):
    #     → Defines a custom manager for EventPayload model with generic type.
    # → models.Manager = Inherits from Django's default manager
    # → ["EventPayload"] = Generic type specifying this manager works with EventPayload model
    @transaction.atomic
    def create_with_payload_file(self, payload: str) -> "EventPayload":
        obj = super().create()
        obj.save_payload_file(payload)
        return obj

    # → Creates a new EventPayload with associated payload file in a transaction.
    # → @transaction.atomic = All database operations succeed or fail together
    # → super().create() = Creates empty EventPayload object
    # → obj.save_payload_file(payload) = Saves payload data to file storage
    # → Returns the created object
    @transaction.atomic
    def bulk_create_with_payload_files(
        self, objs: Iterable["EventPayload"], payloads=Iterable[str]
    ) -> list["EventPayload"]:
        #         → Creates multiple EventPayload objects with their payload files efficiently.
        # → objs = Collection of EventPayload instances (without files yet)
        # → payloads = Collection of payload strings to save
        # → Returns list of created objects
        created_objs = self.bulk_create(objs)
        # → Creates all objects in one database query (much faster than individual creates)
        for obj, payload_data in zip(created_objs, payloads, strict=False):
            obj.save_payload_file(payload_data, save_instance=False)
        #             → Loops through created objects and their payloads together
        # → zip(created_objs, payloads) = Pairs each object with its payload
        # → Saves each payload to file storage without saving instance yet
        # → save_instance=False = Don't save to database now (will bulk update later)
        self.bulk_update(created_objs, ["payload_file"])
        #         → Updates all objects in one database query with their file paths
        # → Only updates the payload_file field
        return created_objs


#     → Returns the list of created objects

# Purpose: Efficiently creates EventPayload records with associated file storage, using bulk operations for performance.


class EventPayload(models.Model):
    PAYLOADS_DIR = "payloads"
    # → Defines a model for storing event payloads (data from webhooks, events, etc.).
    # → PAYLOADS_DIR = Directory name where payload files are stored
    payload = models.TextField(default="")
    #     → Stores small payload data directly in database (for small payloads)
    # → TextField = Unlimited text length
    payload_file = models.FileField(
        storage=private_storage, upload_to=PAYLOADS_DIR, null=True
    )
    #     → Stores large payload data as files on disk (better for large payloads)
    # → storage=private_storage = Uses private storage (not publicly accessible)
    # → upload_to=PAYLOADS_DIR = Saves files in "payloads" directory
    # → null=True = Can be null (if payload stored in text field instead)
    created_at = models.DateTimeField(auto_now_add=True)
    # → Timestamp when payload was created
    objects = EventPayloadManager()
    # → Uses custom manager with bulk creation methods

    # TODO (PE-568): change typing of return payload to `bytes` to avoid unnecessary decoding.
    def get_payload(self):
        if self.payload_file:
            with self.payload_file.open("rb") as f:
                payload_data = f.read()
                return payload_data.decode("utf-8")
        return self.payload

    # → Retrieves payload data regardless of where it's stored:
    # → If file exists: Reads file, decodes from UTF-8, returns string
    # → If no file: Returns payload from text field
    # → TODO note suggests future improvement to return bytes directly
    def save_payload_file(self, payload_data: str, save_instance=True):
        payload_bytes = payload_data.encode("utf-8")
        prefix = get_random_string(length=12)
        file_name = f"{self.pk}.json"
        file_path = safe_join(prefix, file_name)
        self.payload_file.save(
            file_path, ContentFile(payload_bytes), save=save_instance
        )

    # → Saves payload data to file storage:
    # → payload_data.encode("utf-8") = Converts string to bytes
    # → get_random_string(12) = Creates random folder name for security
    # → f"{self.pk}.json" = Filename uses model's primary key
    # → safe_join() = Safely combines path components
    # → self.payload_file.save() = Saves file to storage
    # → save=save_instance = Controls whether to save model instance
    def save_as_file(self):
        payload_data = self.payload
        self.payload = ""
        self.save()
        self.save_payload_file(payload_data)


# → Moves payload from text field to file storage:
# → Saves current payload to variable
# → Clears text field (now empty)
# → Saves model (updates database)
# → Saves payload as file

# Purpose: Flexible event payload storage that can handle both small and large payloads efficiently:

# Small payloads → stored directly in database (faster access)

# Large payloads → stored as files (better performance)

# Can migrate from text to file as needed


class EventDelivery(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    #     → Records when the event delivery was created/queued.
    # → auto_now_add=True = Automatically set timestamp on creation
    status = models.CharField(
        max_length=255,
        choices=EventDeliveryStatus.CHOICES,
        default=EventDeliveryStatus.PENDING,
    )
    #     → Tracks the delivery status of this event.
    # → choices = Limited to predefined statuses (pending, success, failed)
    # → default = New deliveries start as "pending"
    event_type = models.CharField(max_length=255)
    # → Stores what kind of event this is (e.g., "order_created", "product_updated")
    payload = models.ForeignKey(
        EventPayload, related_name="deliveries", null=True, on_delete=models.CASCADE
    )
    #     → Links to the actual event data (payload).
    # → ForeignKey = Many deliveries can share same payload (e.g., retry attempts)
    # → related_name="deliveries" = Allows payload.deliveries.all() to get all deliveries
    # → null=True = Can be null (if payload deleted)
    # → on_delete=models.CASCADE = If payload deleted, delete this delivery too
    webhook = models.ForeignKey("webhook.Webhook", on_delete=models.CASCADE)

    # → Links to the webhook configuration that should receive this event.
    # → "webhook.Webhook" = String reference (avoids circular import)
    # → on_delete=models.CASCADE = If webhook deleted, delete its deliveries
    class Meta:
        ordering = ("-created_at",)


# → Default ordering: newest deliveries first (descending by created_at)

# Purpose: Tracks individual attempts to deliver webhook events:


class EventDeliveryAttempt(models.Model):
    delivery = models.ForeignKey(
        EventDelivery, related_name="attempts", null=True, on_delete=models.CASCADE
    )
    #     → Links this attempt to a specific event delivery.
    # → ForeignKey = Many attempts can belong to one delivery
    # → related_name="attempts" = Allows delivery.attempts.all() to get all attempts
    # → null=True = Can be null (if delivery deleted)
    # → on_delete=models.CASCADE = If delivery deleted, delete its attempts
    created_at = models.DateTimeField(auto_now_add=True)
    # → Timestamp when this attempt was made
    task_id = models.CharField(max_length=255, null=True)
    # → ID of background task that handled this attempt (for debugging)
    duration = models.FloatField(null=True)
    # → How long the attempt took (in seconds)
    response = models.TextField(null=True)
    # → Response body received from webhook endpoint
    response_headers = models.TextField(null=True)
    # → Response headers received from webhook endpoint
    response_status_code = models.PositiveSmallIntegerField(null=True)
    # → HTTP status code from webhook endpoint (200, 404, 500, etc.)
    request_headers = models.TextField(null=True)
    # → Headers sent in the request (for debugging)
    status = models.CharField(
        max_length=255,
        choices=EventDeliveryStatus.CHOICES,
        default=EventDeliveryStatus.PENDING,
    )

    # → Status of this specific attempt (pending, success, failed)
    class Meta:
        ordering = ("-created_at",)


# → Default ordering: newest attempts first

# Purpose: Records detailed information about each attempt to deliver a webhook:


# Why was apps/core/models.py created?

# It was created to:

# Avoid repeating logic across apps
# Provide reusable base models
# Standardize behavior across the system
# Support complex features (webhooks, metadata, jobs)
# Make the project scalable and maintainable
