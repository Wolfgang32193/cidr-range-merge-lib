import unittest

from cidr_range_merge_lib import CIDRParseError, merge_cidrs


class MergeCidrsTests(unittest.TestCase):
    def test_single_block_is_returned_unchanged(self):
        self.assertEqual(merge_cidrs(["10.0.0.0/8"]), ["10.0.0.0/8"])

    def test_empty_input_returns_empty_list(self):
        self.assertEqual(merge_cidrs([]), [])

    def test_adjacent_blocks_merge(self):
        self.assertEqual(
            merge_cidrs(["192.168.0.0/25", "192.168.0.128/25"]),
            ["192.168.0.0/24"],
        )

    def test_overlapping_blocks_merge(self):
        self.assertEqual(
            merge_cidrs(["10.0.0.0/8", "10.1.0.0/16"]),
            ["10.0.0.0/8"],
        )

    def test_disjoint_blocks_stay_separate(self):
        self.assertEqual(
            merge_cidrs(["10.0.0.0/8", "192.168.0.0/16"]),
            ["10.0.0.0/8", "192.168.0.0/16"],
        )

    def test_unsorted_input_is_sorted(self):
        self.assertEqual(
            merge_cidrs(["192.168.0.0/24", "10.0.0.0/8"]),
            ["10.0.0.0/8", "192.168.0.0/24"],
        )

    def test_three_blocks_collapse_to_one(self):
        self.assertEqual(
            merge_cidrs(
                ["10.0.0.0/26", "10.0.0.64/26", "10.0.0.128/25"]
            ),
            ["10.0.0.0/24"],
        )

    def test_merge_does_not_overshoot(self):
        # Two /25s that are adjacent but do not form a /24 because the
        # enclosing /24 also contains 192.168.0.0/25.
        self.assertEqual(
            merge_cidrs(["192.168.0.128/25", "192.168.1.0/25"]),
            ["192.168.0.128/25", "192.168.1.0/25"],
        )

    def test_ipv6_adjacent_blocks_merge(self):
        self.assertEqual(
            merge_cidrs(["2001:db8::/33", "2001:db8:8000::/33"]),
            ["2001:db8::/32"],
        )

    def test_ipv4_and_ipv6_are_kept_separate(self):
        self.assertEqual(
            merge_cidrs(["2001:db8::/32", "10.0.0.0/8"]),
            ["10.0.0.0/8", "2001:db8::/32"],
        )

    def test_ipv6_host_route_merges_with_network(self):
        self.assertEqual(
            merge_cidrs(["2001:db8::/128", "2001:db8::1/128"]),
            ["2001:db8::/127"],
        )

    def test_full_ipv4_space_is_one_block(self):
        self.assertEqual(
            merge_cidrs(["0.0.0.0/1", "128.0.0.0/1"]),
            ["0.0.0.0/0"],
        )

    def test_invalid_cidr_raises_parse_error(self):
        with self.assertRaises(CIDRParseError):
            merge_cidrs(["not-a-cidr"])

    def test_host_bits_set_raise_parse_error(self):
        with self.assertRaises(CIDRParseError):
            merge_cidrs(["10.0.0.1/24"])

    def test_non_string_input_raises_parse_error(self):
        with self.assertRaises(CIDRParseError):
            merge_cidrs([123])  # type: ignore[list-item]

    def test_duplicate_blocks_merge_to_one(self):
        self.assertEqual(
            merge_cidrs(["10.0.0.0/8", "10.0.0.0/8"]),
            ["10.0.0.0/8"],
        )


if __name__ == "__main__":
    unittest.main()
