import os
import pathlib
import datetime
import subprocess

SOURCE_DIR = pathlib.Path('wiki')
DEST_DIR = pathlib.Path('public/handbook')

def get_last_commit_author():
    """Get the last commit author's name using git."""
    try:
        author = subprocess.check_output(
            ['git', 'log', '-1', '--pretty=%an'], 
            stderr=subprocess.PIPE
        ).decode('utf-8').strip()
        return author
    except subprocess.CalledProcessError as e:
        print(f"Error getting last commit author: {e}")
        return "Anonymous"  # Fallback if git command fails

def get_footer():
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    author = get_last_commit_author()
    return f"\n---\nLast Updated: {now}\nAuthor: {author}\n"

def clean_content(content, for_player=False):
    if not for_player:
        return content
    output = []
    inside_player_block = False
    has_player_content = False

    for line in content.splitlines():
        if '<!-- PLAYER -->' in line:
            inside_player_block = True
            has_player_content = True
            continue
        elif line.strip().startswith('<!--') and '-->' in line:
            inside_player_block = False
            continue
        if inside_player_block:
            output.append(line)

    return '\n'.join(output), has_player_content

def update_file(path, content):
    lines = content.rstrip().splitlines()
    if len(lines) >= 3 and lines[-3] == "---" and lines[-2].startswith("Last Updated:"):
        lines = lines[:-3]
    updated_content = "\n".join(lines).rstrip() + get_footer()
    with open(path, 'w', encoding='utf-8') as f:
        f.write(updated_content)

def remove_orphan_files(generated_files):
    """Remove files in DEST_DIR that no longer exist in SOURCE_DIR."""
    for file in DEST_DIR.rglob('*.md'):
        relative_path = file.relative_to(DEST_DIR)
        source_file = SOURCE_DIR / relative_path
        if not source_file.exists():  # File has been removed from source
            print(f"Removing orphaned file: {file}")
            file.unlink()

def handle_placeholder():
    """Handle .placeholder creation or deletion."""
    placeholder = DEST_DIR / '.placeholder'
    # Check if any files were generated, if not, create the placeholder.
    if not any(DEST_DIR.rglob('*.md')):  # No generated files
        if not placeholder.exists():
            placeholder.write_text('This file keeps the directory in Git.\n')
            print(f"Created {placeholder}")
    else:
        if placeholder.exists():
            placeholder.unlink()
            print(f"Removed {placeholder}")

def main():
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    generated_files = []  # <-- track what files are created

    for md_file in SOURCE_DIR.rglob('*.md'):
        relative_path = md_file.relative_to(SOURCE_DIR)
        dest_file = DEST_DIR / relative_path
        dest_file.parent.mkdir(parents=True, exist_ok=True)

        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        update_file(md_file, content)

        player_content, has_player_content = clean_content(content, for_player=True)
        if has_player_content:
            update_file(dest_file, player_content)
            generated_files.append(dest_file)

    # Remove orphaned files in DEST_DIR
    remove_orphan_files(generated_files)

    # Handle .placeholder
    handle_placeholder()

if __name__ == "__main__":
    main()
