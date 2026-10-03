// Run by kidux-webapp in CodeCombat's first page once the child is signed
// in (phase-4c-plan.md, 4.17), with window.KIDUX.lang the child's language:
// the account's language becomes the child's, through CodeCombat's own
// pages, as the site's language menu would set it.
(async () => {
  const codes = { es: "es-ES", en: "en-US" };
  const wanted = codes[window.KIDUX.lang] || window.KIDUX.lang;
  const me = await (await fetch("/auth/whoami", { credentials: "same-origin" })).json();
  if (me && me._id && !me.anonymous && me.preferredLanguage !== wanted) {
    await fetch(`/db/user/${me._id}`, {
      method: "PATCH",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ preferredLanguage: wanted }),
    });
  }
})()
