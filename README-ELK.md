# GxPlugins

Modified for headless plugin build for [Elk Audio OS](https://elk.audio)

## Building Instructions

1. Initialize submodules:
```bash
$ git submodule update --init
```

2. Source the cross-compilation SDK for the target platform:

```bash
$ source [path-to-extracted-sdk]/environment-setup-[aarch-name]-elk-linux
```

1. Run build-elk.sh

All the lv2 bundles will end up in the build-elk/ folder.

