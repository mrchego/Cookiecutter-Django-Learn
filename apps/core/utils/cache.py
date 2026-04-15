import collections

# → Imports Python's collections module, which provides specialized container datatypes.
# What it does:
# The collections module provides alternatives to built-in containers like list, dict, set, and tuple with additional functionality.


class CacheDict(collections.OrderedDict):
    #     → Defines a custom dictionary that acts as an LRU (Least Recently Used) Cache, automatically removing the least recently accessed items when capacity is exceeded.

    # What it does:
    # Implements a cache that keeps track of access order and automatically evicts the oldest items when it gets too full.
    def __init__(self, capacity: int):
        self.capacity = capacity
        super().__init__()

    #         → Constructor that sets the maximum number of items the cache can hold
    # → Stores capacity as instance variable
    # → Calls parent OrderedDict constructor

    def __getitem__(self, key):
        value = super().__getitem__(key)
        super().move_to_end(key)
        return value

    #     → Overrides dictionary lookup:

    # Retrieves the value (same as normal dict)

    # move_to_end(key) moves this key to the end of the order

    # Returns the value
    # → Effect: Recently accessed items become "fresh" (move to end)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        super().move_to_end(key)
        #         → Overrides dictionary assignment:

        # Stores the key-value pair

        # Moves the key to the end (marks as most recent)

        while len(self) > self.capacity:
            surplus = next(iter(self))
            super().__delitem__(surplus)


#             → After adding, check if cache exceeds capacity
# → next(iter(self)) gets the first (oldest) key
# → Delete that oldest key
# → Repeat until under capacity


# Aspect	Description
# Purpose	Implements LRU (Least Recently Used) cache
# Mechanism	Uses OrderedDict to track access order
# Eviction	Removes oldest items when capacity exceeded
# Use cases	Query caching, API response caching, view caching
# Benefits	Automatic memory management, keeps most relevant data
# Key Concept: This CacheDict class implements the classic LRU (Least Recently Used) caching algorithm. It automatically manages memory by removing the least recently accessed items when capacity is exceeded. In Django applications, this is useful for caching expensive operations like database queries, API calls, or computed results where you want to limit memory usage while keeping the most relevant data accessible.
