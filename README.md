# GradientCIO plugins for Claude

Public plugin marketplace for [GradientCIO](https://gradientcio.com) clients.

## Install

**Claude desktop (Cowork):** Customize → Plugins → Add marketplace → `Gradient-AO/claude-plugin`, then install **gradient-cio**.

**Claude Code:**

```
/plugin marketplace add Gradient-AO/claude-plugin
/plugin install gradient-cio@gradientcio
```

After installing, sign in to the **GradientCIO** connector once, then run the **gradient-setup** skill to confirm access.

## Updates

New versions are published to this repository.

- **Claude Code:** turn on automatic updates once: `/plugin` → **Marketplaces** → **gradientcio** → **Enable auto-update**. New versions then install at startup (run `/reload-plugins` to apply mid-session). To update by hand: `/plugin marketplace update gradientcio`.
- **Claude desktop (Cowork):** update the marketplace from Customize → Plugins.
- **Team and Enterprise admins:** add the marketplace for everyone in Organization settings with auto-update on and **gradient-cio** enabled, so users never need to update manually.

Changes to the GradientCIO connector itself reach you immediately and need no plugin update.

## What's included

See [plugins/gradient-cio/README.md](plugins/gradient-cio/README.md) and [CHANGELOG.md](CHANGELOG.md).

## License

Apache-2.0 (see [LICENSE](LICENSE) and [NOTICE](NOTICE)). The license does not cover the GradientCIO name, logo or report design.

Privacy: [GradientCIO Privacy Policy](https://www.gradientcio.com/home/privacy)

Questions: support@gradientcio.com
