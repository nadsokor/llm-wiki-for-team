# Obsidian LLM Wiki Deployment Pack

This workspace contains an agent-readable deployment spec for a two-vault knowledge system:

- a shared `Team Sources` vault for canonical source materials and team ground-truth public wiki notes
- a private per-user wiki vault for ingest, synthesis, and personal outputs

Files:

- `spec/deployment-plan.md`: architecture, governance, folder layout, and Obsidian settings
- `spec/admin-role.yaml`: bootstrap contract for the administrator side
- `spec/user-role.yaml`: bootstrap contract for the user side
- `prompts/source-curator-agent.md`: operating prompt for the shared source curator agent
- `prompts/personal-ingest-agent.md`: operating prompt for the private ingest agent

Recommended reading order:

1. `spec/deployment-plan.md`
2. `spec/admin-role.yaml`
3. `spec/user-role.yaml`
4. the prompt file for the agent you want to deploy
