#!/bin/sh
# Blockly Games, built for kidux-webapps (D68, D69).
#
# Run by ci/build-upstream.sh kidux-module-blockly-games, in an empty
# directory, with the Node.js release upstream.toml names first in PATH.
# Blockly Games' Makefile fetches its third-party code with svn from GitHub,
# which GitHub no longer serves, and compiles with the Closure Compiler's
# Java build, and this machine has no Java: so this fetches the same code
# with git, through ci/upstream/fetch.sh like everything else, and gives the build the Closure Compiler's native build, from
# npm, behind a `java` that runs it, and `python` that is python3. Then the
# games are compiled and the site made as the Makefile's `offline` target
# makes it, without its bash-only patterns.

set -eu

epoch="$(sh "$UPSTREAM_FETCH" git "$UPSTREAM_REPOSITORY" "$UPSTREAM_COMMIT" .)"
top="$PWD"

# The Closure Compiler's native build, and the two names the build calls.
mkdir -p "$top/.tools/bin"
printf '{"name": "blockly-games-tools", "private": true}\n' > "$top/.tools/package.json"
( cd "$top/.tools" && npm install --no-audit --no-fund \
    google-closure-compiler-linux@20240317.0.0 >/dev/null )
compiler="$top/.tools/node_modules/google-closure-compiler-linux/compiler"
[ -x "$compiler" ]
cat > "$top/.tools/bin/java" <<EOF
#!/bin/sh
# java -jar <closure-compiler.jar> <arguments>: the native compiler, with
# the arguments as they are.
[ "\$1" = -jar ] && shift 2
exec "$compiler" "\$@"
EOF
printf '#!/bin/sh\nexec python3 "$@"\n' > "$top/.tools/bin/python"
chmod 755 "$top/.tools/bin/java" "$top/.tools/bin/python"
PATH="$top/.tools/bin:$PATH"
export PATH

fetch() {
    # fetch <repository> <commit> <directory in it> <destination>
    rm -rf "$top/.fetch"
    sh "$UPSTREAM_FETCH" git "https://github.com/$1" "$2" "$top/.fetch" >/dev/null
    rm -rf "$top/.fetch/.git"
    mkdir -p "$4"
    cp -a "$top/.fetch/$3/." "$4/"
    rm -rf "$top/.fetch"
}

# The third-party code the Makefile's deps target fetches at its newest,
# here at the commits it was when this module was made, so that the same
# script makes the same tarball.
echo "==> The third-party code the Makefile's deps target fetches"
mkdir -p appengine/third-party
sh "$UPSTREAM_FETCH" url https://unpkg.com/@babel/standalone@7.14.8/babel.min.js \
    appengine/third-party/babel.min.js
fetch ajaxorg/ace-builds 184177de1dcc5946b093edba0b0fe1c29c2a127a src-min-noconflict appengine/third-party/ace
fetch NeilFraser/blockly-for-BG 837051b5466457a8f4e956b95bff334d95c26b85 . appengine/third-party/blockly
fetch CreateJS/SoundJS 5213ac5696142bcba216ef10bef3105e5be1d4ef lib appengine/third-party/SoundJS
cp third-party/base.js appengine/third-party/
cp -R third-party/soundfonts appengine/third-party/
fetch NeilFraser/JS-Interpreter 45d00b0c86e48cca1bb3af0f711bc4c0d626c359 . appengine/third-party/JS-Interpreter
java -jar closure-compiler.jar \
    --language_out ECMASCRIPT5 --language_in ECMASCRIPT5 \
    --js appengine/third-party/JS-Interpreter/acorn.js \
    --js appengine/third-party/JS-Interpreter/interpreter.js \
    --js_output_file appengine/third-party/JS-Interpreter/compressed.js

echo "==> The games"
make games

echo "==> The site, as the Makefile's offline target makes it"
site="$top/offline/blockly-games"
rm -rf "$top/offline"
mkdir -p "$top/offline"
cp -R appengine "$site"
cd "$site"
rm -f ./*.yaml ./*.py ./*.sh admin.html apple-touch-icon.png favicon.ico robots.txt
rm -rf gallery* generated
find . -type d -name src -prune -exec rm -rf {} +
find . -path '*/generated/uncompressed.js' -delete
rm -f index/title.png index/title-beta.png pond/crobots.txt common/stripes.svg
rm -rf pond/battle
# The soundfonts' README stays: it is their attribution, which their
# licence asks for.
rm -f third-party/base.js
keep() {
    # keep <directory> <files...>: only those files of it
    dir="$1"; shift
    mkdir -p "$top/.keep"
    for file in "$@"; do mv "$dir/$file" "$top/.keep/"; done
    rm -rf "${dir:?}"/* "${dir:?}"/.[!.]* 2>/dev/null || true
    mv "$top/.keep/"* "$dir/"
    rm -rf "$top/.keep"
}
keep third-party/ace ace.js mode-javascript.js theme-chrome.js worker-javascript.js
keep third-party/SoundJS soundjs.min.js
keep third-party/blockly media
keep third-party/JS-Interpreter compressed.js
find . -name '.DS_Store' -delete
cd "$top"

python3 "$UPSTREAM_CHECK_SITE" "$site" /blockly-games/
cp LICENSE "$site/LICENSE"
echo "==> $(find "$site" -type f | wc -l) files, $(du -sh "$site" | cut -f1)"
sh "$UPSTREAM_PACK" "$site" "$UPSTREAM_PACKAGE-$UPSTREAM_VERSION" \
    "$UPSTREAM_OUT/$UPSTREAM_TARBALL" "$epoch"
