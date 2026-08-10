# Microsoft Store Publishing Guide

This guide is for publishing Twality GeoStamp Pro 1.0 as a free Windows desktop app.
Review the latest Microsoft Partner Center screens before final submission, because
Store requirements can change.

## 1. Choose the Submission Path

For this current PySide6 desktop build, the practical path is the Microsoft Store
MSI/EXE submission path:

- Build the app with PyInstaller.
- Build an Inno Setup offline installer.
- Code-sign the installer and installed executable files.
- Host the versioned installer at a stable HTTPS URL.
- Submit the hosted installer URL in Partner Center.

Microsoft also recommends MSIX for many new Windows apps because Microsoft hosts and
re-signs MSIX packages. Consider a future MSIX packaging pass if you want Store-managed
updates and less installer hosting infrastructure.

## 2. Pre-Submission Checklist

- Product name: `Twality GeoStamp Pro`
- Version: `1.0.0`
- Publisher: `Twality Digital Solutions LLP`
- Website/support URL: `https://www.twality.com`
- Pricing: Free
- Architecture: x64, unless additional builds are created
- Installer type: EXE
- Installer silent parameters for Inno Setup: `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART`
- Privacy policy URL: host `PRIVACY.md` content on `https://www.twality.com`
- License/EULA: `LICENSE.txt`
- Third-party notices: `THIRD_PARTY_NOTICES.md`
- Store listing draft: `STORE_LISTING_DRAFT.md`
- Icon: `Logo.ico`

## 3. Build the App

From `windows-app`:

```powershell
.\.venv\Scripts\Activate.ps1
pyinstaller installer\TwalityGeoStamp.spec
```

Expected output:

```text
dist\TwalityGeoStamp\TwalityGeoStamp.exe
```

## 4. Test the App Build

Run:

```powershell
.\dist\TwalityGeoStamp\TwalityGeoStamp.exe
```

Verify:

- Window title is `Twality GeoStamp Pro`.
- `Logo.ico` appears in the title bar/taskbar.
- Settings, logs, and cache files are written under the user's LocalAppData folder, not under Program Files.
- Help > About shows the correct product/company/website.
- Help > Help Contents opens correctly.
- Preview First Image works.
- Batch processing creates stamped copies.
- JPEG metadata restore works when ExifTool is available on PATH.

## 5. Build the Installer

Install Inno Setup, then run from `windows-app`:

```powershell
iscc installer\TwalityGeoStamp.iss
```

Expected output:

```text
installer\TwalityGeoStampProSetup.exe
```

## 6. Test Silent Install and Uninstall

Microsoft Store EXE submissions require silent installer parameters. Test them before
submission:

```powershell
.\installer\TwalityGeoStampProSetup.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
```

Then verify the app launches from:

```text
%ProgramFiles%\Twality GeoStamp Pro\TwalityGeoStamp.exe
```

Test uninstall from Windows Settings > Apps, or use the generated uninstaller in the
install directory.

## 7. Code Signing

For the MSI/EXE Store path, sign the installer and any installed executable files with
a certificate that chains to the Microsoft Trusted Root Program. Self-signed
certificates are not suitable for this submission path.

The locally built artifacts are not signed unless you run your signing process after
the build.

Typical signing targets:

- `dist\TwalityGeoStamp\TwalityGeoStamp.exe`
- `installer\TwalityGeoStampProSetup.exe`
- any other `.exe` or `.dll` files you distribute, if your signing policy requires it

## 8. Host the Installer

Upload the final signed installer to a versioned HTTPS URL, for example:

```text
https://www.twality.com/downloads/twality-geostamp-pro/1.0.0/TwalityGeoStampProSetup.exe
```

Do not replace the binary at that URL after submitting it. For updates, publish a new
versioned URL and create a Store update submission.

## 9. Create the Partner Center Submission

1. Sign in to Partner Center.
2. Create or select the Windows app product.
3. Reserve the name `Twality GeoStamp Pro`.
4. Start a new submission.
5. Complete product properties, category, pricing, markets, age rating, and support
   details.
6. Add the privacy policy URL hosted on the Twality website.
7. Add Store listing metadata from `STORE_LISTING_DRAFT.md`.
8. Upload screenshots and any required Store artwork.
9. On the Packages page, add the hosted HTTPS installer URL.
10. Select architecture, app type `EXE`, and silent installer parameters.
11. Save the draft and run certification checks.
12. Submit for certification.

## 10. Suggested Store Assets

Prepare these before submission:

- App icon from `Logo.ico`.
- Screenshots of the main window, watermark settings, preview, and Help/About.
- Short description and full description from `STORE_LISTING_DRAFT.md`.
- Privacy policy HTTPS URL.
- Support/contact HTTPS URL.

## 11. Operational Notes

- Keep a copy of every submitted installer binary.
- Keep `APP_VERSION`, installer `AppVersion`, and hosted URL version aligned.
- Keep the privacy policy up to date as features change.
- Retest silent install before every submission.
