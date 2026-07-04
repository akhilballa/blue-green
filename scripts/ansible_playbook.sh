#!/usr/bin/env bash
set -euo pipefail

if command -v ansible-playbook >/dev/null 2>&1; then
  exec ansible-playbook "$@"
fi

if [[ -x "$HOME/.local/bin/ansible-playbook" ]]; then
  exec "$HOME/.local/bin/ansible-playbook" "$@"
fi

cat >&2 <<'EOF'
ansible-playbook was not found.

Install the project dependency:
  python3 -m pip install --user -r requirements-dev.txt

If it is already installed, add the user-local bin folder to PATH:
  export PATH="$HOME/.local/bin:$PATH"
EOF

exit 127
