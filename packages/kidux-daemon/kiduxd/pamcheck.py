"""Checking a child's own password, on the lock screen.

The only password check the daemon does through PAM (daemon.md section 2): a
child continuing or ending their own locked session types their own password,
which is their Unix password. Signing in is greetd's job, not the daemon's.

The PAM service is /etc/pam.d/kidux: common-auth and common-account, nothing
that opens a session or changes anything. trixie's python3-pam is PyPAM,
whose module is `PAM`.
"""

from kidux.log import get_logger

_log = get_logger("pam")

SERVICE = "kidux"


def check_password(username: str, password: str) -> bool:
    import PAM

    def conversation(auth, queries, user_data):
        replies = []
        for _prompt, kind in queries:
            if kind == PAM.PAM_PROMPT_ECHO_OFF:
                replies.append((password, 0))
            else:
                replies.append(("", 0))
        return replies

    if not password or "\0" in password:
        return False

    auth = PAM.pam()
    auth.start(SERVICE)
    auth.set_item(PAM.PAM_USER, username)
    auth.set_item(PAM.PAM_CONV, conversation)
    try:
        auth.authenticate()
        auth.acct_mgmt()
    except PAM.error as error:
        _log.debug("PAM refused %s: %s", username, error)
        return False
    return True
