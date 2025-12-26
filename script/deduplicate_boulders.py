"""
Script to find and merge duplicate boulders with slight name variations.
Focuses on boulders in the same crag with similar grades and similar names.

Usage:
    python deduplicate_boulders.py [options]

Arguments:
    --mode {interactive,auto}
        Interactive: asks for confirmation for each group
        Auto: merges all groups automatically
        Default: interactive

    --similarity INT
        Minimum similarity score (0-100) for names to be duplicates
        Default: 85 (interactive), 95 (auto)

    --grade-tolerance INT
        Maximum grade correspondence difference to consider duplicates
        Default: 2

    --area SLUG
        Limit search to specific area (e.g., 'ticino', 'rocklands')
        Default: all areas

    --execute
        Apply changes (auto mode only, interactive always prompts)
        Default: dry-run

Examples:
    python deduplicate_boulders.py --mode interactive --area ticino
    python deduplicate_boulders.py --mode auto --similarity 95 --execute
"""

import re
import sys
from pathlib import Path

# Add parent directory to path to import project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from collections import defaultdict
from typing import List, Tuple
from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database import Session
from models.boulder import Boulder
from models.crag import Crag


# Variation keywords that indicate different versions of the same problem
VARIATION_KEYWORDS = {
    "sit",
    "stand",
    "left",
    "right",
    "direct",
    "extension",
}


def is_likely_variation(name1: str, name2: str) -> bool:
    """
    Check if two boulder names are likely variations rather than duplicates.
    E.g., "Problem X" and "Problem X sit" or "Problem X (sit)" should not be considered duplicates.
    But "Problem X sit" and "Problem X (sit)" or duplicate entries should still be compared.
    """
    name1_lower = name1.lower()
    name2_lower = name2.lower()

    # Remove parentheses and their contents for comparison, but check if keywords are inside
    # Extract text in parentheses
    paren_pattern = r"\(([^)]+)\)"
    paren_1 = set(re.findall(paren_pattern, name1_lower))
    paren_2 = set(re.findall(paren_pattern, name2_lower))

    # Get all variation keywords from both names (in parentheses or not)
    keywords_in_name1 = set()
    keywords_in_name2 = set()

    # Extract keywords from parentheses
    for paren_text in paren_1:
        paren_words = set(paren_text.split())
        keywords_in_name1.update(paren_words & VARIATION_KEYWORDS)

    for paren_text in paren_2:
        paren_words = set(paren_text.split())
        keywords_in_name2.update(paren_words & VARIATION_KEYWORDS)

    # Check words in the main text
    words1 = set(name1_lower.split())
    words2 = set(name2_lower.split())

    keywords_in_name1.update(words1 & VARIATION_KEYWORDS)
    keywords_in_name2.update(words2 & VARIATION_KEYWORDS)

    # If both have the same variation keywords (or both have none), they're potential duplicates
    # If they have different variation keywords, they're different variations
    if keywords_in_name1 != keywords_in_name2:
        return True

    return False


def calculate_similarity(
    name1: str, name2: str, algorithm: str = "ratio"
) -> float:
    """
    Calculate similarity between two names using specified algorithm.

    Args:
        name1: First name
        name2: Second name
        algorithm: One of 'ratio', 'partial_ratio', 'token_sort', 'token_set'

    Returns:
        Similarity score (0-100)
    """
    if algorithm == "ratio":
        return fuzz.ratio(name1, name2)
    elif algorithm == "partial_ratio":
        return fuzz.partial_ratio(name1, name2)
    elif algorithm == "token_sort":
        return fuzz.token_sort_ratio(name1, name2)
    elif algorithm == "token_set":
        return fuzz.token_set_ratio(name1, name2)
    else:
        return fuzz.ratio(name1, name2)


def fetch_boulders_for_duplicate_check(area_slug: str = None) -> List[Boulder]:
    """Fetch boulders from the database for duplicate checking."""
    with Session() as db:
        query = (
            select(Boulder)
            .options(
                joinedload(Boulder.crag),
                joinedload(Boulder.grade),
                joinedload(Boulder.ascents),
            )
            .where(Boulder.ascents.any())
        )  # Only boulders with ascents

        # Filter by area if specified
        if area_slug:
            query = (
                query.join(Boulder.crag)
                .join(Crag.area)
                .where(Crag.area.has(slug=area_slug))
            )

        boulders = db.scalars(query).unique().all()
        return boulders


