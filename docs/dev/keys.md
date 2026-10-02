# Keyboards: which keys Kidux binds, and how a machine's are added

A child's session binds a handful of keys in labwc's configuration
(session.md, section 3), and the screens write those keys where a child
sees them (D61). This is how the keys are named, why they are the same on
a MacBook and on a PC, what differs, and what to do when someone's laptop
sends something else.

## The keys

| Does | labwc keysym | Runs | The tooltip on the bar that says it (D64) |
|---|---|---|---|
| Home | `Super_L` | labwc's `ForEach` in the kiosk; a signal to the launcher on the desk | Home's: `⌘` on a Mac, `Win` elsewhere |
| Close | `A-F4` | a signal to the launcher | Close's: `Alt+(fn)F4` on a Mac whose function keys are media keys first, `Alt+F4` elsewhere |
| Round the windows | `A-Tab`, `A-S-Tab` | a signal to the launcher, `SIGRTMIN+1` and `+2`: the bar's round (launcher.md section 5) | the button Alt+Tab would go to first, the next in the bar: `Alt+Tab`; Home's says only Super's key (D66) |
| Screen brighter, darker | `XF86MonBrightnessUp`, `XF86MonBrightnessDown` | `kidux-keys brightness up`, `down` | none: the key has a picture on it |
| Keyboard light | `XF86KbdBrightnessUp`, `XF86KbdBrightnessDown` | `kidux-keys keyboard up`, `down` | |
| Sound | `XF86AudioRaiseVolume`, `XF86AudioLowerVolume`, `XF86AudioMute` | `kidux-keys volume up`, `down`, `mute` | |

`kidux-keys` (kidux-launcher) changes the level a step of ten, keeps the
screen at five per cent at least, and does nothing on a machine without
the thing; having changed a level, it touches
`$XDG_RUNTIME_DIR/kidux/levels`, and the corner, which watches that file,
shows the new level at once. The
keysyms are xkb's, which is what labwc matches (`xkb_keysym_from_name`).
Both do it through `kidux.hardware.key`, which the trusted screens call
too: under `cage` nothing binds a key, so the sign-in and lock screens
answer the same keysyms themselves (`kidux_greeter/laptop.py`), matched
by number, since GTK 4 names them without xkb's `XF86` prefix
(`MonBrightnessUp`), and logged (`laptop key: volume up`), which
`02-boot.py` reads after sending the volume key to the sign-in screen. A
key added here is added in both `rc.xml` files and in `laptop.KEYSYMS`,
with its keysym's number and name, whose test holds it to
`kidux.hardware.KEYS`.

## Why the same on a Mac and on a PC

A laptop's keyboard, whatever the maker, sends its special keys as the
kernel's `KEY_BRIGHTNESSUP`, `KEY_KBDILLUMUP`, `KEY_VOLUMEUP`, `KEY_MUTE`
and so on: on a PC the keyboard's firmware turns Fn+F5 into that key, on a
MacBook the `hid_apple` driver does it. xkb turns each into the same
`XF86` keysym, so one binding serves both.

What differs is which comes first, the media key or the function key:

- On a MacBook `hid_apple`'s `fnmode` decides. `1` (`fkeyslast`) and `3`
  (`auto`, the default in trixie) make F1 to F12 media keys unless fn is
  held; `2` (`fkeysfirst`) the other way round; `0` disables fn, and the
  keys are plain function keys. `kidux.hardware.function_keys_need_fn`
  reads `/sys/module/hid_apple/parameters/fnmode`, and `function_key("F4")`
  writes `(fn)F4` or `F4` accordingly; `super_key()` writes `⌘` when the
  machine's DMI vendor is Apple. Alt+F4 is one binding either way: labwc
  sees `F4` only when the child presses what the machine wants for it.
- On a PC most keyboards send the function key first and the media key
  with Fn held; some have an Fn lock. Kidux writes `Alt+F4` and binds
  both the function key and the media keysyms, so it works either way.

## When a machine's keys do not work

A laptop whose keys do nothing sends something Kidux does not bind, or
nothing at all. To find out, as root on the machine, with the child's
session or the sign-in screen up:

```
libinput debug-events --show-keycodes
```

prints, for every key pressed, the kernel's key name (`KEY_BRIGHTNESSUP`)
and its code. Then:

- A key with the right kernel name that labwc still ignores is an xkb
  matter: `xkbcli how-to-type` and the keymap's `XF86` names. Rare.
- A key with another kernel name, `KEY_F21` say, needs a binding of its own
  in both `rc.xml` files, or a `hwdb` entry that renames the scancode to
  the kernel name every other laptop uses. The hwdb way is the one to
  ship: `packages/kidux-session/conf/70-kidux-keyboard.hwdb` (not there
  yet) would carry lines like systemd's own `60-keyboard.hwdb`, one block
  per DMI match (`evdev:atkbd:dmi:bvn*:bvr*:bd*:svn<vendor>:pn<product>*`),
  so that a report from a family, with the output above and their
  `/sys/class/dmi/id/{sys_vendor,product_name}`, becomes a few lines and
  a test.
- A key that sends nothing at all is the firmware's, and there is nothing
  to bind; the launcher's sliders do the same with the mouse.

Whatever the fix, it is a change to `kidux-session` (the bindings, the
hwdb) or to `kidux.hardware` (how a key is written), never to a module:
a module never sees these keys, since the compositor takes them first.
