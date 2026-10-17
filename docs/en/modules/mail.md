# Mail

*[Versión en español](../../es/modules/mail.md)* · [Back to the user guide](../user-guide.md#9-learning-modules)

**Mail** is a mailbox of the child's own, in Thunderbird, the mail program. The child reads and writes their messages there, and has nothing to set up: the account is the one an adult gives.

| | |
|---|---|
| **For** | Children from 8 up |
| **Needs** | The internet to send and receive, and an email account: Gmail, Outlook, iCloud or any provider that speaks IMAP |
| **Program** | [Thunderbird](https://www.thunderbird.net/), by MZLA and the Mozilla community, under the MPL-2.0 licence, from Debian |

## What it is

Thunderbird, set up by Kidux for one child and one account. The child sees their inbox, writes messages, and nothing else: Thunderbird's chat, its add-ons and its advanced settings are closed.

![Mail](../../images/en/module-mail.png)

## What an adult sets

| Setting | What it does |
|---|---|
| **Email address** | The child's email address. Mail finds the provider's servers from it by itself, for Gmail, Outlook, Hotmail, iCloud, Yahoo and most others. |
| **Name** | The name the child's messages are sent as. |
| **Incoming server** | Only for a provider Mail cannot find by itself: its IMAP server, such as `imap.example.org`. A server on a port of its own is written with the port, such as `imap.example.org:143`. |
| **Outgoing server** | Only for such a provider: its SMTP server, such as `smtp.example.org`. |

The adult then opens Mail with the child the first time. For a Gmail or Outlook account, Google's or Microsoft's own sign-in window opens inside Mail. The adult signs in there, with the second step if the account has one, and Mail stays signed in. For any other provider, Mail asks for the password once. The adult types it, with the box to remember it ticked, and Mail keeps it. The password stays in the child's own part of the computer, which nobody else on it can read. The panel never has it.

## Good to know

- A Google account of a child under thirteen is managed with Family Link, and Google does not let such an account sign in to Mail. For it, the [Gmail](gmail.md) module is the way.
- Whatever the child changes in the account is put back the next time Mail opens, and an account added by hand is gone: the account is always the one given on the panel. Without an address on the panel, or with a provider Mail cannot find and no servers given, Mail opens with only its local folders.
- A link in a message leads nowhere. An attachment is saved in the child's **Downloads**, and never opened with another program.
- When a server does not answer, Mail says so in a bubble above the bar, and in the line along its bottom.

![Mail's bubble when its server does not answer](../../images/en/mail-notice.png)
