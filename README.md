# Homebrew Package Information Analyzer

A Python program that analyzes installed Homebrew packages and casks, displaying their dependencies and reverse dependencies in a comprehensive table format.

## Features

- Lists all installed Homebrew packages (formulas) and casks
- Displays package descriptions and URLs
- Shows build and runtime dependencies with status indicators
- Displays reverse dependencies (which packages depend on each package)
- Uses green checkmarks (✅) and red X marks (❌) to indicate dependency status
- Provides summary statistics

## Requirements

- Python 3.6 or higher
- Homebrew installed on macOS
- No external Python dependencies required

## Usage

Run the program from the command line:

```bash
python3 brewinfo.py
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

Example output:

```
Package      | Description                    | Used By    | Build Deps        | Runtime Deps
-------------|--------------------------------|------------|-------------------|------------------
git          | Distributed revision control  | node, vim  | ✅ openssl, ❌ foo | ✅ pcre2
python@3.11  | Interpreted programming lang  | pip, numpy |                   | ✅ openssl
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

## Performance

The program processes packages sequentially and displays progress. Analysis time depends on the number of installed packages, typically taking a few seconds to a minute for typical installations.