def find_duplicate_groups(
    min_similarity: int = 85,
    grade_tolerance: int = 2,
    dry_run: bool = True,
    area_slug: str = None,
    algorithm: str = "ratio",
) -> List[List[Boulder]]:
    """
    Find groups of potentially duplicate boulders.

    Args:
        min_similarity: Minimum similarity score (0-100) for names to be considered duplicates
        grade_tolerance: Max grade value difference to consider boulders as potential duplicates
        dry_run: If True, only show what would be merged without making changes
        area_slug: Optional area slug to limit search to specific area

    Returns:
        List of boulder groups that are likely duplicates
    """
    boulders = fetch_boulders_for_duplicate_check(area_slug=area_slug)

    print(f"Analyzing {len(boulders)} boulders for duplicates...")

    # Group boulders by crag
    boulders_by_crag = defaultdict(list)
    for boulder in boulders:
        boulders_by_crag[boulder.crag_id].append(boulder)

    duplicate_groups = []

    # Check each crag for duplicates
    for crag_id, crag_boulders in boulders_by_crag.items():
        if len(crag_boulders) < 2:
            continue

        # Sort by grade for efficient comparison
        crag_boulders.sort(key=lambda b: b.grade.correspondence)

        # Track which boulders have already been grouped
        processed = set()

        for i, boulder1 in enumerate(crag_boulders):
            if boulder1.id in processed:
                continue

            # Start a new potential duplicate group
            group = [boulder1]

            # Compare with remaining boulders in similar grade range
            for boulder2 in crag_boulders[i + 1 :]:
                if boulder2.id in processed:
                    continue

                # Check if grades are close enough
                grade_diff = abs(
                    boulder1.grade.correspondence
                    - boulder2.grade.correspondence
                )
                if grade_diff > grade_tolerance:
                    # Since sorted, no point checking further
                    if (
                        boulder2.grade.correspondence
                        > boulder1.grade.correspondence + grade_tolerance
                    ):
                        break
                    continue

                # Calculate name similarity
                similarity = calculate_similarity(
                    boulder1.name_normalized.lower(),
                    boulder2.name_normalized.lower(),
                    algorithm=algorithm,
                )

                if similarity >= min_similarity:
                    group.append(boulder2)
                    processed.add(boulder2.id)

            # If we found duplicates, add the group
            if len(group) > 1:
                duplicate_groups.append(group)
                processed.add(boulder1.id)

    return duplicate_groups


def display_duplicate_group(group: List[Boulder], group_num: int):
    """Display information about a duplicate group."""
    print(f"\n{'='*80}")
    print(f"Duplicate Group #{group_num}")
    print(f"{'='*80}")

    for idx, boulder in enumerate(group, 1):
        ascent_count = len(boulder.ascents)
        print(f"\n  [{idx}] Boulder ID: {boulder.id}")
        print(f"      Name: {boulder.name}")
        print(f"      Grade: {boulder.grade.value}")
        print(f"      Crag: {boulder.crag.name}")
        print(f"      Ascents: {ascent_count}")
        print(f"      URL: {boulder.url}")


def merge_boulder_group(
    db, group: List[Boulder], dry_run: bool = True
) -> Tuple[Boulder, List[Boulder]]:
    """
    Merge a group of duplicate boulders.
    Moves all ascents to the boulder with the most ascents. Keeps all boulders.

    Returns:
        Tuple of (target_boulder, source_boulders)
    """
    # Sort by ascent count (descending) to get the boulder with most ascents
    group_with_counts = [(boulder, len(boulder.ascents)) for boulder in group]
    group_with_counts.sort(key=lambda x: x[1], reverse=True)

    target_boulder = group_with_counts[0][0]
    duplicates = [b for b, _ in group_with_counts[1:]]

    print(
        f"\n  Target boulder (keeping): {target_boulder.name} (ID: {target_boulder.id})"
    )
    print(f"  With {len(target_boulder.ascents)} ascents")
    print(f"\n  Merging from {len(duplicates)} duplicate(s):")

    total_moved = 0
    for duplicate in duplicates:
        ascent_count = len(duplicate.ascents)
        print(
            f"    - {duplicate.name} (ID: {duplicate.id}): {ascent_count} ascents"
        )

        if not dry_run:
            # Move all ascents to target boulder
            for ascent in duplicate.ascents:
                ascent.boulder_id = target_boulder.id
                db.add(ascent)

            total_moved += ascent_count

    if not dry_run:
        db.commit()
        print(
            f"\n  ✓ Merged {total_moved} ascents from {len(duplicates)} duplicate boulder(s)"
        )
        print(f"  Note: Duplicate boulders kept for potential re-scraping")
    else:
        print(
            f"\n  [DRY RUN] Would merge {sum(len(d.ascents) for d in duplicates)} ascents"
        )

    return target_boulder, duplicates


