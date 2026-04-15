from django.db.models import QuerySet

# → Imports Django's QuerySet class for type hinting.

# What it does:
# Defines a generator function that efficiently splits a queryset into batches using primary key ordering, avoiding performance issues with large datasets.


def queryset_in_batches(queryset: QuerySet, batch_size: int):
    #     → Takes a queryset and batch size, yields batches of primary keys
    # → Uses type hint to indicate this works with Django querysets
    """Slice a queryset into batches."""
    start_pk = 0
    # → Initializes the starting point for the next batch
    # → Starts at 0 because primary keys are typically positive integers
    while True:
        # → Infinite loop that breaks when no more records found
        qs = queryset.filter(pk__gt=start_pk).order_by("pk")[:batch_size]
        #         → Gets next batch of records:

        # filter(pk__gt=start_pk) = Only records with PK greater than last batch's max

        # order_by("pk") = Ensures consistent ordering

        # [:batch_size] = Limits to batch size
        pks = list(qs.values_list("pk", flat=True))
        # → Extracts just the primary keys from the batch
        # → flat=True returns a list of values instead of tuples
        if not pks:
            break
        # → If no keys returned, we've processed all records
        # → Exit the loop
        yield pks
        # → Returns the batch of primary keys to the caller
        # → Generator yields one batch at a time
        start_pk = pks[-1]


#         → Updates start_pk to the last primary key in current batch
# → Next iteration will get records after this PK
# Summary:
# Aspect	Description
# Purpose	Efficiently iterate through large querysets in batches
# Method	Keyset pagination using primary key ordering
# Returns	Generator yielding batches of primary keys
# Use cases	Bulk updates, data exports, migrations, cleanup jobs
# Advantages	Constant time per batch, memory efficient, handles large datasets
# Key Concept: This function implements keyset pagination (also known as "seek method") which is significantly more efficient than traditional offset pagination for large datasets. Instead of using LIMIT offset, batch_size (which requires scanning all previous rows), it uses WHERE pk > last_pk to directly jump to the next batch. This is essential for processing millions of records in Django applications without performance degradation.
