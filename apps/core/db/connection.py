import logging

# → Imports Python's built-in logging module for recording events, errors, and debug information from your application.

# What it does:
# Provides a flexible framework for generating log messages with different severity levels, which can be directed to various outputs (console, files, external services).
import traceback

# → Imports Python's traceback module for working with exception stack traces, providing detailed information about where and how errors occurred.
# What it does:
# The traceback module allows you to extract, format, and print stack traces of exceptions, helping you understand the execution path that led to an error.
from contextlib import contextmanager

# → Imports the contextmanager decorator from Python's contextlib module, which allows you to create context managers using generator functions.
# What it does:
# contextmanager turns a generator function into a context manager that can be used with the with statement, simplifying resource management and setup/teardown patterns.
from django.conf import settings

# → Imports the Django settings object, which provides access to all project configuration values defined in settings.py.
# What it does:
# settings is a lazy-loaded object that contains all the configuration variables for your Django project, combining defaults from Django itself with your custom settings.
from django.core.management.color import color_style

# → Imports the color_style function from Django's management color module, which provides colored terminal output for management commands.
# What it does:
# color_style() returns an object with methods that produce ANSI color codes for styling terminal text in Django management commands.
from django.db import connections

# → Imports the connections object from Django's database module, which manages all database connections for the Django project.
# What it does:
# connections is a dictionary-like object that provides access to all configured database connections defined in settings.DATABASES.
from django.db.backends.base.base import BaseDatabaseWrapper

from apps.graphql.core.context import SaleorContext, get_database_connection_name

# → Imports the base class for database wrappers in Django, which defines the interface that all database backends must implement.
# What it does:
# BaseDatabaseWrapper is the abstract base class that defines the standard API for database connections in Django. Every database backend (PostgreSQL, MySQL, SQLite, etc.) implements its own wrapper that inherits from this class.
logger = logging.getLogger(__name__)
# → Creates a logger instance named after the current Python module for logging messages.

# What it does:
# logging.getLogger(__name__) returns a logger object with the name of the current module, allowing you to log messages with proper context about where the log came from.
# → Gets or creates a logger with the specified name
# → If logger doesn't exist, creates a new one
# → If it exists, returns the existing logger
#  Python special variable that contains the current module's name
# → Example values:

# "myapp.views" when in myapp/views.py

# "myapp.models" when in myapp/models.py

# "__main__" when script is run directly
# → Stores the logger instance in a module-level variable
# → Convention is to call it logger (lowercase)
writer = settings.DATABASE_CONNECTION_DEFAULT_NAME
replica = settings.DATABASE_CONNECTION_REPLICA_NAME
# → Assigns database connection names from Django settings to local variables for easier access.

# What it does:
# Extracts the names of database connections (master/writer and read replica) from Django settings and stores them in convenient local variables.


TRACEBACK_LIMIT = 20
# → Defines a constant that limits how many lines of traceback (error stack trace) to display when an error occurs.

# What it does:
# Sets the maximum number of stack frames to show in error tracebacks, preventing excessively long tracebacks from overwhelming logs or user interfaces.


UNSAFE_WRITER_ACCESS_MSG = (
    "Unsafe access to the writer DB detected. Call `using()` on the `QuerySet` "
    "to utilize a replica DB, or employ the `allow_writer` context manager to "
    "explicitly permit access to the writer."
)
# → Defines a constant error message for when code attempts to use the writer (master) database when it should be using a read replica.
# What it does:
# This message is displayed when the system detects that a database query is trying to use the master/writer database for a read operation that could be served by a read replica.


class UnsafeWriterAccessError(Exception):
    pass


# → Defines a custom exception class for when code attempts unsafe access to the writer (master) database.

# What it does:
# Creates a specific exception type that can be raised when the system detects that a read operation is trying to use the writer database instead of a read replica.


