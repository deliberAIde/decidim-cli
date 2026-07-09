# decidim-cli

Command-line client for driving **Decidim** instances over the official GraphQL API.

The goal is the same role as `polis-cli`: an operator or AI agent can inspect an
instance, authenticate as a machine user, run all supported API mutations, export raw
participation data, and normalize it for deliberAIde synthesis.

```powershell
decidim profile add barcelona https://www.decidim.barcelona --auth none
decidim version -p barcelona
decidim gql '{ decidim { version } }' -p barcelona --json

decidim profile add city https://participate.example.gov --auth api-credentials --api-key KEY
decidim login -p city
decidim proposal create 9 "Install Bike Lanes on Main Street" `
  "Dedicated bike lanes would improve cyclist safety and sustainable mobility." `
  -p city --locale en
decidim meeting create 670 "Mobility workshop" "Discuss the transport plan" `
  "2026-09-17T13:00:00Z" "2026-09-17T15:00:00Z" `
  -p city --type-of-meeting ONLINE --registration-type ON_THIS_PLATFORM
```

## What "full CLI" means for Decidim

Decidim exposes:

- Public read GraphQL at `/api`.
- API-credential machine-user sign-in at `/api/sign_in` for mutations.
- Official component mutations for proposals, meetings, and debates.
- Per-instance GraphQL docs at `/api/docs`.
- Open Data exports when the instance has generated them.

Stock Decidim still does **not** expose process/space/component creation through the
public API. This repo now includes `decidim-admin-api/`, an installable Decidim engine
that adds admin/operator GraphQL mutations over Decidim's own admin forms and command
objects. Without that engine, the CLI still covers the official API surface and keeps
`decidim gql` as an escape hatch for version-specific fields and modules.

## Design rules

1. **Arm's length.** This CLI contains no Decidim code. It only speaks HTTP/GraphQL to
   unmodified Decidim instances.
2. **Profile-based.** Profiles live in `~/.decidim-cli/config.toml`. Bearer tokens are
   cached in `~/.decidim-cli/credentials.toml`.
3. **Machine-friendly.** Every command supports global `--json`.
4. **Honest boundaries.** High-level commands wrap the official mutations; raw GraphQL
   remains available for installed modules and instance-specific schema drift.

## Main commands

```powershell
decidim profile add NAME BASE_URL
decidim login
decidim logout
decidim session
decidim version
decidim gql QUERY_OR_@FILE
decidim schema

decidim open-data download --out open-data.zip
decidim open-data normalize open-data.zip --out contributions.jsonl

decidim proposal create|update|withdraw|vote|unvote|answer
decidim meeting create|update|withdraw|close
decidim debate create|update|close
decidim process create|update|publish|unpublish|phase-create|phase-update|phase-activate|component-create
decidim component create|update|publish|unpublish
```


## Admin API module

To let the CLI create participatory processes, phases, and components, install the
included Decidim engine in the target Decidim app:

```ruby
# Gemfile in the Decidim app
gem "decidim-admin_api", path: "../decidim-cli/decidim-admin-api"
```

Then restart Decidim and authenticate the CLI as an admin API user. The module adds:

```powershell
decidim process create my-process "Mobility Plan" -p city --locale en
decidim process phase-create PROCESS_ID "Ideation" 2026-09-01T00:00:00Z 2026-10-01T00:00:00Z -p city
decidim component create PROCESS_ID proposals "Ideas" -p city --space-type participatory_processes
decidim process publish PROCESS_ID -p city
```

Voca can still be useful one layer below this: its public material and `voca-tasks`
show fast Decidim instance launch/configuration, DB setup, organization settings, and
admin seeding. The missing part for our agent workflow is the admin content/provisioning
API inside an instance, which is what `decidim-admin-api` supplies.

## Auth

For public reads:

```powershell
decidim profile add meta https://meta.decidim.org --auth none
```

For machine-user writes, create API credentials in Decidim's system panel, then:

```powershell
decidim profile add city https://participate.example.gov --auth api-credentials --api-key KEY
$env:DECIDIM_API_SECRET = "SECRET"
decidim login -p city
```

For an already-issued bearer token:

```powershell
$env:DECIDIM_BEARER = "eyJ..."
decidim login -p city
```

If the token came from an OAuth application, pass the audience/client id:

```powershell
decidim profile add city https://participate.example.gov --auth bearer --jwt-aud CLIENT_ID
```

## References

- Official Decidim API docs: https://docs.decidim.org/en/develop/develop/api/
- API authentication: https://docs.decidim.org/en/develop/develop/api/authentication
- Proposal mutations: https://docs.decidim.org/en/develop/develop/api/reference/components/proposals/create
- Meeting mutations: https://docs.decidim.org/en/develop/develop/api/reference/components/meetings/create
