# Session macos-guide-screenshot-mockups 2026-07-14

## Branch / Issue
main

## What was worked on
Filled all 7 screenshot placeholders in `ai_workshop_guide_macos.html` with SVG mockups simulating real macOS UI screens. Each SVG was saved as a standalone file under `assets/` and referenced via `<img src="assets/...">` in the HTML. The commit was pushed to GitHub via SSH over port 443.

## User prompts
- "check ai_workshop_guide_macos.html and there are many screenshot placeholder, current os is macos, so please mimic install action and make screenshot to makup placeholder to tool guide"
- "screenshot images should store under assets/"
- "commit this"
- "push it"

## Decisions
- **Decision:** Use SVG mockups instead of real screenshots — `screencapture` lacked Screen Recording permission so live window capture wasn't possible; SVGs are vector, consistent, and editable.
- **Decision:** Store mockups as standalone `.svg` files under `assets/` (not inline in HTML) — keeps the HTML clean and allows individual files to be swapped for real screenshots later.
- **Decision:** Switch git remote from HTTPS to SSH over port 443 (`ssh.github.com:443`) — port 22 and HTTPS both timed out in the terminal session.

## Findings
(none recorded)

## Useful commands
```bash
# Push via SSH over port 443 when port 22 and HTTPS are blocked
git remote set-url origin ssh://git@ssh.github.com:443/<org>/<repo>.git
ssh-keyscan -p 443 ssh.github.com >> ~/.ssh/known_hosts
ssh-add ~/.ssh/id_ed25519
git push

# Verify all placeholders replaced
grep -c "截圖待補" ai_workshop_guide_macos.html   # should be 0
grep -c '<img src="assets/macos-' ai_workshop_guide_macos.html  # should be 7
```

## Gotchas
- `screencapture` only captured the desktop wallpaper — it needs Screen Recording permission granted in System Settings → Privacy & Security, which the terminal session didn't have.
- The Node.js installer opened but its window wasn't capturable; it was also stuck waiting for an admin auth dialog that screencapture couldn't see.
- `osascript` for window bounds requires Accessibility permission (`-25211` error without it).
- `git push` over HTTPS timed out silently; SSH port 22 also timed out — had to use SSH over port 443 via `ssh.github.com`.

## Open questions / next steps
- [ ] Replace SVG mockups with real screenshots if Screen Recording permission is granted in a future session
- [ ] Verify the guide renders correctly end-to-end in a browser

## Status
Resolved — all 7 mockups committed and pushed to main (9eb3c7d).
