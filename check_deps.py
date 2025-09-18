#!/usr/bin/env python3
"""
Check dependencies of neo-api-client to understand exact requirements
This script creates a temporary virtual environment to avoid polluting the main environment
"""
import subprocess
import sys
import tempfile
import os

def run_in_venv():
    """Create a temporary venv and check neo-api-client dependencies"""
    print("🔍 Creating temporary virtual environment...")

    # Create a temporary directory for the venv
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = os.path.join(tmpdir, "temp_check_venv")

        try:
            # Create virtual environment
            print(f"📁 Creating venv at: {venv_path}")
            subprocess.run([sys.executable, "-m", "venv", venv_path],
                         check=True, capture_output=True)

            # Determine paths based on OS
            if os.name == 'nt':  # Windows
                pip_path = os.path.join(venv_path, "Scripts", "pip")
                python_path = os.path.join(venv_path, "Scripts", "python")
            else:  # Unix/Linux/Mac
                pip_path = os.path.join(venv_path, "bin", "pip")
                python_path = os.path.join(venv_path, "bin", "python")

            print("⬆️  Upgrading pip in venv...")
            subprocess.run([python_path, "-m", "pip", "install", "--upgrade", "pip"],
                         check=True, capture_output=True)

            print("📦 Installing neo-api-client in isolated venv...")
            install_result = subprocess.run([
                pip_path, "install",
                "git+https://github.com/Kotak-Neo/Kotak-neo-api-v2.git#egg=neo_api_client"
            ], capture_output=True, text=True)

            if install_result.returncode != 0:
                print(f"❌ Installation failed:")
                print(f"STDERR: {install_result.stderr}")
                return

            print("✅ Installation successful!")
            print("📋 Getting dependency list...")

            # Get list of installed packages
            list_result = subprocess.run([pip_path, "list"],
                                       capture_output=True, text=True, check=True)

            print("\n" + "="*50)
            print("📦 NEO-API-CLIENT DEPENDENCIES")
            print("="*50)

            # Parse output
            lines = list_result.stdout.strip().split('\n')
            deps = {}

            for line in lines:
                line = line.strip()
                if line and not line.startswith('Package') and not line.startswith('---'):
                    parts = line.split()
                    if len(parts) >= 2:
                        deps[parts[0]] = parts[1]

            # Show critical dependencies first
            critical_deps = ['neo-api-client', 'numpy', 'pandas', 'websockets', 'python-dotenv']
            print("\n🎯 CRITICAL DEPENDENCIES:")
            for dep in critical_deps:
                if dep in deps:
                    print(f"  {dep}=={deps[dep]}")

            print(f"\n📦 ALL DEPENDENCIES ({len(deps)} total):")
            for name, version in sorted(deps.items()):
                print(f"  {name}=={version}")

            # Generate compatible requirements.txt
            print("\n" + "="*50)
            print("🔧 SUGGESTED REQUIREMENTS.TXT")
            print("="*50)

            # Core dependencies with exact versions from neo-api-client
            suggested_reqs = [
                f"numpy=={deps.get('numpy', '2.1.0')}",
                f"pandas=={deps.get('pandas', '2.2.3')}",
                f"websockets=={deps.get('websockets', '8.1')}",
                f"python-dotenv=={deps.get('python-dotenv', '1.0.0')}",
                "fastapi>=0.100.0,<0.105.0",  # Compatible with older ecosystem
                "uvicorn>=0.18.0,<0.20.0",    # Compatible with websockets 8.1
                "sqlalchemy>=2.0.0,<2.1.0",
                "asyncpg>=0.28.0,<0.30.0",
                "python-multipart>=0.0.5,<0.1.0",
                "pydantic>=1.10.0,<2.0.0",    # Avoid v2 breaking changes
                "pyotp>=2.8.0,<3.0.0",
                "qrcode[pil]>=7.0.0,<8.0.0",
                "jinja2>=3.1.0,<4.0.0",
                "aiofiles>=23.0.0,<24.0.0",
                "git+https://github.com/Kotak-Neo/Kotak-neo-api-v2.git#egg=neo_api_client"
            ]

            for req in suggested_reqs:
                print(req)

        except subprocess.CalledProcessError as e:
            print(f"❌ Error during execution: {e}")
            if hasattr(e, 'stdout') and e.stdout:
                print(f"STDOUT: {e.stdout}")
            if hasattr(e, 'stderr') and e.stderr:
                print(f"STDERR: {e.stderr}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("🚀 Starting dependency check...")
    print("This script will create a temporary virtual environment")
    print("and install neo-api-client to check its exact dependencies.\n")

    run_in_venv()

    print("\n✅ Dependency check complete!")
    print("The temporary virtual environment has been automatically cleaned up.")