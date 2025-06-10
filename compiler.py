import os
import subprocess
import sys
import shutil
import datetime

def create_version_file(build_dir):
    """Create a version file for the executable."""
    version_info = {
        'version': '1.0.0',
        'company_name': 'HAdesk',
        'file_description': 'HAdesk integration for Home Assistant - Integrate your Windows machine with Home Assistant',
        'internal_name': 'HAdesk',
        'legal_copyright': f'© {datetime.datetime.now().year} HAdesk',
        'original_filename': 'HAdesk.exe',
        'product_name': 'HAdesk'
    }
    
    version_file = os.path.join(build_dir, 'version.txt')
    with open(version_file, 'w') as f:
        f.write(f"""
# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers=({version_info['version'].replace('.', ', ')}, 0),
    prodvers=({version_info['version'].replace('.', ', ')}, 0),
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x40004,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'{version_info["company_name"]}'),
        StringStruct(u'FileDescription', u'{version_info["file_description"]}'),
        StringStruct(u'FileVersion', u'{version_info["version"]}'),
        StringStruct(u'InternalName', u'{version_info["internal_name"]}'),
        StringStruct(u'LegalCopyright', u'{version_info["legal_copyright"]}'),
        StringStruct(u'OriginalFilename', u'{version_info["original_filename"]}'),
        StringStruct(u'ProductName', u'{version_info["product_name"]}'),
        StringStruct(u'ProductVersion', u'{version_info["version"]}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
""")
    return version_file

def install_pyinstaller():
    """Install PyInstaller if not already installed."""
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def compile_executable():
    """Compile the application into an executable."""
    print("Starting compilation process...")
    
    # Ensure we're in the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Create build directory
    build_dir = os.path.join(script_dir, 'build')
    os.makedirs(build_dir, exist_ok=True)
    
    # Clean up only the work and dist subdirectories
    work_dir = os.path.join(build_dir, "work")
    dist_dir = os.path.join(build_dir, "dist")
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    
    # Create version file
    version_file = create_version_file(build_dir)
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--name=HAdesk",
        "--onefile",
        "--noconsole",  # No console window
        "--clean",
        "--version-file", version_file,
        "--workpath", work_dir,
        "--distpath", dist_dir,
        "--specpath", build_dir,
        "ha_desk.py"
    ]
    
    # Add icon if it exists, otherwise create it
    icon_path = os.path.join(build_dir, "icon.ico")
    if os.path.exists(icon_path):
        cmd.extend(["--icon", icon_path])
    else:
        print("Icon not found, creating it automatically...")
        import create_icon
        create_icon.create_icon()
        cmd.extend(["--icon", icon_path])
    
    # Add data files if needed
    cmd.extend([
        "--add-data", "requirements.txt;.",
    ])
    
    # Run PyInstaller
    subprocess.check_call(cmd)
    
    print("\nCompilation completed!")
    print(f"Executable can be found in: {os.path.join(dist_dir, 'HAdesk.exe')}")

if __name__ == "__main__":
    install_pyinstaller()
    compile_executable() 