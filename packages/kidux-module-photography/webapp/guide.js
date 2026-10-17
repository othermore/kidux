// The guide: one chapter at a time, with Back and Next above it and the
// list of chapters beside it, the one shown marked, remembering where the
// child was. Its chapters are written into the page when the package is
// built (page.py).

(function () {
  "use strict";

  const chapters = window.PHOTOGRAPHY.chapters;
  const STORED = "kidux-photography-chapter";

  const article = document.getElementById("chapter");
  const list = document.getElementById("list");
  const back = document.getElementById("back");
  const next = document.getElementById("next");
  const items = [];

  let shown = 0;

  function show(index) {
    shown = Math.max(0, Math.min(chapters.length - 1, index));
    article.innerHTML = chapters[shown].html;
    window.scrollTo(0, 0);
    back.disabled = shown === 0;
    next.disabled = shown === chapters.length - 1;
    items.forEach((item, at) => {
      item.classList.toggle("here", at === shown);
      item.setAttribute("aria-current", at === shown ? "page" : "false");
    });
    items[shown].scrollIntoView({ block: "nearest" });
    try { localStorage.setItem(STORED, chapters[shown].slug); } catch (error) { /* not kept */ }
  }

  chapters.forEach((chapter, index) => {
    const item = document.createElement("button");
    item.type = "button";
    item.textContent = chapter.title;
    item.addEventListener("click", () => show(index));
    list.appendChild(item);
    items.push(item);
  });

  back.addEventListener("click", () => show(shown - 1));
  next.addEventListener("click", () => show(shown + 1));

  let start = 0;
  try {
    const slug = localStorage.getItem(STORED);
    start = Math.max(0, chapters.findIndex((chapter) => chapter.slug === slug));
  } catch (error) { start = 0; }
  show(start);
  // Next has the focus, for a child to go on with Enter; on the last
  // chapter, where it cannot be pressed, the chapter's place in the list.
  (next.disabled ? items[shown] : next).focus();
})();
