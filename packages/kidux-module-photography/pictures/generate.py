#!/usr/bin/python3
"""Asks Gemini for one of the guide's pictures, where no photograph is found.

    KIDUX_GEMINI_KEY_FILE=<file> pictures/generate.py <name> [--model MODEL]

A development-time tool, run by hand and not installed (docs/dev/photography.md,
section 5; D102). The prompt is pictures/prompts/<name>.txt, kept in the
repository beside the picture so that anyone can see how it was made. The
answer is kept as it came under build/pictures-src/generated/, outside the
package, and written as pictures/<name>.jpg through prepare.py. Its entry in
pictures.toml is written by hand: `author = "generated"`, the model, and
the prompt's file.

The key is read from the file KIDUX_GEMINI_KEY_FILE names, which is kept
outside the repository, and goes only into the request's header: never
into an address, an argument, a log or a message.
"""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

PICTURES = Path(__file__).resolve().parent
REPO = PICTURES.parents[2]
GENERATED = REPO / "build" / "pictures-src" / "generated"
MODEL = "gemini-2.5-flash-image"
API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def key() -> str:
    named = os.environ.get("KIDUX_GEMINI_KEY_FILE")
    if not named:
        raise SystemExit("KIDUX_GEMINI_KEY_FILE names the file the key is in")
    text = Path(named).read_text(encoding="utf-8").strip()
    if not text:
        raise SystemExit("the key's file is empty")
    return text


def generate(prompt: str, model: str) -> tuple[bytes, str]:
    """The picture's bytes and its type, from the first picture in the answer."""
    request = urllib.request.Request(
        API.format(model=model),
        data=json.dumps({"contents": [{"parts": [{"text": prompt}]}],
                         "generationConfig": {"responseModalities": ["IMAGE"]}}).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": key()},
        method="POST")
    try:
        with urllib.request.urlopen(request, timeout=180) as answer:
            said = json.load(answer)
    except urllib.error.HTTPError as error:
        # Google's own message, which never holds the key.
        detail = error.read().decode("utf-8", "replace")[:600]
        raise SystemExit(f"Gemini answered {error.code}: {detail}") from None
    for candidate in said.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                return base64.b64decode(inline["data"]), inline.get("mimeType", "image/png")
    raise SystemExit(f"no picture in the answer: {json.dumps(said)[:600]}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("name", help="the picture's name, without .jpg")
    parser.add_argument("--model", default=MODEL)
    arguments = parser.parse_args(argv)
    prompt = (PICTURES / "prompts" / f"{arguments.name}.txt").read_text(encoding="utf-8").strip()
    data, kind = generate(prompt, arguments.model)
    GENERATED.mkdir(parents=True, exist_ok=True)
    raw = GENERATED / f"{arguments.name}.{'jpg' if kind == 'image/jpeg' else 'png'}"
    raw.write_bytes(data)
    print(f"{raw}: {len(data) // 1000} kB from {arguments.model}")
    sys.path.insert(0, str(PICTURES))
    import prepare
    return prepare.main([str(raw), arguments.name])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