@contextmanager
def allow_writer():
    """Context manager that allows write access to the default database connection.

    This context manager works in conjunction with the `restrict_writer_middleware` and
    `log_writer_usage_middleware` middlewares. If any of these middlewares are enabled,
    use the `allow_writer` context manager to allow write access to the default
    database. Otherwise an error will be raised or a log message will be emitted.
    """
    # → Defines a context manager that temporarily permits write operations to the master database, overriding safety restrictions.

    # What it does:
    # Creates a context where database write operations are explicitly allowed, even when write restrictions are normally enforced (like in read-only replicas).
    default_connection = connections[settings.DATABASE_CONNECTION_DEFAULT_NAME]
    # → Gets the default/master database connection object
    # → Used to track whether writer access is currently allowed
    # Check if we are already in an allow_writer block. If so we don't need to do
    # anything and we don't have to close access to the writer at the end.
    in_allow_writer_block = getattr(default_connection, "_allow_writer", False)
    #     → Checks if we're already inside an allow_writer() block
    # → _allow_writer = Custom flag stored on the connection object
    # → Defaults to False if flag doesn't exist
    if not in_allow_writer_block:
        setattr(default_connection, "_allow_writer", True)
    #         → If we're not already in a writer block:
    # → Set the flag to True to allow writer access
    try:
        yield
    #          Executes the code inside the with block
    # → Any database operations here are allowed to use the writer
    finally:
        if not in_allow_writer_block:
            # Close writer access when exiting the outermost allow_writer block.
            setattr(default_connection, "_allow_writer", False)


#             → Always runs when exiting the context
# → If this was the outer-most block, reset flag to False
# → This restores normal restrictions


@contextmanager
def allow_writer_for_default_connection(connection_name: str):
    """Context manager that allows write access when connection points to writer.

    This is a helper context manager that conditionally allows write access based on the
    given connection name.
    """
    #     → Defines a context manager that conditionally allows write access only when the connection being used is the default/writer database.

    # What it does:
    # A helper wrapper around allow_writer() that only activates writer permissions if the specified connection is actually the master database. If it's a replica connection, it does nothing.
    if connection_name == settings.DATABASE_CONNECTION_DEFAULT_NAME:
        #         → Checks if the database connection being used is the master/writer database
        # → DATABASE_CONNECTION_DEFAULT_NAME = usually 'default' (the writer)
        with allow_writer():
            yield
    #             → If using writer database, enter the allow_writer() context
    # → Temporarily permits write operations
    # → Executes the code inside the with block
    else:
        yield


#         → If using replica database, just execute the code without any writer permission
# → No need to allow writer access since replica can't write anyway


@contextmanager
def allow_writer_in_context(context: SaleorContext):
    #     → Defines a context manager that enables writer access based on the database connection stored in a SaleorContext object.

    # What it does:
    # A convenience wrapper that extracts the database connection name from a SaleorContext and then uses allow_writer_for_default_connection() to conditionally allow writer access.

    """Context manager that allows write access to the default database connection in a context (SaleorContext).

    This is a helper context manager that conditionally allows write access based on the
    database connection name in the given context.
    """
    conn_name = get_database_connection_name(context)
    #     → Gets the database connection name from the SaleorContext
    # → This determines whether we're using writer ('default') or replica ('replica')
    # → Uses the context's allow_replica flag to decide
    with allow_writer_for_default_connection(conn_name):
        yield


#         → Calls the helper that conditionally enables writer permissions
# → If conn_name is the writer ('default'), writer access is allowed
# → If conn_name is the replica, writer access is NOT allowed


def restrict_writer_middleware(get_response):
    """Middleware that restricts write access to the default database connection.

    This middleware will raise an error if a write operation is attempted on the default
    database connection. To allow writes, use the `allow_writer` context manager. Make
    sure that writer is not used accidentally and always use the `using` queryset method
    with proper database connection name.
    """

    # → Django middleware factory function
    # → Takes get_response (next middleware or view) as parameter
    def middleware(request):
        # → Inner middleware function that processes each request
        with connections[writer].execute_wrapper(restrict_writer):
            #             → Wraps the writer database connection with the restrict_writer wrapper
            # → Intercepts all SQL queries sent to the writer database
            # → writer = master database connection name (from earlier constant)
            with connections[replica].execute_wrapper(restrict_writer):
                #                 → Wraps the replica database connection with the same wrapper
                # → Prevents accidental writes on replica as well (which would fail anyway)
                return get_response(request)

    #             → Process the request through the rest of the middleware stack
    # → All database queries go through the wrapped connections

    return middleware


# → Defines a Django middleware that prevents accidental write operations on the master database unless explicitly allowed.

