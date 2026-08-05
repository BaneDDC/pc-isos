#!/usr/bin/env python3
"""
manifest_gen.py - Boot Sector Disk Image Manifest Generator
Run this script in the folder containing your .img files.
It will produce a manifest.json you can commit to your GitHub repo.

Usage:
  python3 manifest_gen.py

Output:
  manifest.json  (commit this alongside your .img files)

Then provide Astra with the single raw GitHub URL to manifest.json,
e.g.: https://raw.githubusercontent.com/USER/REPO/main/manifest.json
"""

import os
import json
import hashlib

DRIVES = {
    "HDD0": None,
    "HDD1": None,
    "HDD2": None,
    "HDD3": None,
    "CDROM": None,
    "FDD0": None,
}

EXTENSIONS = [".img", ".iso", ".ima", ".bin"]

def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def scan():
    found = []
    for fname in sorted(os.listdir(".")):
        ext = os.path.splitext(fname)[1].lower()
        if ext in EXTENSIONS:
            size = os.path.getsize(fname)
            checksum = md5(fname)
            found.append({
                "file": fname,
                "size_bytes": size,
                "md5": checksum,
                "drive": None  # assign below
            })
    return found

def auto_assign(images):
    """
    Auto-assign drive type based on file size:
      - <= 1,474,560 bytes (1.44MB) -> FDD0 (floppy)
      - <= 737,280,000 bytes (~700MB) -> CDROM
      - > 700MB -> HDD0, HDD1, HDD2, HDD3
    """
    FLOPPY_MAX = 1_474_560        # 1.44 MB
    CDROM_MAX = 737_280_000       # ~700 MB

    floppy_imgs = []
    cdrom_imgs = []
    hdd_imgs = []

    for img in sorted(images, key=lambda x: x["size_bytes"]):
        if img["size_bytes"] <= FLOPPY_MAX:
            floppy_imgs.append(img)
        elif img["size_bytes"] <= CDROM_MAX:
            cdrom_imgs.append(img)
        else:
            hdd_imgs.append(img)

    # Assign floppy (only 1 slot)
    for i, img in enumerate(floppy_imgs):
        img["drive"] = f"FDD{i}" if i == 0 else f"HDD{len(hdd_imgs)}"
        if i > 0:
            hdd_imgs.append(img)  # overflow to HDD

    # Assign CD-ROM (only 1 slot)
    for i, img in enumerate(cdrom_imgs):
        if i == 0:
            img["drive"] = "CDROM"
        else:
            img["drive"] = f"HDD{len(hdd_imgs)}"
            hdd_imgs.append(img)  # overflow to HDD

    # Assign HDDs (up to 4)
    for i, img in enumerate(hdd_imgs):
        if i < 4:
            img["drive"] = f"HDD{i}"
        else:
            img["drive"] = f"HDD_OVERFLOW_{i}"

    return images

def main():
    images = scan()
    if not images:
        print("No disk image files found in current directory.")
        return

    images = auto_assign(images)

    manifest = {
        "version": "1.0",
        "generated_by": "manifest_gen.py",
        "base_url": "",  # <-- Set this to your raw GitHub base URL
                         # e.g. https://raw.githubusercontent.com/USER/REPO/main/disks/
        "disks": images
    }

    with open("manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"manifest.json written with {len(images)} disk image(s):")
    for img in images:
        print(f"  [{img['drive']}] {img['file']}  ({img['size_bytes']} bytes)")

    print()
    print("NEXT STEPS:")
    print("  1. Edit manifest.json and set 'base_url' to the raw GitHub")
    print("     URL of the folder containing your .img files.")
    print("  2. Commit manifest.json and all .img files to your repo.")
    print("  3. Give Astra the raw URL to manifest.json.")

if __name__ == "__main__":
    main()
