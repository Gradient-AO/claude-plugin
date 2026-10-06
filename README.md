# GradientCIO plugins for Claude

Public plugin marketplace for [GradientCIO](https://gradientcio.com) clients.

## Install

Pick the option that matches how you use Claude. Every option installs the same **gradient-cio** plugin from this repository: `Gradient-AO/claude-plugin`.

### For your whole organization (Team and Enterprise admins) — recommended

1. In Claude, open **Organization settings → Plugins & skills → Add**.
2. Add this repository, `Gradient-AO/claude-plugin`, as a marketplace. If your settings only accept a GitHub repository your organization owns, fork or mirror this repository into your GitHub organization and add that copy instead (keep it in sync to receive updates).
3. Turn on **auto-sync** (auto-update) and enable **gradient-cio** for your members.

Members then get the plugin, and every new version, without doing anything.

### Claude desktop (Cowork), for yourself

**Customize → Plugins → Add marketplace →** `Gradient-AO/claude-plugin`, then install **gradient-cio**.

### Claude Code

```
/plugin marketplace add Gradient-AO/claude-plugin
/plugin install gradient-cio@gradientcio
```

### After installing (everyone)

1. Sign in to the **GradientCIO** connector once when Claude asks. Your GradientCIO account decides which data and modules you can use.
2. Ask Claude to run **gradient-setup**. It checks your connection and licensed modules and shows which Gradient skills are ready.

## Updates

New versions are published to this repository; see [CHANGELOG.md](CHANGELOG.md). How you receive them depends on how you installed:

| Installed through | How updates arrive |
|---|---|
| Organization settings | Automatically, with auto-sync on |
| Claude desktop (Cowork) | Update the marketplace from **Customize → Plugins** |
| Claude Code | Turn on auto-update once: `/plugin` → **Marketplaces** → **gradientcio** → **Enable auto-update**. New versions then install at startup (run `/reload-plugins` to apply mid-session). To update by hand: `/plugin marketplace update gradientcio` |

Changes to the GradientCIO connector itself reach you immediately and need no plugin update.

## What's included

See [plugins/gradient-cio/README.md](plugins/gradient-cio/README.md) and [CHANGELOG.md](CHANGELOG.md).

## License

Apache-2.0 (see [LICENSE](LICENSE) and [NOTICE](NOTICE)). The license does not cover the GradientCIO name, logo or report design.

Privacy: [GradientCIO Privacy Policy](https://www.gradientcio.com/home/privacy)

Questions: support@gradientcio.com
