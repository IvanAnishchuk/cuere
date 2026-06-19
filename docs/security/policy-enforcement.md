# Security policy enforcement

How cuere's repository security settings are enforced and kept from drifting —
and why the project uses **settings-as-code** rather than the OpenSSF Allstar
policy bot.

## The model: settings-as-code as the single source of truth

cuere's repository security configuration is declared in
[`.github/settings.yml`](https://github.com/IvanAnishchuk/cuere/blob/main/.github/settings.yml)
and applied by the [Probot **Settings** app](https://probot.github.io/apps/settings/).
The file is version-controlled and changes only through a reviewed pull request,
so branch protection, merge rules, and the security-and-analysis features are
auditable in git history rather than clicked into the GitHub UI.

What `settings.yml` enforces on `main`:

- Pull-request review required — one approval, code-owner review, stale-review
  dismissal, and last-push approval.
- A fixed list of **required status checks** (tests, lint, the three type
  checkers, CodeQL, dependency audit, OSV scan, secret scan, dependency-review,
  and the GitHub Actions audit).
- Signed commits required; force-push and branch deletion forbidden; required
  conversation resolution.
- Repository-level secret scanning with push protection, and Dependabot security
  updates.

This sits inside a three-layer model:

| Layer | Tool | Role |
|-------|------|------|
| **Assess** | [OpenSSF Scorecard](https://scorecard.dev/) | Weekly and on-push scoring of the repo's posture, including a Branch-Protection check that surfaces drift |
| **Enforce** | Probot Settings (`settings.yml`) | Declarative branch protection / repo settings, reviewed in git |
| **Gate** | Required status checks | Blocks merges until the quality and security CI passes |

## Allstar: evaluated, not adopted

[OpenSSF Allstar](https://github.com/ossf/allstar) is a GitHub App that
*continuously enforces* security policies (branch protection, binary artifacts,
dangerous workflows, outside collaborators, …) and files issues or auto-fixes
violations — the enforcement complement to Scorecard's assessment. cuere
evaluated it (issue [#40](https://github.com/IvanAnishchuk/cuere/issues/40)) and
chose **not** to adopt it:

1. **Allstar is built for GitHub organizations; cuere is a personal-account
   repository.** Its install flow targets an organization, its configuration
   lives in an org-level `.allstar` repository, and its opt-in / opt-out
   strategies are org-scoped. There is no documented support for a personal user
   account.
2. **Most of its policies don't apply to a single personal repo.** *Outside
   Collaborators* and *Repository Administrators* are organization concepts with
   no analog here. Of Allstar's policies, only **Branch Protection** is
   meaningful for cuere.
3. **That one policy is already covered — and better.** `settings.yml` enforces
   branch protection declaratively, in version control, and covers more than
   Allstar's branch-protection policy (required checks, signed commits,
   conversation resolution, review dismissal). Running Allstar's branch-protection
   **fix** action on top would have two controllers reconciling the same settings
   against different definitions — they would fight.

In short, the gap Allstar fills — continuously correcting security-setting
*drift across many repositories in an organization* — does not exist for a single
personal-account repository that already declares its settings as code and has
Scorecard watching for drift. This is a fit decision, not a judgement on Allstar,
which is actively maintained.

!!! note "If cuere ever moves to a GitHub organization"
    Should the project grow into a multi-repository GitHub organization, this
    decision is worth revisiting — Allstar's value (uniform, self-healing policy
    across many repos) appears precisely at that scale. The reconciliation with
    `settings.yml` would then need deciding (scope Allstar to policies
    `settings.yml` does not manage, or hand branch protection to one of them) so
    the two do not fight.
