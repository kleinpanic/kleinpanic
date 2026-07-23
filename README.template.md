<!-- ═══════════════════════════════════════════════════════════════════
     README.md is GENERATED from this template + profile.yml.
     Do not edit README.md directly. Regenerate with:
       python3 scripts/generate_readme.py
     CI regenerates weekly and on changes to this file / profile.yml / scripts/.
     ═══════════════════════════════════════════════════════════════════ -->
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=EA24F7&height=100&section=header&text=kleinpanic&fontColor=ffffff&fontSize=40&fontAlignY=38&desc=systems+%7C+terminal+%7C+open+source&descAlignY=60&descSize=16" />
</p>

<div align="center">
<pre>
  _  ___     _      ___           _    
 | |/ / |___(_)_ _ | _ \__ _ _ _ (_)__ 
 | ' <| / -_) | ' \|  _/ _` | ' \| / _|
 |_|\_\_\___|_|_||_|_| \__,_|_||_|_\__|
</pre>

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=15&duration=2000&pause=100&multiline=true&width=700&height=100&color=EA24F7&lines=Linux+%7C+Debian+%7C+Arch+%7C+Neovim+%7C+DWM;C+%7C+Python+%7C+TypeScript+%7C+Rust+%7C+Bash;Systems+%C2%B7+Networking+%C2%B7+Terminal+Tools;DRM+Hater+%C2%B7+Privacy-First+%C2%B7+Self-Hosted" />

{{LINKS}}

<p>{{STATS}}</p>
</div>

```
┌─────────────────────────────────────────────────────────────┐
│  Systems tinkerer. Linux developer. Terminal-first.         │
│  I write things that talk to hardware, run in the terminal, │
│  or solve a problem I couldn't find a good solution for.    │
│  Privacy-first. Self-hosted where it makes sense. No DRM.   │
└─────────────────────────────────────────────────────────────┘
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Setup

```
┌──────────────────┬─────────────────────────────────────────────────────┐
│  OS              │  Debian 13 (Trixie)  ·  Arch Linux                  │
│  WM              │  DWM                                                 │
│  Editor          │  Neovim                                              │
│  Shell           │  Zsh                                                 │
│  Terminal        │  st                                                  │
├──────────────────┼─────────────────────────────────────────────────────┤
│  Workstations    │  Dell Inspiron (x2)  ·  MacBook Pro                 │
│  Server          │  Dell PowerEdge R630                                 │
│  AI              │  NVIDIA DGX Spark                                    │
│  SBCs            │  Raspberry Pi 5  ·  Raspberry Pi 4                  │
│  Edge            │  DigitalOcean droplet                                │
└──────────────────┴─────────────────────────────────────────────────────┘
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## [kleinpanic.com](https://kleinpanic.com)

The site is `w3m`, `lynx`, and `curl` compliant.

```bash
curl https://kleinpanic.com        # browse from the terminal
curl https://kleinpanic.com/ip     # check your public IP
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Stack

<p align="center">
  <img src="https://skillicons.dev/icons?i=c,py,bash,ts,js,java,rust,arduino&perline=8&theme=dark" />
  <br/>
  <img src="https://skillicons.dev/icons?i=linux,debian,arch,neovim,git,docker,nginx,githubactions,raspberrypi&perline=9&theme=dark" />
  <br/>
  <img src="https://skillicons.dev/icons?i=sqlite,mongodb,github,cmake&perline=8&theme=dark" />
</p>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Featured Projects

{{FEATURED}}

Full index: [github.com/kleinpanic?tab=repositories](https://github.com/kleinpanic?tab=repositories) · retired work: [Archived](https://github.com/kleinpanic/Archived)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Recently Active

{{RECENT}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Languages

{{LANGUAGES}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Hugging Face

{{HUGGINGFACE}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Things I've built that I actually use

<details>
<summary><kbd>toralizer</kbd> — transparent Tor proxy for any program</summary>
<br/>

```bash
$ toralizer curl https://ifconfig.me
# → routes curl through Tor via LD_PRELOAD SOCKS5 hook
# → no app config needed, works on anything dynamically linked

$ toralizer wget https://example.com/file.tar.gz
```

</details>

<details>
<summary><kbd>lumos</kbd> — unified brightness control (laptop + external monitors)</summary>
<br/>

```bash
$ lumos 70          # set laptop backlight to 70% via sysfs
$ lumos --ddc 50    # set external monitor via DDC/CI protocol
$ lumos             # show current brightness levels
```

</details>

<details>
<summary><kbd>quicknotes</kbd> — terminal sticky notes with VimWiki integration</summary>
<br/>

```bash
$ quicknotes add "fix the lumos DDC edge case"
$ quicknotes ls
  [0] fix the lumos DDC edge case
  [1] read more about libsodium streams

$ quicknotes nb     # opens a VimWiki scratchpad in Neovim
```

</details>

<details>
<summary><kbd>OSLA</kbd> — offline LICENSE generator</summary>
<br/>

```bash
$ osla MIT          # writes LICENSE with current year + git author
$ osla --list       # show available license templates
$ osla GPL-3.0
```

</details>

<details>
<summary><kbd>bx</kbd> — encrypted, resumable backups over SSH</summary>
<br/>

```bash
$ bx client sync /home/klein user@server:/backups
# → BLAKE3 hashed, libsodium encrypted, zstd compressed
# → resumable, SQLite manifest, deduped

$ bx server start   # run as a backup receive daemon
```

</details>

<details>
<summary><kbd>fblogin</kbd> — framebuffer display manager</summary>
<br/>

```bash
# Replaces getty entirely — runs directly on /dev/fb0
# PAM auth + fprintd fingerprint support
# No X11, no Wayland, no display server needed at boot
```

</details>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Self-Hosted

Everything I run, I run myself. Public endpoints:

<p align="center">
  <a href="https://kleinpanic.com"><img src="https://img.shields.io/badge/web-kleinpanic.com-EA24F7?style=for-the-badge&logo=firefox&logoColor=white" /></a>
  &nbsp;
  <a href="https://git.kleinpanic.com"><img src="https://img.shields.io/badge/git-git.kleinpanic.com-609926?style=for-the-badge&logo=gitea&logoColor=white" /></a>
</p>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{{LAST_UPDATED}}

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=EA24F7&height=80&section=footer" />
</p>

<p align="center"><a href="https://kleinpanic.com">kleinpanic.com</a> · <a href="https://git.kleinpanic.com">git.kleinpanic.com</a></p>
