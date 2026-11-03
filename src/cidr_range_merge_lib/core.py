"""Merge adjacent and overlapping IPv4/IPv6 CIDR blocks.

The implementation uses only integer arithmetic on the network address and
prefix length.  CIDR blocks are converted to half-open integer intervals
``[start, end)`` where ``end`` is exclusive.  Merging then reduces to a
classic interval-union problem, after which each merged interval is converted
back to the minimal list of CIDR blocks that exactly cover it.

Why intervals instead of string manipulation?  String-based merging has to
special-case every prefix length and address family; integer arithmetic is
uniform and makes the adjacency rule (``a.end == b.start``) obvious.
"""

from __future__ import annotations

import ipaddress
from typing import Iterable, List, Tuple


class CIDRRangeMergeError(ValueError):
    """Base class for errors raised by this library."""


class CIDRParseError(CIDRRangeMergeError):
    """Raised when an input string is not a valid CIDR block."""


# An interval is a half-open range of integers [start, end).  ``bits`` is the
# address width (32 or 128) and is needed to reconstruct CIDR blocks.
_Interval = Tuple[int, int, int]


def _parse_cidr(text: str) -> _Interval:
    """Parse one CIDR string into ``(start, end, bits)``.

    Raises ``CIDRParseError`` for anything ``ipaddress`` rejects; we do not
    try to be more permissive than the standard library because a lax parser
    would happily accept host bits set in the network address and silently
    change the meaning of the input.
    """
    if not isinstance(text, str):
        raise CIDRParseError(f"CIDR must be a string, got {type(text).__name__}")
    try:
        net = ipaddress.ip_network(text, strict=True)
    except ValueError as exc:
        raise CIDRParseError(str(exc)) from exc
    start = int(net.network_address)
    end = start + (1 << (net.max_prefixlen - net.prefixlen))
    return start, end, net.max_prefixlen


def _merge_intervals(intervals: List[_Interval]) -> List[_Interval]:
    """Merge a list of intervals that all share the same address width.

    Adjacent intervals (``a.end == b.start``) are merged as well as
    overlapping ones, because the brief asks for the minimal covering set.
    """
    if not intervals:
        return []
    intervals.sort(key=lambda item: (item[0], item[1]))
    merged: List[_Interval] = []
    cur_start, cur_end, bits = intervals[0]
    for start, end, _ in intervals[1:]:
        if start <= cur_end:
            if end > cur_end:
                cur_end = end
        else:
            merged.append((cur_start, cur_end, bits))
            cur_start, cur_end = start, end
    merged.append((cur_start, cur_end, bits))
    return merged


def _interval_to_cidrs(start: int, end: int, bits: int) -> List[str]:
    """Cover ``[start, end)`` with the fewest possible CIDR blocks.

    The greedy algorithm takes the largest aligned block that starts at the
    current position and does not overshoot ``end``.  This is optimal for
    interval covering with power-of-two blocks: any block starting at
    ``start`` is aligned to its own size, and taking the largest possible one
    can never force more blocks later.
    """
    result: List[str] = []
    while start < end:
        # Largest block size that is aligned at ``start`` and fits in the
        # remaining range.  ``lowbit`` is the largest power of two dividing
        # ``start``; when ``start`` is zero there is no alignment constraint
        # other than the address width itself.
        if start == 0:
            max_by_alignment = 1 << bits
        else:
            max_by_alignment = start & -start
        remaining = end - start
        size = 1
        while size * 2 <= max_by_alignment and size * 2 <= remaining:
            size *= 2
        prefix = bits - size.bit_length() + 1
        network = ipaddress.ip_network((start, prefix), strict=False)
        result.append(str(network))
        start += size
    return result


def merge_cidrs(cidrs: Iterable[str]) -> List[str]:
    """Merge CIDR strings into the minimal covering set.

    IPv4 and IPv6 inputs are handled independently: the result contains the
    merged IPv4 blocks followed by the merged IPv6 blocks, each family in
    ascending network order.  Mixing families in one list is fine; the
    function never tries to merge across them because their integer ranges
    are not comparable.

    Raises ``CIDRParseError`` if any input is not a valid CIDR block.
    """
    v4: List[_Interval] = []
    v6: List[_Interval] = []
    for text in cidrs:
        start, end, bits = _parse_cidr(text)
        if bits == 32:
            v4.append((start, end, bits))
        else:
            v6.append((start, end, bits))

    merged = _merge_intervals(v4) + _merge_intervals(v6)
    out: List[str] = []
    for start, end, bits in merged:
        out.extend(_interval_to_cidrs(start, end, bits))
    return out
