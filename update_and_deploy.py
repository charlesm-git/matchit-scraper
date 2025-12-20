from datetime import datetime
import shutil
import subprocess
import sys

from config import (
    API_DIR,
    ASCENT_MATRIX_FILE,
    DB_FILE,
    GRADE_MATRIX_FILE,
    SCRAPER_DIR,
    STYLE_MATRIX_FILE,
    REMOTE_NAME,
    GIT_BRANCH,
)


def run_command(cmd, cwd=None):
    """Run a shell command and handle errors."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)


def main():
    print("=" * 60)
    print("BLEAU.INFO DATABASE UPDATE AUTOMATION")
    print("=" * 60)

    # Step 1: Run the scraper
    print("\n[1/7] Running scraper...")
    run_command("python scraper.py", cwd=SCRAPER_DIR)
    print("✓ Scraping completed")

    # Step 2: Create indexes
    print("\n[2/7] Creating database indexes...")
    run_command("python create_indexes.py", cwd=SCRAPER_DIR)
    print("✓ Indexes created")

    # Step 3: Generate ML matrices
    print("\n[3/7] Generating recommendation matrices...")
    run_command("python ml_algorithm.py", cwd=SCRAPER_DIR)
    print("✓ Recommendation matrices generated")

    # Step 4: Verify files exist
    print("\n[4/7] Verifying generated files...")
    db_path = SCRAPER_DIR / DB_FILE
    ascent_matrix_path = SCRAPER_DIR / ASCENT_MATRIX_FILE
    grade_matrix_path = SCRAPER_DIR / GRADE_MATRIX_FILE
    style_matrix_path = SCRAPER_DIR / STYLE_MATRIX_FILE

    if not db_path.exists():
        print(f"❌ Database file not found: {db_path}")
        sys.exit(1)
    if not ascent_matrix_path.exists():
        print(f"❌ Matrices file not found: {ascent_matrix_path}")
        sys.exit(1)
    if not grade_matrix_path.exists():
        print(f"❌ Matrices file not found: {grade_matrix_path}")
        sys.exit(1)
    if not style_matrix_path.exists():
        print(f"❌ Matrices file not found: {style_matrix_path}")
        sys.exit(1)

    db_size = db_path.stat().st_size / (1024 * 1024)  # MB
    ascent_matrix_size = ascent_matrix_path.stat().st_size / (1024 * 1024)
    grade_matrix_size = grade_matrix_path.stat().st_size / (1024 * 1024)
    style_matrix_size = style_matrix_path.stat().st_size / (1024 * 1024)

    print(f"✓ Database: {db_size:.2f} MB")
    print(f"✓ Ascent Matrix: {ascent_matrix_size:.2f} MB")
    print(f"✓ Grade Matrix: {grade_matrix_size:.2f} MB")
    print(f"✓ Style Matrix: {style_matrix_size:.2f} MB")

    # Step 5: Copy files to API directory
    print("\n[5/7] Copying files to API directory...")
    api_db_path = API_DIR / DB_FILE
    api_ascent_matrix_path = API_DIR / ASCENT_MATRIX_FILE
    api_grade_matrix_path = API_DIR / GRADE_MATRIX_FILE
    api_style_matrix_path = API_DIR / STYLE_MATRIX_FILE

    shutil.copy2(db_path, api_db_path)
    print(f"✓ Copied {DB_FILE} to {API_DIR}")

    shutil.copy2(ascent_matrix_path, api_ascent_matrix_path)
    print(f"✓ Copied {ASCENT_MATRIX_FILE} to {API_DIR}")

    shutil.copy2(grade_matrix_path, api_grade_matrix_path)
    print(f"✓ Copied {GRADE_MATRIX_FILE} to {API_DIR}")

    shutil.copy2(style_matrix_path, api_style_matrix_path)
    print(f"✓ Copied {STYLE_MATRIX_FILE} to {API_DIR}")

    # Step 6: Commit to API repository
    print("\n[6/7] Committing to API repository...")
    commit_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    commit_message = f"Database update - {commit_date}"

    # Git add
    run_command(
        f"git add {DB_FILE} {ASCENT_MATRIX_FILE} {GRADE_MATRIX_FILE} {STYLE_MATRIX_FILE}",
        cwd=API_DIR,
    )
    print("✓ Files staged")

    # Check if there are changes to commit
    status = run_command("git status --porcelain", cwd=API_DIR)
    if not status.strip():
        print("⚠️  No changes to commit")
        return

    # Git commit
    run_command(f'git commit -m "{commit_message}"', cwd=API_DIR)
    print(f"✓ Committed with message: '{commit_message}'")

    # Step 7: Push to GitHub
    print("\n[7/7] Pushing to GitHub...")
    run_command(f"git push {REMOTE_NAME} {GIT_BRANCH}", cwd=API_DIR)
    print("✓ Pushed to GitHub")

    print("\n" + "=" * 60)
    print("✓ AUTOMATION COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)