# What it does:
# Wraps database execution to intercept and block any write operations (INSERT, UPDATE, DELETE) on the master/writer database unless the code is running inside an allow_writer() context.


def restrict_writer(execute, sql, params, many, context):
    #     → Defines a wrapper function that intercepts database queries and blocks unsafe write operations on the writer database.

    # What it does:
    # Checks every SQL query before execution. If the query is targeting the writer database and writer access hasn't been explicitly allowed, it raises an error instead of executing the query.
    conn: BaseDatabaseWrapper = context["connection"]
    #     → Gets the database connection object from the context
    # → BaseDatabaseWrapper = Django's base database connection class
    # → context["connection"] contains the connection being used for this query
    allow_writer = getattr(conn, "_allow_writer", False)
    #     → Checks if writer access is currently allowed on this connection
    # → _allow_writer = Custom flag set by allow_writer() context manager
    # → Returns False if the flag doesn't exist (not in a writer block)
    if conn.alias == writer and not allow_writer:
        #          Two conditions must be true to block:

        # conn.alias == writer = This query is going to the writer/master database

        # not allow_writer = Writer access hasn't been explicitly allowed
        raise UnsafeWriterAccessError(f"{UNSAFE_WRITER_ACCESS_MSG} SQL: {sql}")
    #     → If both conditions are true, raise an error with:

    # Standard error message from UNSAFE_WRITER_ACCESS_MSG

    # The actual SQL query that was attempted
    return execute(sql, params, many, context)


# → If conditions don't trigger blocking, execute the original query
# → Passes through all parameters unchanged


def log_writer_usage_middleware(get_response):
    """Middleware that logs write access to the default database connection.

    This is similar to the `restrict_writer_middleware` middleware, but instead of
    raising an error, it logs a message when a write operation is attempted on the
    default database connection.
    """
    # → Defines a Django middleware that logs write operations on the master database without blocking them.

    # What it does:
    # Similar to restrict_writer_middleware, but instead of raising errors, it logs warnings when write operations occur on the writer database, allowing writes to proceed while still providing visibility.
    def middleware(request):
        # → Inner middleware function that processes each request
        with connections[writer].execute_wrapper(log_writer_usage):
            #             → Wraps ONLY the writer database connection (not the replica)
            # → Every query to the writer DB goes through log_writer_usage wrapper
            # → Replica DB remains unwrapped (no logging for reads)
            return get_response(request)

    #         → Process the request through the rest of the middleware stack
    # → Writer queries are logged, but not blocked

    return middleware


def log_writer_usage(execute, sql, params, many, context):
    #     → Defines a wrapper function that logs, but does not block, unsafe write operations on the writer database.

    # What it does:
    # Intercepts every query to the writer database, checks if it's an unsafe write (outside allow_writer() context), and logs detailed information including the SQL and stack trace without blocking the operation.
    conn: BaseDatabaseWrapper = context["connection"]
    #     → Gets the database connection object from the execution context
    # → Contains information about which database this query is targeting
    allow_writer = getattr(conn, "_allow_writer", False)
    #     → Checks if writer access is explicitly allowed (via allow_writer() context)
    # → Defaults to False if flag doesn't exist
    if conn.alias == writer and not allow_writer:
        #         → Triggers logging when:

        # Query targets the writer/master database

        # Writer access hasn't been explicitly allowed
        stack_trace = traceback.extract_stack(limit=TRACEBACK_LIMIT)
        #         → Captures the call stack to show where the query originated
        # → TRACEBACK_LIMIT = 20 (previously defined) limits to 20 frames
        # → extract_stack() gets stack frames without raising an exception
        error_msg = color_style().NOTICE(UNSAFE_WRITER_ACCESS_MSG)
        #         → Adds colored formatting to the error message
        # → color_style().NOTICE() makes it stand out in terminal output
        log_msg = (
            f"{error_msg} SQL: {sql} \n"
            f"Traceback: \n{''.join(traceback.format_list(stack_trace))}"
        )
        #         → Builds comprehensive log message containing:

        # The error message (colored)

        # The SQL query that was executed

        # Full stack trace showing where the query came from
        logger.warning(log_msg)
        # → Logs at WARNING level (not ERROR, since operation still proceeds)
    return execute(sql, params, many, context)


# → Always executes the query, regardless of whether it was logged
# → Unlike restrict_writer, this doesn't block operations
