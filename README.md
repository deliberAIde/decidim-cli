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
public API. This CLI therefore covers the whole official API surface it can reach, and
keeps an explicit `decidim gql` escape hatch for version-specific fields and modules.
Creating a participatory process itself remains the follow-on Decidim module/community
work.

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
decidim process create|update|publish|phase-create|component-create
```

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


