"""Public surface for cidr-range-merge-lib.

Only the merge function and the two error types are exported.  Everything
else lives in :mod:`cidr_range_merge_lib.core` and is considered internal.
"""

from .core import CIDRParseError, CIDRRangeMergeError, merge_cidrs

__all__ = ["merge_cidrs", "CIDRParseError", "CIDRRangeMergeError"]
