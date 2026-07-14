tea pr list --repo molecule-ai/example --state open --json number,title
curl https://git.moleculesai.app/api/v1/repos/molecule-ai/example --jq '.name'
curl https://git.moleculesai.app/api/v1/repos/molecule-ai/example | jq '.name'
