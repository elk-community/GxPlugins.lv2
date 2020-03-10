# GxPlugins

Modified for headless plugin build for [Elk Audio OS](https://elk.audio)

## Building Instructions

1. Initialize submodules:
```bash
$ git submodule update --init
```

2. Apply the patch to fix Makefiles in submodules:
```bash
$ ./apply-patch
```

The patch might fail for some subprojects, in that case fix manually. Hopefully it will mainstreamed in Gx repositories so it won't be needed

3. Build and install locally the .lv2 packages with:
```bash
$ make mod
$ make install
```
