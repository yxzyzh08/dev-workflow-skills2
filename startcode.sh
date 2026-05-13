#!/usr/bin/env bash
# Local convenience launcher for this workstation only.
# Not part of the distributed skill/plugin contract for this repository.
exec codex --dangerously-bypass-approvals-and-sandbox "$@"
