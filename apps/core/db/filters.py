from django.db.models.lookups import IContains

# → Imports Django's IContains lookup class, which implements the icontains lookup for case-insensitive containment.

# What it does:
# IContains is Django's built-in lookup that generates SQL like: UPPER(field) LIKE UPPER('%value%')


class PostgresILike(IContains):
    #     → Inherits from Django's built-in IContains lookup
    # → Overrides the PostgreSQL-specific behavior
    lookup_name = "ilike"
    #     → Defines the name of this lookup (used in querysets)
    # → This will be registered as ilike lookup

    def as_postgresql(self, compiler, connection):
        #         → Method that generates PostgreSQL-specific SQL
        # → Called when using PostgreSQL database backend
        lhs, lhs_params = self.process_lhs(compiler, connection)
        #         → Processes the left-hand side (the field being searched)
        # → Example: name becomes "products"."name"
        # → Returns SQL string and parameters
        # Left-hand side WHERE to search
        rhs, rhs_params = self.process_rhs(compiler, connection)
        #         → Processes the right-hand side (the value to search for)
        # → Example: 'laptop' becomes '%laptop%' (adds wildcards)
        # → Returns SQL string and parameters
        # Right-hand side WHAT to search
        params = lhs_params + rhs_params  # type: ignore[operator]
        # → Combines parameters from both sides
        return f"{lhs} ILIKE {rhs}", params


# → Returns PostgreSQL's native ILIKE operator (case-insensitive LIKE)
# → ILIKE is PostgreSQL's case-insensitive version of LIKE
