import zipfile

z = zipfile.ZipFile("code.zip")
print(f"Total files: {len(z.namelist())}")
forbidden = [f for f in z.namelist() if any(bad in f for bad in ["dataset/", ".git", "__pycache__", ".venv", ".env", ".zip"])]
print(f"Forbidden entries: {len(forbidden)}")
for f in sorted(z.namelist()):
    info = z.getinfo(f)
    print(f"  {f} ({info.file_size} bytes)")
