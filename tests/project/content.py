#!/usr/bin/python3
"""Refuse a change that leaves a lesson translated from an older English text.

    tests/project/content.py [module-content-directory ...]

Learning modules ship their text in their own package, under
``packages/kidux-module-<id>/content/<lang>/``, since a source package holds
only its own directory. English is the source; every other language is a
translation of a specific version of it.

A translation that silently goes stale is worse here than in an interface. An
interface string is a word, and a wrong word is obvious. A lesson is an
explanation, and a Spanish child can read a perfectly fluent explanation of the
*previous* version of an exercise and simply be unable to do it. Nobody notices,
least of all the child, who assumes they did not understand.

So every translated file records the SHA-256 of the English file it was
translated from, in its front matter:

    ---
    source_sha256 = "d2f9..."
    ---

and this fails if that hash no longer matches. Editing English without
retranslating fails the build. Retranslating means recomputing the hash, which
is what ``--update`` does.

The check is on content, not on timestamps: a git checkout writes every file
with the current time, so dates would report a project's whole content as stale
every time somebody cloned it.
"""

import argparse
import hashlib
import sys
import tomllib
from pathlib import Path

#: The language every other one is translated from.
SOURCE_LANGUAGE = "en"

#: Files with text in them. Anything else in a content directory — a picture, a
#: sound — is shared between languages and has nothing to keep in step.
TEXT_SUFFIXES = {".md", ".toml", ".txt"}

FRONT_MATTER_FENCE = "---"


class ContentProblem(Exception):
    pass


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_front_matter(path: Path) -> dict:
    """Parse the TOML block between the first two --- lines.

    Returns an empty dictionary when a file has no front matter at all, which
    is a separate problem from having front matter that does not parse.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    if not lines or lines[0].strip() != FRONT_MATTER_FENCE:
        return {}

    try:
        end = next(
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.strip() == FRONT_MATTER_FENCE
        )
    except StopIteration:
        raise ContentProblem(f"{path}: front matter is never closed") from None

    block = "\n".join(lines[1:end])
    try:
        return tomllib.loads(block)
    except tomllib.TOMLDecodeError as error:
        raise ContentProblem(f"{path}: front matter is not valid TOML: {error}") from None


def write_source_hash(path: Path, digest: str) -> None:
    """Record a new source hash, leaving the rest of the file alone."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    for index, line in enumerate(lines):
        if line.strip().startswith("source_sha256"):
            lines[index] = f'source_sha256 = "{digest}"\n'
            path.write_text("".join(lines), encoding="utf-8")
            return

    raise ContentProblem(f"{path}: no source_sha256 line to update")


def check_module(module_dir: Path, *, update: bool) -> list[str]:
    """Check one module's translations against its English source."""
    problems: list[str] = []

    source_dir = module_dir / SOURCE_LANGUAGE
    if not source_dir.is_dir():
        return [f"{module_dir}: has no {SOURCE_LANGUAGE}/ directory to translate from"]

    languages = sorted(
        entry.name
        for entry in module_dir.iterdir()
        if entry.is_dir() and entry.name != SOURCE_LANGUAGE
    )

    if not languages:
        problems.append(
            f"{module_dir}: only exists in {SOURCE_LANGUAGE}. "
            f"Kidux ships in Spanish and English from the first day."
        )

    source_files = sorted(
        path
        for path in source_dir.rglob("*")
        if path.is_file() and path.suffix in TEXT_SUFFIXES
    )

    for language in languages:
        language_dir = module_dir / language

        for source in source_files:
            relative = source.relative_to(source_dir)
            translated = language_dir / relative

            if not translated.is_file():
                problems.append(f"{translated}: missing, but {source} exists")
                continue

            digest = sha256_of(source)

            try:
                front_matter = read_front_matter(translated)
            except ContentProblem as error:
                problems.append(str(error))
                continue

            recorded = front_matter.get("source_sha256")

            if recorded is None:
                problems.append(
                    f"{translated}: no source_sha256 in its front matter, so "
                    f"there is no way to tell whether it is up to date"
                )
                continue

            if recorded != digest:
                if update:
                    write_source_hash(translated, digest)
                else:
                    problems.append(
                        f"{translated}: translated from an older {source}. "
                        f"Retranslate it, then run this with --update."
                    )

        # A translation of something that no longer exists in English is a file
        # a child could still be shown.
        for translated in sorted(language_dir.rglob("*")):
            if not translated.is_file() or translated.suffix not in TEXT_SUFFIXES:
                continue
            relative = translated.relative_to(language_dir)
            if not (source_dir / relative).is_file():
                problems.append(
                    f"{translated}: has no counterpart in {SOURCE_LANGUAGE}/"
                )

    return problems


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "content",
        nargs="*",
        help="a module's content directories to check (default: every "
             "packages/kidux-module-*/content)",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="record the current source hash instead of failing on a stale one",
    )
    arguments = parser.parse_args(argv)

    if arguments.content:
        modules = [Path(directory) for directory in arguments.content]
    else:
        packages = Path(__file__).resolve().parents[2] / "packages"
        modules = sorted(path for path in packages.glob("kidux-module-*/content")
                         if path.is_dir())

    if not modules:
        # Not a failure: a module without words of its own has nothing to
        # keep in step, and a check that fails on nothing is a check people
        # learn to ignore.
        print("==> No module has content; nothing to check.")
        return 0

    problems: list[str] = []
    for module in modules:
        problems.extend(check_module(module, update=arguments.update))

    if problems:
        for problem in problems:
            print(f"FAIL  {problem}", file=sys.stderr)
        print(
            f"\n==> {len(problems)} content problems.",
            file=sys.stderr,
        )
        return 1

    print(f"==> {len(modules)} modules checked; translations are in step.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
