// The guide: one chapter at a time beside the machine, with Back, Next and
// the list of chapters, remembering where the child was. Its chapters are
// written into the page when the package is built (page.py); a listing's
// button puts the listing in the editor.

(function () {
  "use strict";

  const words = window.BASIC.words;
  const chapters = window.BASIC.chapters;
  const STORED = "kidux-basic-chapter";

  const article = document.getElementById("chapter");
  const list = document.getElementById("list");
  const back = document.getElementById("back");
  const next = document.getElementById("next");
  const contents = document.getElementById("contents");

  let shown = 0;

  function show(index) {
    shown = Math.max(0, Math.min(chapters.length - 1, index));
    article.innerHTML = chapters[shown].html;
    article.hidden = false;
    list.hidden = true;
    article.scrollTop = 0;
    article.parentElement.scrollTop = 0;
    back.disabled = shown === 0;
    next.disabled = shown === chapters.length - 1;
    contents.setAttribute("aria-expanded", "false");
    try { localStorage.setItem(STORED, chapters[shown].slug); } catch (error) { /* not kept */ }
  }

  function showList() {
    list.innerHTML = "";
    chapters.forEach((chapter, index) => {
      const item = document.createElement("button");
      item.type = "button";
      item.textContent = chapter.title;
      item.className = index === shown ? "here" : "";
      // The list goes away with the item that has the focus, so the focus
      // goes back to Chapters, where the keyboard can go on from.
      item.addEventListener("click", () => { show(index); contents.focus(); });
      list.appendChild(item);
    });
    article.hidden = true;
    list.hidden = false;
    contents.setAttribute("aria-expanded", "true");
    list.querySelector(".here").focus();
  }

  back.addEventListener("click", () => show(shown - 1));
  next.addEventListener("click", () => show(shown + 1));
  contents.addEventListener("click", () => (list.hidden ? showList() : show(shown)));

  article.addEventListener("click", (event) => {
    const button = event.target.closest("button.type-in");
    if (!button) { return; }
    const listing = button.parentElement.querySelector("pre");
    window.BASIC.typeIn(listing.textContent.replace(/\n+$/, ""));
  });

  let start = 0;
  try {
    const slug = localStorage.getItem(STORED);
    start = Math.max(0, chapters.findIndex((chapter) => chapter.slug === slug));
  } catch (error) { start = 0; }
  show(start);
})();
