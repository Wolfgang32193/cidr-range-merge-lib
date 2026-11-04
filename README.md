# cidr-range-merge-lib

Merge adjacent and overlapping IPv4/IPv6 CIDR blocks into the minimal
covering set.

```python
from cidr_range_merge_lib import merge_cidrs

merge_cidrs(["192.168.0.0/25", "192.168.0.128/25"])
# ['192.168.0.0/24']

merge_cidrs(["10.0.0.0/8", "10.1.0.0/16", "2001:db8::/33", "2001:db8:8000::/33"])
# ['10.0.0.0/8', '2001:db8::/32']
```

## Why this exists

Firewall rules, route tables and allow-lists accumulate CIDR blocks.  Two
adjacent `/25`s are one `/24`; a `/8` swallows every `/16` inside it.  The
obvious string-based merge has to special-case every prefix length and both
address families, and it is easy to get the adjacency rule wrong.  This
library converts each block to a half-open integer interval `[start, end)`
and merges intervals, then reconstructs the fewest CIDR blocks that cover
the merged range.  Integer arithmetic is uniform across IPv4 and IPv6 and
makes the adjacency condition (`a.end == b.start`) explicit.

The trade-off: the input must be a canonical network address.  Host bits
set in the network portion (`10.0.0.1/24`) are rejected with
`CIDRParseError` rather than silently masked, because silently changing the
meaning of a caller's input is worse than failing loudly.

## API

- `merge_cidrs(cidrs)` — takes an iterable of CIDR strings and returns a
  list of CIDR strings.  IPv4 and IPv6 inputs are merged independently; the
  result lists the merged IPv4 blocks first, then the merged IPv6 blocks,
  each in ascending network order.
- `CIDRParseError` — raised for any input that is not a valid CIDR block.
- `CIDRRangeMergeError` — base class for the parse error, in case callers
  want to catch every error this library raises.

## The awkward edge

Merging is family-aware.  An IPv4 block and an IPv6 block never merge,
because their integer ranges are not comparable.  If you pass both, you get
both back, each family merged on its own.  The other edge is host bits set
in the network address: `merge_cidrs(["10.0.0.1/24"])` raises
`CIDRParseError` rather than returning `10.0.0.0/24`.
