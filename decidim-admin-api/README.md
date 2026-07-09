# decidim-admin-api

Installable Decidim engine that exposes admin/operator GraphQL mutations needed
by `decidim-cli`.

Stock Decidim exposes public reads and several component write mutations, but it
does not expose the admin UI surface for creating participatory processes,
phases, or components. This engine adds a narrow API layer over Decidim's own
admin forms, permissions, and command objects so an operator or agent can
provision a process without browser automation.

## Install in a Decidim app

```ruby
# Gemfile
gem "decidim-admin_api", path: "../decidim-admin-api"
```

Then restart the Decidim app. The module extends `/api` with admin-scoped
mutations:

- `createParticipatoryProcess`
- `updateParticipatoryProcess`
- `publishParticipatoryProcess`
- `unpublishParticipatoryProcess`
- `createProcessPhase`
- `updateProcessPhase`
- `activateProcessPhase`
- `createComponent`
- `updateComponent`
- `publishComponent`
- `unpublishComponent`

All mutations require an authenticated Decidim admin with `admin:read` and
`admin:write` API scopes.
