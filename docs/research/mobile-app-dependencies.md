# What the Flutter mobile app needs from the Rails server

Researched 2026-11-11 against `main` at `4f2970b0f`. It supports the plan to drop
user accounts, `Family` tenancy, OAuth/Doorkeeper and SSO. Under that plan the
Flutter app in `mobile/` stays and authenticates with one API key.

Sources are the code itself, cited as `path:line`, plus Apple's FinanceKit
reference (`developer.apple.com/documentation/financekit`).

## Summary

- **API-key mode already works end to end in the Flutter client.** The login
  screen has an "API key" dialog (`mobile/lib/screens/login_screen.dart:118`,
  `:499`). `AuthService.loginWithApiKey` checks the key with
  `GET /api/v1/accounts` and stores it (`mobile/lib/services/auth_service.dart:349`).
  `ApiConfig.getAuthHeaders` then sends `X-Api-Key` in place of
  `Authorization: Bearer` on every request (`mobile/lib/services/api_config.dart`).
  The client does not need a new auth mechanism. It needs the token and SSO
  paths removed and three user-derived fields replaced (see
  [Client changes](#client-changes)).
- **The mobile app does not use push notifications.** It has no FCM, APNs or
  `push_subscriptions` code (a grep of `mobile/` for
  `firebase|apns|push_subscr|fcm` finds nothing). `MobileDevice` is not a push
  record. It ties Doorkeeper tokens to a device for the email, password and SSO
  login flows (`app/models/mobile_device.rb`). `apnotic`,
  `PushSubscription` and `/api/v1/push_subscriptions` served the native Swift
  iOS app added in #3134 (`0aa43de10`) and removed in #3235 (`390ed5061`).
- **FinanceKit sync is not in the Flutter app.** The `mobile/` tree never
  mentions FinanceKit. The server-side publisher protocol
  (`/api/v1/financekit/*`) expects a native iOS client that is not in this
  repository. It relies heavily on users, families and admins (see
  [FinanceKit](#apple-financekit)).
- **Server-side per-user and per-family scoping is everywhere.** Every endpoint
  the app uses resolves data through `current_resource_owner.family`,
  `Account.accessible_by(user)` or `current_resource_owner.chats`. Removing
  users means rewriting that scoping. The JSON the app *reads* barely depends
  on it: only the login and SSO user payload, and `month_start_day` from
  `family_settings`.

## Authentication flows the client implements

| Flow | Client code | Server endpoint(s) | Keep for single-key mode? |
| --- | --- | --- | --- |
| Email and password login, with optional TOTP (`otp_code`, `mfa_required` on 401) | `auth_service.dart:88-140`, `login_screen.dart:150` | `POST /api/v1/auth/login`, which issues a Doorkeeper token via `MobileDevice#issue_token!` | No |
| Token refresh | `auth_service.dart:281` | `POST /api/v1/auth/refresh` (`Doorkeeper::AccessToken.by_refresh_token`) | No |
| Signup | `auth_service.dart:194` and `auth_provider.dart:287` exist, but no screen calls them | `POST /api/v1/auth/signup`, which creates a `Family` | No (already dead in the UI) |
| SSO (OIDC and similar) | `auth_service.dart:408-640`, deep link `sureapp://oauth/callback` handled in `main.dart:229-243` | `GET /api/v1/auth/sso_providers`, web `GET /auth/mobile/:provider` (`config/routes.rb:391`, `sessions#mobile_sso_start`), `POST /api/v1/auth/sso_exchange`, `sso_link`, `sso_create_account` | No |
| **API key** | `auth_service.dart:349`, `auth_provider.dart:222`, `api_config.dart` | Any endpoint with the `X-Api-Key` header, handled by `Api::V1::BaseController#authenticate_api_key` | **Yes** |
| Enable AI | `auth_service.dart:644`, `main_navigation_screen.dart:54,208` | `PATCH /api/v1/auth/enable_ai` (authenticated; accepts an API key) | Replace (see below) |

`Api::V1::BaseController#authenticate_request!` tries OAuth first
(`Authorization` header → `Doorkeeper::AccessToken`) and then the API key
(`X-Api-Key` → `ApiKey.find_by_value`). Either way it sets `@current_user`
(`app/controllers/api/v1/base_controller.rb`). `ApiKey belongs_to :user`,
carries `scopes` (`read` / `read_write`) and has the sources
`web|mobile|monitoring` (`app/models/api_key.rb`). Rate limiting applies only
to API keys and does nothing when self-hosted (`ApiRateLimiter.limit` →
`NoopApiRateLimiter`). Hosted mode allows 100 requests per hour by default,
which a mobile client with offline sync could exceed.

The app makes two non-API web requests:

- `GET /sessions/new` is the **"Test connection" probe** on the backend
  configuration screen (`mobile/lib/screens/backend_config_screen.dart:93`).
  It breaks once the login page is gone and should point at `/up` or
  `/api/v1/version` instead.
- `GET /auth/mobile/:provider` starts SSO and goes away with SSO.

## api/v1 endpoints the mobile app calls

Collected from every `api/v1` URL in `mobile/lib/services/*.dart` and checked
against `config/routes.rb:803-895`.

| Endpoint | Client caller | Scoping on the server today |
| --- | --- | --- |
| `GET /accounts`, `GET /accounts/:id` | `accounts_service.dart:71`, `account_detail_service.dart:32`, plus the API-key validity probe | family plus `accessible_by(user)` |
| `GET /balances` | `account_detail_service.dart:61` | family plus `accessible_by(user)` |
| `GET /holdings` | `account_detail_service.dart:172` | family plus `accessible_by(user)` |
| `GET /transactions` (`account_id`, `page`, `per_page`, `start_date`, `end_date`, `category_ids[]`), `GET/POST/PATCH/DELETE /transactions[/:id]` | `transactions_service.dart`, used by `sync_service.dart` for offline sync | `accessible_by(user)` |
| `GET /categories` (`roots_only`, `parent_id`, paging) | `categories_service.dart:29` | family |
| `GET /merchants` | `merchants_service.dart:10` | family |
| `GET /tags` | `tags_service.dart:8` | family |
| `GET /budgets`, `GET /budgets/:id` | `budgets_service.dart:40,64` | family |
| `GET /budget_categories`, `GET /budget_categories/:id` | `budgets_service.dart:96,121` | family |
| `GET /cash_flow?view=sankey&start_date&end_date` | `cash_flow_service.dart:66` | family |
| `GET /balance_sheet` | `balance_sheet_service.dart:16` | family |
| `GET /family_settings` (reads only `month_start_day`) | `cash_flow_service.dart:34` | `current_resource_owner.family` |
| `GET/POST/PATCH/DELETE /chats[/:id]`, `POST /chats/:id/messages`, `POST /chats/:id/messages/retry` | `chat_service.dart` | `current_resource_owner.chats`, gated by `require_ai_enabled` on `user.ai_enabled?` |
| `DELETE /users/reset` | `user_service.dart:10` (Settings → reset) | enqueues `FamilyResetJob(family)` |
| `DELETE /users/me` | `user_service.dart:43` (Settings → delete account) | `user.deactivate` |
| `auth/login`, `auth/refresh`, `auth/sso_providers`, `auth/sso_exchange`, `auth/sso_link`, `auth/sso_create_account`, `auth/enable_ai` | `auth_service.dart` | see the auth table above |

## api/v1 endpoints the mobile app does NOT use (removal candidates)

Other clients may still need some of these. The MCP endpoint and the
web app do not use `api/v1`, but custom scripts might. Treat this list as
"unused by `mobile/`", not "unused".

- `GET /version`
- `/financekit/*`, all of it: `capabilities`; `connections` create, show and
  destroy; `account_mappings`; `activate`; `credential`; `repair`; `conflicts`;
  and the `publishers/:publisher_id/batches` upload and status routes. Only the
  absent native iOS client uses them.
- `POST /auth/signup` (client code exists but no UI reaches it)
- `GET /balances/:id`
- `GET /categories/:id`, `POST /categories`
- `GET /merchants/:id`, `POST /merchants`
- `GET /tags/:id`, `POST/PATCH/DELETE /tags`
- `GET /holdings/:id`
- `/rules`, `/rule_runs`
- `/securities`, `/security_prices` (index, show and create)
- `/transactions/:id/split` (show, create, update and destroy)
- `/trades` (all)
- `/transfers`, `/rejected_transfers`
- `/valuations` (all)
- `/recurring_transactions` (all)
- `/family_exports` (including `download`)
- `/imports` (including `preflight` and `rows`), `/import_sessions` (including
  `chunks` and `publish`)
- `GET /usage`
- `GET /spending_vs_normal`
- `/insights` (including `acknowledge`). The removed Swift app used it.
- `/push_subscriptions` (create and destroy). The removed Swift app used it,
  through `apnotic`.
- `POST /sync`, `/syncs` (including `latest`)
- `GET /provider_connections`
- `GET /users/reset/status`
- The test-only routes (`/test*`)

## Could it run with one API key and no users?

Yes. The client already supports it. The work is mostly on the server.

### Server changes

1. **Authentication.** Replace `authenticate_request!` with a single key
   check: compare `X-Api-Key` against one stored secret, either a single
   `ApiKey` row with no `user` or an env or credential value, using a
   constant-time comparison. Delete `authenticate_oauth`,
   `Doorkeeper::Rails::Helpers`, `doorkeeper_token`, the
   `Doorkeeper::Errors` rescue, `setup_current_context_for_api` (which builds
   a `Session` for the user), `reject_guest_writes!` and
   `ensure_current_family_access`. Keep or drop `read`/`read_write` scopes
   (`authorize_scope!`) as you see fit. With one owner, a single full-access
   key is enough. `log_api_access` and the rate limiter log
   `current_resource_owner.email` and `family_id`, so update them too.
2. **`Api::V1::AuthController`.** Remove `signup`, `login`, `refresh`, all
   `sso_*` actions, `MobileDevice` and the `Invitable` include. Remove
   `enable_ai` too, or keep it as a no-op that returns `{ user: {...,
   ai_enabled: true} }` so older builds keep working.
3. **Data scoping.** Every used controller goes through
   `current_resource_owner.family` (22 call sites across the used
   controllers) or `accounts.accessible_by(current_resource_owner)` (accounts,
   transactions, balances and holdings). Both must point at the single data
   root, and "accessible" becomes "all".
4. **Chats.** `Chat belongs_to :user` (`app/models/chat.rb:30`) and the
   controllers use `current_resource_owner.chats`. They need either an
   ownerless chat model or one owner. `require_ai_enabled` reads
   `user.ai_enabled?`, so make it a global setting.
5. **`family_settings`.** The client reads only `month_start_day`
   (`app/views/api/v1/family_settings/show.json.jbuilder`). Keep the route and
   field and point it at whatever replaces `Family`. Renaming it requires a
   client change.
6. **`users/reset` and `users/me`.** Reset becomes "reset all financial data",
   since `FamilyResetJob` takes a family. `DELETE /users/me` stops making
   sense. Remove it, together with the Settings button that calls it.
7. **Remove the web login page.** The client's "Test connection" probe hits
   `/sessions/new`, so either keep a cheap 200 route there or change the
   client (preferred).

### Client changes

Changes needed for correctness once the user-based flows are gone:

- **AI gating.** `AuthProvider.aiEnabled` is `_user?.aiEnabled ?? false`
  (`auth_provider.dart:40`). `_user` is never set in API-key mode, because
  `loginWithApiKey` returns no user and no `GET /users/me` exists. Each
  time someone opens the chat tab, the app shows the "enable AI" prompt and
  calls `PATCH auth/enable_ai` (`main_navigation_screen.dart:54`). Get the
  flag from a settings endpoint, or treat AI as always on.
- **Backend probe.** Change `/sessions/new` to `/up` or `/api/v1/version`
  (`backend_config_screen.dart:93`).
- **Settings.** Remove "delete account" (`settings_screen.dart:401`). The
  profile header already falls back to `settingsUserFallback` when `user` is
  null (`:558-582`).

Cleanup (dead code once the server endpoints are gone):

- The email, password and MFA form; SSO buttons and onboarding
  (`sso_onboarding_screen.dart`, `models/sso_provider.dart`);
  `AuthTokens` and refresh; `DeviceService` (device info exists only for
  `MobileDevice`); the `sureapp://oauth/callback` deep link
  (`main.dart:229-243`, `Info.plist` URL scheme,
  `AndroidManifest.xml:32`); `signup`.
- `User.uiLayout` drives `isIntroLayout` and defaults to `dashboard` when the
  user is null, so nothing breaks. If the intro layout should stay reachable,
  it needs a new source.
- `AuthProvider` can shrink to "is there a stored API key". The
  `getValidAccessToken()` call sites already receive the key in API-key mode
  (`auth_provider.dart:654`), so the services need no change.

### Payload and client-state assumptions

- The login and SSO user payload is `{id, email, first_name, last_name,
  ui_layout, ai_enabled}` (`auth_controller.rb#mobile_user_payload`). It is
  stored in secure storage under `user_data` and used only for display, the
  intro layout, AI gating and telemetry user identity.
- The client stores `auth_mode`, `api_key`, `auth_tokens`, `user_data`,
  `device_id` and `backend_url` (`auth_service.dart:13-17`,
  `device_service.dart`, `api_config.dart`). No family ID or user ID is used
  to build request URLs. All scoping happens on the server.
- The offline transaction store (`offline_storage_service.dart`,
  `database_helper.dart`) is keyed by local and server transaction IDs, not
  by user. It does not clear per user, so a single owner causes no
  migration issue.

## Push notifications (MobileDevice, apnotic)

- `MobileDevice` (`app/models/mobile_device.rb`) records each device that
  signed in with email, password or SSO. It creates the shared Doorkeeper
  application "Sure Mobile" (`sureapp://oauth/callback`) and issues 30-day
  `read_write` tokens bound to the device (`issue_token!`). It has nothing to
  do with push and disappears with OAuth.
- `apnotic` is used only in `app/services/apns/client.rb`, which
  `PushSubscription`, `PushSubscription::Delivery`,
  `DeliverInsightNotificationJob`, `DeliverTestPushNotificationJob` and
  `PushNotificationTest` use. `PushSubscription belongs_to :user`. The only
  API entry point is `/api/v1/push_subscriptions`, and the Flutter app does
  not call it. **The whole push stack can be removed without affecting
  mobile.**

## Apple FinanceKit

- **Not the Flutter app.** The server describes the client as "the iOS
  client", which decides through StoreKit whether to offer Wallet sync
  (`app/controllers/api/v1/financekit/base_controller.rb`,
  `docs/providers/financekit.md`). No such client is in this repository.
- **Same API base, separate credentials.** Enrollment and management
  (`/api/v1/financekit/connections*`, `capabilities`, `conflicts`) inherit
  `Api::V1::BaseController`, so they accept OAuth or `X-Api-Key` with
  `read`/`write` scope. They also require `current_resource_owner.admin?`.
  Batch upload and status (`/financekit/publishers/:id/batches*`) is a
  separate `ActionController::API` that authenticates with a per-publisher
  bearer credential issued by `activate`, `credential` or `repair`
  (`batches_controller.rb#authenticated_item!`).
- **Heavy dependence on users and families.** `FinancekitItem belongs_to
  :family` and `belongs_to :user`. Before every upload, `require_publisher!`
  checks again that `user.active? && user.family_id == family_id &&
  user.admin?`, and that mapped accounts are in
  `family.accounts.writable_by(user)` (`app/models/financekit_item.rb:56-67`).
  Lookups use `current_resource_owner.family.financekit_items.where(user:)`.
  Keeping FinanceKit without users means removing these checks and the
  `user` and `family` foreign keys, then confining the publisher only by its
  credential and the single API key.
- **Apple's requirements** (FinanceKit reference): available on iOS and
  iPadOS 17.0+ and Mac Catalyst 17.0+. The data is on-device data read
  through `FinanceStore` after `requestAuthorization()`. Access requires a
  **managed entitlement** that Apple approves per app, an
  **organization-level** developer account (Account Holder), and
  `NSFinancialDataUsageDescription`. The server never sees Apple credentials.
  The device reads Wallet data and uploads batches
  (`docs/providers/financekit.md`).
- **What follows.** For a personal, single-owner setup, FinanceKit needs a
  native iOS or Mac Catalyst app with an Apple-approved entitlement on an
  organization account. That is a high bar for a personal fork, and the
  Flutter app would need a native plugin to do it. If no such client is
  planned, `/api/v1/financekit/*`, `FinancekitItem` and the related models
  and jobs are removal candidates along with the push stack.

## Open questions

- Will any client besides `mobile/` (scripts, Home Assistant and similar)
  keep calling the unused endpoints, such as imports, `syncs` or
  `valuations`? Nothing in this repository does.
- Should `family_settings` keep its name for client compatibility, or be
  renamed together with a client release?
