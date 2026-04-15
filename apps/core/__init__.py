from django.conf import settings

# → Imports Django's settings module to access configuration values.
# → from django.conf = Imports from Django's configuration package
# → import settings = Brings in the settings object containing all Django project settings
# → Allows access to variables like settings.DATABASES, settings.INSTALLED_APPS, settings.SECRET_KEY, etc.
from django.core.files.storage import Storage

# → Imports the base Storage class from Django's file storage system.
# → from django.core.files.storage = Imports from Django's file handling module
# → import Storage = Brings in the abstract base class for creating custom storage backends
# → Used when you want to create your own storage system (like custom cloud storage) by subclassing Storage
from django.utils.functional import LazyObject

# → Imports LazyObject utility from Django for lazy initialization.
# → from django.utils.functional = Imports from Django's functional utilities module
# → import LazyObject = Brings in a base class that delays object creation until first access
# → Used for optimizing performance by creating expensive objects only when needed (e.g., storage backends, caches)
from django.utils.module_loading import import_string

# → Imports a utility function for dynamically importing Python modules by string path.
# → from django.utils.module_loading = Imports from Django's module loading utilities
# → import import_string = Function that imports a module or attribute using a dot path string
# → Example: import_string('django.core.files.storage.FileSystemStorage') imports the FileSystemStorage class


# What are Constants?
# Constants are variables whose value never changes throughout your program.


class JobStatus:
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    DELETED = "deleted"
    # → Defines a class with constants for job status values.
    # → PENDING = "pending" = Job is waiting to be processed
    # → SUCCESS = "success" = Job completed successfully
    # → FAILED = "failed" = Job encountered an error
    # → DELETED = "deleted" = Job was removed
    CHOICES = [
        (PENDING, "Pending"),
        (SUCCESS, "Success"),
        (FAILED, "Failed"),
        (DELETED, "Deleted"),
    ]


#     → Creates a list of tuples for Django model field choices.
# → First value = stored in database (e.g., "pending")
# → Second value = human-readable label for forms/admin (e.g., "Pending")
# → Used in model fields like status = models.CharField(choices=JobStatus.CHOICES)


class TimePeriodType:
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"

    CHOICES = [(DAY, "Day"), (WEEK, "Week"), (MONTH, "Month"), (YEAR, "Year")]


class EventDeliveryStatus:
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"

    CHOICES = [
        (PENDING, "Pending"),
        (SUCCESS, "Success"),
        (FAILED, "Failed"),
    ]


def _get_private_storage_class(import_path=None):
    return import_string(import_path or settings.PRIVATE_FILE_STORAGE)


# → Defines a helper function that gets the private storage class dynamically.
# → _get_private_storage_class = Function name (underscore means "internal use only")
# → import_path=None = Optional parameter: specific storage class path

# → import_path or settings.PRIVATE_FILE_STORAGE = Uses provided path OR falls back to Django setting
# → settings.PRIVATE_FILE_STORAGE = String from settings.py like "myapp.storage.PrivateStorage"

# → import_string(...) = Converts string path into actual Python class
# → return = Returns the storage class (not an instance, the class itself)


# Purpose: Allows flexible configuration of which storage backend to use for private files.
class PrivateStorage(LazyObject):
    def _setup(self):
        self._wrapped = _get_private_storage_class()()


# → Defines a lazy-loading private storage class.
# → class PrivateStorage(LazyObject): = Creates class that inherits from Django's LazyObject
# → LazyObject = Delays actual object creation until first use (saves memory/performance)

# → def _setup(self): = Required LazyObject method that creates the real object
# → _get_private_storage_class() = Gets the storage class (from settings or import_path)
# → () = Calls the class to create an instance
# → self._wrapped = = Stores the real storage instance inside the lazy wrapper

# Purpose: Creates a private storage object only when first accessed, not at startup.

private_storage: Storage = PrivateStorage()  # type: ignore
# → Creates a global instance of the private storage with type hint.
# → private_storage: = Variable name for the storage instance
# → : Storage = Type hint indicating this is a Django Storage object
# → = PrivateStorage() = Creates instance of the lazy PrivateStorage class
# → When first used, PrivateStorage() will initialize the actual storage backend

# Purpose: A ready-to-use storage instance for handling private files throughout the Django application.

# ------------------------------WHY THIS FILE WAS MADE------------------------------

# In Python, a file named: __init__.py turns a folder into a Python package. Because of this file, Python can import things like: from apps.core import private_storage Without __init__.py, Python would not treat core as an importable module. it Make apps/core an importable Python package.

# __init__.py solves three architecture problems.
# Problem 1 — Avoid Code Duplication
# status = models.CharField(
#     choices=[("pending","Pending"),("success","Success")]
# )
# You define it once:
# class JobStatus:
# Then reuse everywhere.

# Problem 2 — Centralize Infrastructure
# Things like file storage should not belong to a single app.
# You create:  core/private_storage One global system.

# Problem 3 — Lazy Loading Expensive Services
# class PrivateStorage(LazyObject)
# solves a performance problem.

# Without lazy loading:
# Django startup
# → connect storage
# → configure backend
# → load drivers
# Even if storage is never used.

# Lazy loading means:
# Startup → fast
# First storage usage → initialize backend
# This is a major performance pattern in Django internals.

# Why Put This Inside __init__.py
# Because the project wants a simple import path.
# Instead of:
# from apps.core.storage.private import private_storage
# You can do:
# from apps.core import private_storage
# __init__.py acts as a public API for the package. This is called: package interface design
