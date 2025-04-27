import os
import pathlib

SOURCE_DIR = pathlib.Path('wiki')
DEST_DIR = pathlib.Path('public/handbook')

def extract_player_sections(content):
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

def main():
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    for md_file in SOURCE_DIR.rglob('*.md'):
        relative_path = md_file.relative_to(SOURCE_DIR)
        dest_file = DEST_DIR / relative_path
        dest_file.parent.mkdir(parents=True, exist_ok=True)

        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        player_content, has_player_content = extract_player_sections(content)

        if has_player_content:
            with open(dest_file, 'w', encoding='utf-8') as f:
                f.write(player_content)

if __name__ == "__main__":
    main()
