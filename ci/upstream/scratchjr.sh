#!/bin/sh
# ScratchJr, from its community desktop port, built for Linux with a current
# Electron (D68, D69).
#
# Run by ci/build-upstream.sh kidux-module-scratchjr, in an empty directory,
# with the Node.js release upstream.toml names first in PATH. The port,
# ScratchJr-Desktop, puts MIT's own HTML5 ScratchJr in Electron 1.8 through
# electron-compile, which no longer builds. So its code is taken as it is and
# given what a current Electron needs, and nothing else:
#
# - the pages' modules bundled by webpack into the appEntry.js each page
#   already loads, which electron-compile used to transpile on the fly,
#   Electron's own module left for Electron to give at run time;
# - the window given Node in its pages, which ScratchJr's client asks
#   Electron through, as Electron 1.8 did by default;
# - `remote`, which Electron no longer has, and a zoom call it no longer
#   has, left out of the client;
# - no application menu, no Windows installer's start-up hook, and no
#   BrowserView, which the port makes and never loads anything into;
# - no question, at the first start, of where it is used.
#
# Then the app packaged for Linux x64 with @electron/packager. The versions of
# Electron, webpack and the packager are pinned here; the tarball holds the
# packaged directory as it is.

set -eu

ELECTRON=44.5.1
WEBPACK=5.111.1
WEBPACK_CLI=6.0.1
PACKAGER=20.3.0

epoch="$(sh "$UPSTREAM_FETCH" git "$UPSTREAM_REPOSITORY" "$UPSTREAM_COMMIT" .)"
top="$PWD"

echo "==> node $(node --version), npm $(npm --version)"

# The dependencies the app runs with, as the port's package.json names them,
# without electron-compile, electron-forge and the Windows installer's hook;
# and the tools that build it.
python3 - <<'PYTHON'
import json
package = json.load(open("package.json"))
keep = {name: version for name, version in package["dependencies"].items()
        if name not in ("electron-compile", "electron-squirrel-startup")}
package["dependencies"] = keep
package["devDependencies"] = {}
package.pop("config", None)
package["scripts"] = {}
json.dump(package, open("package.json", "w"), indent=2)
PYTHON
rm -f package-lock.json
# The electron package's own install would download Electron's zip into the
# cache, which nothing here runs: the packager takes the zip fetched below.
export ELECTRON_SKIP_BINARY_DOWNLOAD=1
if [ -n "${UPSTREAM_KEPT:-}" ]; then
    # From the source tarball: the versions npm chose when it was made.
    cp "$UPSTREAM_KEPT/package.json" "$UPSTREAM_KEPT/package-lock.json" .
    npm ci --no-audit --no-fund
else
    npm install --no-audit --no-fund
    npm install --no-audit --no-fund --save-dev \
        "electron@$ELECTRON" "webpack@$WEBPACK" "webpack-cli@$WEBPACK_CLI" \
        "@electron/packager@$PACKAGER"
    # The port has no lock file of its own: the one npm wrote, for the
    # source tarball.
    cp package.json package-lock.json "$UPSTREAM_KEEP/"
fi

# The first start asks where ScratchJr is used, for usage figures the app
# sends nowhere on a computer; a child of five cannot answer it, and it has
# no translation. It is taken as unanswered and never asked.
python3 - <<'PYTHON'
from pathlib import Path
usage = Path("src/app/src/utils/AppUsage.js")
text = usage.read_text()
asked = "return window.localStorage.appUsage === undefined;"
assert asked in text, "AppUsage.js no longer asks as it did"
usage.write_text(text.replace(asked, "return false;"))
PYTHON

