import os
import pathlib
import datetime
import subprocess
import re

SOURCE_DIR = pathlib.Path('wiki')
DEST_DIR = pathlib.Path('public/handbook')

def get_last_commit_author():
    try:
        author = subprocess.check_output(
            ['git', 'log', '-1', '--pretty=%an'], 
            stderr=subprocess.PIPE
        ).decode('utf-8').strip()
        return author
    except subprocess.CalledProcessError as e:
        print(f"Error getting last commit author: {e}")
        return "Unknown"

def get_footer():
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    author = get_last_commit_author()
    return f"\n---\nLast Updated: {now}\nAuthor: {author}\n"

def clean_content(content, for_player=False):
    if not for_player:
        return content

    # Remove SECRET blocks
    content = re.sub(r'<!--\s*SECRET\s*-->.*?<!--\s*END\s*-->', '', content, flags=re.DOTALL | re.IGNORECASE)

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

    # If no explicit PLAYER blocks, return whole content after secret removal
    if not has_player_content:
        return content, False

    return '\n'.join(output), True

def update_file(path, content):
    lines = content.rstrip().splitlines()
    if len(lines) >= 3 and lines[-3] == "---" and lines[-2].startswith("Last Updated:"):
        lines = lines[:-3]
    updated_content = "\n".join(lines).rstrip() + get_footer()
    with open(path, 'w', encoding='utf-8') as f:
        f.write(updated_content)

def remove_orphan_files(valid_files):
    """Remove files in DEST_DIR that are not among the generated valid_files."""
    for file in DEST_DIR.rglob('*.md'):
        if file not in valid_files:
            print(f"Removing orphaned file: {file}")
            file.unlink()

def handle_placeholder():
    """Handle .placeholder creation or deletion."""
    placeholder = DEST_DIR / '.placeholder'
    if not any(DEST_DIR.rglob('*.md')):
        if not placeholder.exists():
            placeholder.write_text('This file keeps the directory in Git.\n')
            print(f"Created {placeholder}")
    else:
        if placeholder.exists():
            placeholder.unlink()
            print(f"Removed {placeholder}")

def main():
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    generated_files = []  # Keep track of what files are generated

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

    # Clean up orphan files
    remove_orphan_files(generated_files)

    # Handle .placeholder
    handle_placeholder()

if __name__ == "__main__":
    main()
