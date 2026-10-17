# Sourced by the acceptance VM's runner, which provides check() and $ARCHIVE.
# phase-4f-plan.md, step 4.30: Simulations, PhET's simulations fetched at
# development time (D68), installs from the archive with kidux-webapps, is
# served under /simulations/ with its page and every simulation, each in a
# version PhET published under CC BY 4.0, and is removed without a trace of
# the module's own.

ADMIN_AS="runuser -u debian -- /usr/local/bin/kidux-as"
SIMS=/usr/share/kidux/modules/simulations
SITE=/usr/share/kidux/webapps/simulations

check "kidux-module-simulations installs through the daemon, with kidux-webapps" \
    sh -c "$ADMIN_AS install simulations | grep -q '^installed ' && dpkg -s kidux-webapps >/dev/null"
check "its manifest, icon, Spanish words, page, simulations and their licence are in place" \
    sh -c "test -f $SIMS/module.toml && test -f $SIMS/icon.svg \
           && test -f /usr/share/locale/es/LC_MESSAGES/kidux-module-simulations.mo \
           && test -f $SITE/index.html && test -f $SITE/LICENSE \
           && [ \"\$(ls $SITE/sims/*_all.html | wc -l)\" -ge 40 ]"
check "no simulation is under CC BY-NC, and the licence names CC BY 4.0 and PhET's attribution" \
    sh -c "! grep -l 'creativecommons.org/licenses/by-nc/' $SITE/sims/*_all.html \
           && grep -q 'creativecommons.org/licenses/by/4.0' $SITE/LICENSE \
           && grep -q 'Simulation by PhET Interactive Simulations' $SITE/LICENSE"
check "the server answers for the page and for a simulation" \
    sh -c "for _ in \$(seq 20); do curl -fsS 'http://127.0.0.1:8123/simulations/?lang=es' | grep -q 'Simulaciones' && break; sleep 0.5; done \
           && curl -fsS 'http://127.0.0.1:8123/simulations/?lang=es' | grep -q 'Simulaciones' \
           && curl -fsS -o /dev/null 'http://127.0.0.1:8123/simulations/sims/build-an-atom_all.html'"
check "it is listed for a child, switched off" \
    sh -c "$ADMIN_AS modules marta | grep -qx 'simulations off'"
check "removing it leaves nothing of the module behind" \
    sh -c "$ADMIN_AS remove simulations | grep -q '^removed ' && test ! -e $SIMS && test ! -e $SITE \
           && test -z \"\$(find /usr/share/locale -name 'kidux-module-simulations.*')\""