echo "==> The pages' modules, bundled into the appEntry.js they load"
cat > webpack.config.js <<'WEBPACK'
const path = require('path');
module.exports = {
    mode: 'production',
    target: 'web',
    entry: './src/app/appEntry.js',
    output: {path: path.resolve(__dirname, 'bundle'), filename: 'appEntry.js'},
    // Electron's own module, which the page asks for at run time, and not
    // the npm package of the same name, which only says where Electron is.
    externals: {electron: 'commonjs electron'},
    // snap.svg and its eve load themselves as AMD modules when they find an
    // AMD loader, and webpack's leaves eve undefined; as CommonJS modules,
    // which electron-compile gave them, they find each other.
    module: {parser: {javascript: {amd: false}}},
    performance: {hints: false},
};
WEBPACK
npx webpack --config webpack.config.js
cp bundle/appEntry.js src/app/appEntry.js

echo "==> What a current Electron needs of the client and the main process"
python3 - <<'PYTHON'
from pathlib import Path

client = Path("src/electronClient.js")
text = client.read_text()
text = text.replace("const {ipcRenderer, webFrame, remote} = require('electron');",
                    "const {ipcRenderer, webFrame} = require('electron');")
text = text.replace("webFrame.setLayoutZoomLevelLimits(0, 0);", "")
text = text.replace(
    "const DEBUG =   remote.getCurrentWebContents().browserWindowOptions.isDebug;",
    "const DEBUG = false;")
assert "remote" not in text.split("\n", 30)[-1] or True
client.write_text(text)

main = Path("src/main.js")
text = main.read_text()
text = text.replace("if (require('electron-squirrel-startup')) app.quit(); // eslint-disable-line global-require", "")
text = text.replace(
    """      customVar: 'elephants',
      isDebug: DEBUG
    });""",
    """      customVar: 'elephants',
      isDebug: DEBUG,
      autoHideMenuBar: true,
      webPreferences: {nodeIntegration: true, contextIsolation: false, sandbox: false}
    });""")
text = text.replace("Menu.setApplicationMenu(menu);", "Menu.setApplicationMenu(null);")
start = text.index("  const view = new BrowserView(")
end = text.index("});", start) + 3
text = text[:start] + text[end:]
text = text.replace("  win.setBrowserView(view);\n", "")
main.write_text(text)
for needle in ("nodeIntegration: true, contextIsolation: false",
               "Menu.setApplicationMenu(null);"):
    assert needle in text, needle
PYTHON
grep -q "remote\." src/electronClient.js && { echo "the client still uses remote" >&2; exit 1; }

echo "==> Packaged for Linux x64"
# The packager would download Electron itself, and the release's checksums
# with it, every time. Electron's zip is fetched here instead, so that the
# source tarball holds it, checked against the sums the electron package
# carries, and the packager takes it from there.
zips="$PWD/.kidux-fetched/electron"
zip="electron-v$ELECTRON-linux-x64.zip"
sh "$UPSTREAM_FETCH" url \
    "https://github.com/electron/electron/releases/download/v$ELECTRON/$zip" "$zips/$zip"
expected="$(python3 -c "import json, sys; print(json.load(open('node_modules/electron/checksums.json'))[sys.argv[1]])" "$zip")"
echo "$expected  $zips/$zip" | sha256sum -c --quiet -
npx @electron/packager . ScratchJr --platform=linux --arch=x64 --out=out \
    --electron-zip-dir="$zips" \
    --ignore='^/out$' --ignore='^/bundle$' --ignore='^/webpack.config.js$' \
    --ignore='^/docs$' --ignore='^/\.git' --ignore='^/\.kidux-fetched$' --prune=true
app="$(ls -d out/ScratchJr-linux-x64)"
cp LICENSE "$app/LICENSE.scratchjr"
echo "==> what its binary needs that the machine may not have"
ldd "$app/ScratchJr" | grep "not found" || true
echo "==> $(find "$app" -type f | wc -l) files, $(du -sh "$app" | cut -f1)"
sh "$UPSTREAM_PACK" "$app" "$UPSTREAM_PACKAGE-$UPSTREAM_VERSION" \
    "$UPSTREAM_OUT/$UPSTREAM_TARBALL" "$epoch"
