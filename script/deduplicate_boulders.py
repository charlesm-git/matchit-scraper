"""
Script to find and merge duplicate boulders with slight name variations.
Focuses on boulders in the same crag with similar grades and similar names.
"""

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


def find_duplicate_groups(
    min_similarity: int = 85,
    grade_tolerance: int = 2,
    dry_run: bool = True,
    area_slug: str = None,
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
    with Session() as db:
        # Build query for all boulders with their crag and grade
        query = select(Boulder).options(
            joinedload(Boulder.crag),
            joinedload(Boulder.grade),
            joinedload(Boulder.ascents),
        )

        # Filter by area if specified
        if area_slug:
            query = (
                query.join(Boulder.crag)
                .join(Crag.area)
                .where(Crag.area.has(slug=area_slug))
            )

        boulders = db.scalars(query).unique().all()

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
                    similarity = fuzz.ratio(
                        boulder1.name_normalized.lower(),
                        boulder2.name_normalized.lower(),
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
):
    """
    Interactive mode: show each duplicate group and ask user to confirm merge.
    """
    duplicate_groups = find_duplicate_groups(
        min_similarity=min_similarity,
        grade_tolerance=grade_tolerance,
        dry_run=True,
        area_slug=area_slug,
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

    args = parser.parse_args()

    if args.mode == "interactive":
        interactive_merge(
            min_similarity=args.similarity,
            grade_tolerance=args.grade_tolerance,
            area_slug=args.area,
        )
    else:
        # Auto mode with higher default similarity for safety
        similarity = max(args.similarity, 90)
        auto_merge(
            min_similarity=similarity,
            grade_tolerance=args.grade_tolerance,
            area_slug=args.area,
            dry_run=not args.execute,
        )