def interactive_merge(
    min_similarity: int = 85,
    grade_tolerance: int = 2,
    area_slug: str = None,
    algorithm: str = "ratio",
):
    """
    Interactive mode: show each duplicate group and ask user to confirm merge.
    """
    duplicate_groups = find_duplicate_groups(
        min_similarity=min_similarity,
        grade_tolerance=grade_tolerance,
        dry_run=True,
        area_slug=area_slug,
        algorithm=algorithm,
    )

    if not duplicate_groups:
        print("\n✓ No duplicate groups found!")
        return

    print(f"\nFound {len(duplicate_groups)} potential duplicate group(s)")

    with Session() as db:
        for group_num, group in enumerate(duplicate_groups, 1):
            display_duplicate_group(group, group_num)

            # Ask for confirmation
            response = (
                input("\n  Merge this group? (y/n/q to quit): ")
                .strip()
                .lower()
            )

            if response == "q":
                print("\nQuitting...")
                break
            elif response == "y":
                merge_boulder_group(db, group, dry_run=False)
            else:
                print("  Skipped.")

    print("\n✓ Done!")


def auto_merge(
    min_similarity: int = 95,
    grade_tolerance: int = 1,
    algorithm: str = "ratio",
    area_slug: str = None,
    dry_run: bool = True,
):
    """
    Automatic mode: merge all groups with high confidence (higher similarity threshold).
    """
    duplicate_groups = find_duplicate_groups(
        min_similarity=min_similarity,
        grade_tolerance=grade_tolerance,
        dry_run=True,
        area_slug=area_slug,
        algorithm=algorithm,
    )

    if not duplicate_groups:
        print("\n✓ No duplicate groups found!")
        return

    print(f"\nFound {len(duplicate_groups)} duplicate group(s)")

    if dry_run:
        print("\n[DRY RUN MODE - No changes will be made]")

    with Session() as db:
        for group_num, group in enumerate(duplicate_groups, 1):
            display_duplicate_group(group, group_num)
            merge_boulder_group(db, group, dry_run=dry_run)

    if dry_run:
        print("\n[DRY RUN] Run with --execute to apply changes")
    else:
        print("\n✓ All duplicates merged!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Find and merge duplicate boulders with similar names"
    )
    parser.add_argument(
        "--mode",
        choices=["interactive", "auto"],
        default="interactive",
        help="Interactive mode asks for confirmation, auto mode merges all",
    )
    parser.add_argument(
        "--similarity",
        type=int,
        default=85,
        help="Minimum similarity score (0-100) to consider names as duplicates (default: 85)",
    )
    parser.add_argument(
        "--grade-tolerance",
        type=int,
        default=2,
        help="Maximum grade value difference to consider boulders as duplicates (default: 2)",
    )
    parser.add_argument(
        "--area",
        type=str,
        help="Limit search to specific area slug (e.g., 'ticino')",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute changes (default is dry-run)",
    )
    parser.add_argument(
        "--algorithm",
        choices=["ratio", "partial_ratio", "token_sort", "token_set"],
        default="ratio",
        help="Similarity algorithm: ratio (default, strict), partial_ratio (substring), token_sort (word order), token_set (word sets)",
    )

    args = parser.parse_args()

    if args.mode == "interactive":
        interactive_merge(
            min_similarity=args.similarity,
            grade_tolerance=args.grade_tolerance,
            area_slug=args.area,
            algorithm=args.algorithm,
        )
    else:
        # Auto mode with higher default similarity for safety
        similarity = args.similarity if args.similarity else 95
        auto_merge(
            min_similarity=similarity,
            grade_tolerance=args.grade_tolerance,
            area_slug=args.area,
            dry_run=not args.execute,
            algorithm=args.algorithm,
        )
