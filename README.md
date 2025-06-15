# DevManager - Development Environment Manager

**Version 0.1.0** | **Professional Development Tool**

DevManager is a sophisticated installer and auto-updater for DevAutomator, providing seamless development environment management with secure token-based authentication and automated update workflows.

## 🚀 **Key Features**

### **Dual Operation Modes**
- **Normal Mode**: Auto-update and DevAutomator launcher for end users
- **Token Mode**: Developer build and release operations

### **Auto-Update System**
- **Self-Update**: Automatic DevManager updates with UAC elevation
- **DevAutomator Management**: Download, install, and launch DevAutomator
- **GitHub Integration**: Real-time version checking and binary downloads

### **Security & Authentication**
- **Token-Based Security**: Secure JWT and compatible token systems
- **One-Time Use**: Prevents token replay attacks
- **Expiration Handling**: Automatic token lifecycle management

### **Installation & Deployment**
- **First-Run Installation**: Automatic installation to Program Files
- **UAC Elevation**: Proper Windows permissions handling
- **Shortcut Creation**: Desktop and Start Menu shortcuts
- **Registry Integration**: Proper Windows registry entries

## 📋 **System Requirements**

- **Operating System**: Windows 10/11 (Primary), macOS, Linux
- **Python**: 3.10+ (for development)
- **Dependencies**: PySide6, PyGitHub, PyInstaller, Cryptography
- **Permissions**: Administrator rights for installation

## 🔧 **Installation**

### **End User Installation**
1. Download `DevManager.exe` from GitHub releases
2. Run the executable (UAC prompt will appear)
3. DevManager installs to `C:\Program Files\DevManager\`
4. Desktop and Start Menu shortcuts are created

### **Developer Setup**
```bash
# Clone repository
git clone https://github.com/cyberionsoft/css_dev_manager.git
cd css_dev_manager

# Install dependencies with UV
uv sync

# Run in development mode
python main.py
```

## 🎯 **Usage**

### **Normal Mode (End Users)**
```bash
# Double-click DevManager.exe or run:
DevManager.exe
```

**Workflow:**
1. **Self-Update Check**: Checks for DevManager updates
2. **DevAutomator Update**: Checks and updates DevAutomator
3. **Token Generation**: Creates secure authentication token
4. **Launch DevAutomator**: Starts DevAutomator with token
5. **Exit**: DevManager exits after successful launch

### **Token Mode (Developers)**
```bash
# Start with developer token:
DevManager.exe --token <developer_token>
```

**Available Operations:**
- **Build and Upload DevManager**: Complete build and GitHub release
- **Build and Upload DevAutomator**: DevAutomator build and release

## 🏗️ **Architecture**

### **Core Components**
```
src/
├── main.py                 # Main entry point and CLI handling
├── gui.py                  # PySide6 GUI for both modes
├── updater.py              # Self-update and DevAutomator update logic
├── github_client.py        # GitHub API integration
├── token_handler*.py       # JWT and compatible token systems
├── installer/              # Installation and UAC handling
└── common/                 # Constants and utilities
```

### **Build System**
```
scripts/
├── build_devmanager.py    # DevManager build automation
├── build_devautomator.py  # DevAutomator build automation
└── self_update.py         # Self-update script template
```

## 🔐 **Security Features**

### **Token Authentication**
- **JWT Tokens**: RS256 signed tokens for developer operations
- **Compatible Tokens**: SHA-256 hashed tokens for DevAutomator
- **Expiration**: 24-hour token lifetime
- **One-Time Use**: Prevents token reuse attacks

### **Update Security**
- **SHA-256 Verification**: Binary integrity checking
- **GitHub Releases**: Official release channel only
- **UAC Elevation**: Proper Windows security model

## 🔄 **Update Workflow**

### **Self-Update Process**
1. **Version Check**: Compare local vs GitHub latest
2. **Download**: Secure binary download with verification
3. **Update Script**: Separate process handles file replacement
4. **Restart**: Automatic restart with new version

### **DevAutomator Update**
1. **Process Termination**: Stop running DevAutomator instances
2. **Download & Extract**: Update DevAutomator binaries
3. **Token Launch**: Start updated DevAutomator with fresh token

## 🛠️ **Development**

### **Building**
```bash
# Build DevManager for all platforms
python scripts/build_devmanager.py --version 1.0.0

# Build and release to GitHub
python scripts/build_devmanager.py --version 1.0.0 --github-token <token>

# Build specific platform only
python scripts/build_devmanager.py --version 1.0.0 --platforms windows
```

### **Testing**
```bash
# Run comprehensive tests
python -m pytest tests/ -v

# Test specific components
python -m pytest tests/test_updater.py -v
```

### **Code Quality**
```bash
# Format and lint code
ruff format .
ruff check . --fix

# Type checking
mypy src/
```

## 📊 **Performance**

- **Startup Time**: < 2 seconds
- **Update Check**: < 5 seconds
- **Binary Size**: ~56 MB (cross-platform)
- **Memory Usage**: ~50 MB runtime

## 🔗 **Integration**

### **DevAutomator Communication**
- **Token Passing**: Secure command-line token transfer
- **Process Management**: Start/stop coordination
- **Status Monitoring**: Real-time operation feedback

### **GitHub Integration**
- **Repository**: `cyberionsoft/css_dev_manager`
- **Releases**: Automated release creation and asset upload
- **Version Management**: Semantic versioning with Git tags

## 📝 **Configuration**

### **Constants** (`src/common/constants.py`)
```python
# GitHub Configuration
GITHUB_TOKEN = "your_github_token_here"
DEVMANAGER_REPO = "cyberionsoft/css_dev_manager"
DEVAUTOMATOR_REPO = "cyberionsoft/css_dev_automator"

# Installation Paths
INSTALL_DIR = "C:/Program Files/DevManager/"
DEVAUTOMATOR_INSTALL_DIR = "C:/Program Files/DevManager/"
```

## 🚨 **Troubleshooting**

### **Common Issues**

**Installation Fails**
- Ensure administrator privileges
- Check Windows Defender exclusions
- Verify disk space availability

**Update Fails**
- Check internet connectivity
- Verify GitHub API access
- Review Windows firewall settings

**DevAutomator Won't Start**
- Verify token generation
- Check DevAutomator installation
- Review process permissions

### **Logs**
- **Location**: `%APPDATA%/DevManager/logs/`
- **Levels**: DEBUG, INFO, WARNING, ERROR
- **Rotation**: Daily log files with cleanup

## 🤝 **Contributing**

1. **Fork** the repository
2. **Create** feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** changes (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Open** Pull Request

## 📄 **License**

This project is proprietary software developed by CSS Development Team.

## 📞 **Support**

- **Issues**: [GitHub Issues](https://github.com/cyberionsoft/css_dev_manager/issues)
- **Documentation**: [Wiki](https://github.com/cyberionsoft/css_dev_manager/wiki)
- **Contact**: CSS Development Team

---

**DevManager** - *Streamlining Development Workflows Since 2025*
