# Sourced by the acceptance VM's runner, which provides check() and $ARCHIVE.
# phase-4e-plan.md, step 4.28: Photography, a guide to taking photographs
# with a real camera, installs from the archive with kidux-webapps, is served
# under /photography/ with every language's guide in its page and its
# photographs beside it, and is removed without a trace of the module's own.

ADMIN_AS="runuser -u debian -- /usr/local/bin/kidux-as"
MODULE=/usr/share/kidux/modules/photography
SITE=/usr/share/kidux/webapps/photography

check "kidux-module-photography installs through the daemon, with kidux-webapps" \
    sh -c "$ADMIN_AS install photography | grep -q '^installed ' && dpkg -s kidux-webapps >/dev/null"
check "its manifest, icon, Spanish words, page and photographs are in place" \
    sh -c "test -f $MODULE/module.toml && test -f $MODULE/icon.svg \
           && test -f /usr/share/locale/es/LC_MESSAGES/kidux-module-photography.mo \
           && test -f $SITE/index.html && test -f $SITE/guide.js \
           && ls $SITE/pictures/*.jpg >/dev/null"
check "the server answers for the page, with the Spanish guide in it" \
    sh -c "for _ in \$(seq 20); do curl -fsS 'http://127.0.0.1:8123/photography/?lang=es' > /tmp/photography.html && break; sleep 0.5; done \
           && grep -q 'Fotografía' /tmp/photography.html && grep -q 'Una caja con un agujero' /tmp/photography.html; \
           status=\$?; rm -f /tmp/photography.html; exit \$status"
check "and for a photograph, as a JPEG" \
    sh -c "picture=\$(basename \$(ls $SITE/pictures/*.jpg | head -1)) \
           && curl -fsS -o /dev/null -w '%{content_type}' http://127.0.0.1:8123/photography/pictures/\$picture | grep -q '^image/jpeg'"
check "it is listed for a child, switched off" \
    sh -c "$ADMIN_AS modules marta | grep -qx 'photography off'"
check "removing it leaves nothing of the module behind" \
    sh -c "$ADMIN_AS remove photography | grep -q '^removed ' && test ! -e $MODULE && test ! -e $SITE \
           && test -z \"\$(find /usr/share/locale -name 'kidux-module-photography.*')\""
