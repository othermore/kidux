// Run by kidux-webapp in CodeCombat's front page when a child with no
// account set asks to sign in by hand (phase-4c-plan.md, 4.17): the site's
// sign-in is a window its Login button opens, with no address of its own,
// so the button is pressed for the child once the page has drawn it.
new Promise((done) => {
  const started = Date.now();
  const look = () => {
    const button = document.querySelector(".login-button");
    if (button) {
      button.click();
      done("opened");
    } else if (Date.now() - started > 20000) {
      done("no button");
    } else {
      setTimeout(look, 250);
    }
  };
  look();
})
