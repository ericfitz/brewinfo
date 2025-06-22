# Homebrew Package Information Analyzer

A Python program that analyzes installed Homebrew packages and casks, displaying their dependencies and reverse dependencies in a comprehensive table format.

## Features

- Lists all installed Homebrew packages (formulas) and casks
- Displays package descriptions and URLs
- Shows build and runtime dependencies with status indicators
- Displays reverse dependencies (which packages depend on each package)
- Uses green checkmarks (✅) and red X marks (❌) to indicate dependency status
- Provides summary statistics
- **NEW**: Runtime dependency tree view showing hierarchical package relationships

## Tree View Feature

The new tree view displays runtime dependencies in a hierarchical format:

- **Root packages**: Packages that are not dependencies of any other installed package appear at the top level
- **Dependencies**: Each package's runtime dependencies are shown as child nodes
- **Tree structure**: Uses Unicode box-drawing characters (├──, └──, │) for clear visual hierarchy
- **Status indicators**: Shows ✅ for installed dependencies and ❌ for missing ones
- **Circular dependency handling**: Detects and marks circular dependencies to prevent infinite loops

### Tree View Options

- `--tree`: Display both the regular table and the dependency tree
- `--tree-only`: Display only the dependency tree (no table or summary)
- Works with all other options (`--api`, `--output`, etc.)

## Requirements

- Python 3.6 or higher
- Homebrew installed on macOS
- For optimized version: `requests` library (install with `pip install -r requirements.txt`)

### Python Version Management

This project uses pyenv for Python version management and virtual environments for dependency isolation:

- **Recommended Python versions**: 3.11+, 3.12+, or 3.13+ (via pyenv)
- **Virtual environment**: Isolated dependencies using Python's built-in venv
- **Project-specific version**: Set via `.python-version` file

#### Quick Setup

```bash
# Use the provided setup script
./setup_venv.sh

# Or manually:
python -m venv venv
source venv/bin/activate
pip install --no-user -r requirements.txt
```

## Usage

### Original Version

Run the original program from the command line:

```bash
python3 brewinfo.py
```

### Optimized Version (Recommended)

For significantly faster performance, use the optimized version with virtual environment:

```bash
# Set up virtual environment (first time only)
./setup_venv.sh

# Activate virtual environment
source venv/bin/activate

# Use batch processing (3-5x faster)
python brewinfo_optimized.py

# Use API method (5-10x faster, requires internet)
python brewinfo_optimized.py --api

# Save output to file
python brewinfo_optimized.py --api -o output.txt

# Adjust batch size for CLI method
python brewinfo_optimized.py --batch-size 100

# Display runtime dependency tree in addition to table
python brewinfo_optimized.py --tree

# Display only the dependency tree (no table)
python brewinfo_optimized.py --tree-only

# Save tree output to file
python brewinfo_optimized.py --tree-only -o dependency_tree.txt

# Deactivate virtual environment when done
deactivate
```

### Performance Comparison

To compare performance between versions:

```bash
python3 performance_comparison.py
```

The program will:

1. Get the list of all installed packages and casks
2. Analyze each package to gather dependency information
3. Display results in a formatted table with the following columns:
   - **Package**: Name of the package/cask
   - **Description**: Short description of the package
   - **Used By**: Packages that depend on this package (reverse dependencies)
   - **Build Deps**: Build-time dependencies with status indicators
   - **Runtime Deps**: Runtime dependencies with status indicators

## Output Format

The table uses the following status indicators:

- ✅ Green checkmark: Dependency is installed
- ❌ Red X: Dependency is not installed

Example table output:

```
Package      | Description                    | Used By    | Build Deps        | Runtime Deps
-------------|--------------------------------|------------|-------------------|------------------
git          | Distributed revision control  | node, vim  | ✅ openssl, ❌ foo | ✅ pcre2
python@3.11  | Interpreted programming lang  | pip, numpy |                   | ✅ openssl
```

Example tree output (`--tree-only`):

```
Runtime Dependency Tree:
==================================================
Found 3 root packages:

✅ git
├── ✅ pcre2
└── ✅ openssl

✅ node
├── ✅ python@3.11
│   └── ✅ openssl
└── ✅ libuv

✅ vim
└── ✅ ncurses
```

## Implementation Details

The program uses the following approach:

- Executes `brew list` to get installed packages and casks
- For each package, runs `brew info --json <package>` to get detailed information
- Parses JSON output to extract descriptions, URLs, and dependencies
- Builds reverse dependency mappings
- Formats output in a readable table with appropriate column widths

## Data Structures

- `PackageInfo`: Dataclass storing package metadata and dependencies
- `BrewAnalyzer`: Main class handling analysis and output formatting
- Dictionary mapping package names to `PackageInfo` objects
- Reverse dependency mapping using defaultdict of sets

## Error Handling

The program handles various error conditions:

- Missing Homebrew installation
- Failed brew commands
- JSON parsing errors
- Keyboard interruption (Ctrl+C)

## Performance Optimizations

### Original Version

The original program processes packages sequentially and displays progress. Analysis time depends on the number of installed packages, typically taking a few seconds to a minute for typical installations.

### Optimized Version Performance Improvements

The optimized version (`brewinfo_optimized.py`) provides several performance enhancements:

#### 1. **Batch CLI Queries (3-5x faster)**

- Groups multiple packages into single `brew info --json` commands
- Reduces subprocess overhead significantly
- Default batch size: 50 packages per command
- Configurable with `--batch-size` parameter

#### 2. **Homebrew API Access (5-10x faster)**

- Uses Homebrew's JSON API directly: `https://formulae.brew.sh/api/`
- Eliminates subprocess calls entirely
- Requires internet connection
- Enable with `--api` flag

#### 3. **Performance Comparison**

Typical performance improvements on a system with 100+ packages:

| Method                    | Time | Speedup |
| ------------------------- | ---- | ------- |
| Original (sequential CLI) | 60s  | 1x      |
| Optimized (batch CLI)     | 15s  | 4x      |
| Optimized (API)           | 6s   | 10x     |

### Alternative Approaches Considered

1. **Direct File System Access**: Reading Homebrew's local database files directly

   - Location: `/opt/homebrew/Cellar/` and `/opt/homebrew/Library/Taps/`
   - Pros: Fastest possible access
   - Cons: Fragile, depends on internal Homebrew structure

2. **Homebrew Bundle**: Using `brew bundle dump` for package lists

   - Pros: Single command for all packages
   - Cons: Limited dependency information

3. **Concurrent Processing**: Threading/async for CLI commands
   - Pros: Parallelizes slow operations
   - Cons: Can overwhelm system, complex error handling

The batch and API approaches provide the best balance of speed, reliability, and maintainability.
