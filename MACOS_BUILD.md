# macOS Build

This project can be built for both major Mac CPU families:

- Apple Silicon (arm64): `Countdown-macOS-Apple-Silicon.zip`
- Intel (x86_64): `Countdown-macOS-Intel.zip`

## Build

1. Add `.github/workflows/build-macos.yml` to the GitHub repository.
2. Commit and push it.
3. For a release, push a tag such as `v1.0.1`, or run the workflow manually.
4. The workflow builds `Countdown.app` on the matching macOS runner.
5. When triggered by a tag, the ZIP files are uploaded automatically to that GitHub Release.

## Install on Mac

Download the ZIP that matches the Mac's processor, extract it, then move
`Countdown.app` to Applications.

The current app is unsigned/not notarized. macOS may show a security warning
on first launch. Apple Developer signing and notarization can be added later
for a polished public release.

## macOS packaging

The workflow uses PyInstaller `--onedir --windowed` to create a `.app` bundle.
This is preferable to a `--onefile --windowed` macOS app bundle for distribution.
