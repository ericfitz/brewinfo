#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""
Homebrew Package Information Analyzer

This program analyzes installed Homebrew packages and casks, displaying
their dependencies and reverse dependencies in a tabular format.
"""

import subprocess
import json
import sys
import argparse
from typing import Dict, List, Set, Tuple, Optional, TextIO
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class PackageInfo:
    """Data structure to hold package information."""

    name: str
    description: str
    url: str
    build_dependencies: List[str]
    runtime_dependencies: List[str]
    is_cask: bool = False


class BrewAnalyzer:
    """Main class for analyzing Homebrew packages."""

    def __init__(self):
        self.packages: Dict[str, PackageInfo] = {}
        self.reverse_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.installed_packages: Set[str] = set()

    def run_brew_command(self, args: List[str]) -> str:
        """Run a brew command and return its output."""
        try:
            result = subprocess.run(
                ["brew"] + args, capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error running brew {' '.join(args)}: {e}", file=sys.stderr)
            return ""
        except FileNotFoundError:
            print(
                "Error: Homebrew not found. Please install Homebrew first.",
                file=sys.stderr,
            )
            sys.exit(1)

    def get_installed_packages(self) -> List[Tuple[str, bool]]:
        """Get list of all installed packages and casks."""
        # Get regular packages
        packages_output = self.run_brew_command(["list", "--formula"])
        packages = packages_output.split("\n") if packages_output else []

        # Get casks
        casks_output = self.run_brew_command(["list", "--cask"])
        casks = casks_output.split("\n") if casks_output else []

        # Mark casks for later identification
        all_packages = [(pkg, False) for pkg in packages if pkg] + [
            (cask, True) for cask in casks if cask
        ]

        return all_packages

    def parse_brew_info(
        self, package_name: str, is_cask: bool = False
    ) -> Optional[PackageInfo]:
        """Parse brew info output for a package."""
        info_args = ["info", "--json"]
        if is_cask:
            info_args.append("--cask")
        info_args.append(package_name)

        info_output = self.run_brew_command(info_args)
        if not info_output:
            return None

        try:
            info_data = json.loads(info_output)
            if not info_data:
                return None

            pkg_data = info_data[0]

            if is_cask:
                # Handle cask data structure
                description = pkg_data.get("desc", "No description available")
                url = pkg_data.get("homepage", "")
                build_deps = []
                runtime_deps = []
            else:
                # Handle formula data structure
                description = pkg_data.get("desc", "No description available")
                url = pkg_data.get("homepage", "")
                build_deps = pkg_data.get("build_dependencies", [])
                runtime_deps = pkg_data.get("dependencies", [])

            return PackageInfo(
                name=package_name,
                description=description,
                url=url,
                build_dependencies=build_deps,
                runtime_dependencies=runtime_deps,
                is_cask=is_cask,
            )

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"Error parsing info for {package_name}: {e}", file=sys.stderr)
            return None

    def build_reverse_dependencies(self):
        """Build reverse dependency mapping."""
        for pkg_name, pkg_info in self.packages.items():
            # Add reverse dependencies for build dependencies
            for dep in pkg_info.build_dependencies:
                self.reverse_dependencies[dep].add(pkg_name)

            # Add reverse dependencies for runtime dependencies
            for dep in pkg_info.runtime_dependencies:
                self.reverse_dependencies[dep].add(pkg_name)

    def check_dependency_status(self, dep_name: str) -> str:
        """Check if a dependency is installed and return status symbol."""
        if dep_name in self.installed_packages:
            return "✅"  # Green check
        return "❌"  # Red X

    def format_dependencies(self, dependencies: List[str]) -> str:
        """Format dependencies with status indicators."""
        if not dependencies:
            return ""

        formatted_deps = []
        for dep in dependencies:
            status = self.check_dependency_status(dep)
            formatted_deps.append(f"{status} {dep}")

        return ", ".join(formatted_deps)

    def analyze_packages(self):
        """Main method to analyze all packages."""
        print("Getting list of installed packages...")
        installed_list = self.get_installed_packages()

        if not installed_list:
            print("No packages found.")
            return

        # Build set of installed package names for dependency checking
        self.installed_packages = {pkg[0] for pkg in installed_list}

        print(f"Found {len(installed_list)} packages. Analyzing...")

        # Get detailed info for each package
        for i, (package_name, is_cask) in enumerate(installed_list, 1):
            print(f"Analyzing {package_name} ({i}/{len(installed_list)})...", end="\r")
            print("\033[K", end="")  # Clear rest of line

            pkg_info = self.parse_brew_info(package_name, is_cask)
            if pkg_info:
                self.packages[package_name] = pkg_info

        print("\nBuilding dependency relationships...")
        self.build_reverse_dependencies()

        print("Analysis complete!\n")

    def print_table(self, output_file: Optional[TextIO] = None):
        """Print the results in a formatted table."""
        if not self.packages:
            print("No package information available.")
            return

        # Calculate column widths
        max_name_width = max(len(pkg.name) for pkg in self.packages.values())
        max_desc_width = min(
            50, max(len(pkg.description) for pkg in self.packages.values())
        )
        max_reverse_deps_width = 30
        max_build_deps_width = 40
        max_runtime_deps_width = 40

        # Ensure minimum widths
        max_name_width = max(max_name_width, 12)
        max_desc_width = max(max_desc_width, 20)

        # Print header
        header = (
            f"{'Package':<{max_name_width}} | "
            f"{'Description':<{max_desc_width}} | "
            f"{'Used By':<{max_reverse_deps_width}} | "
            f"{'Build Deps':<{max_build_deps_width}} | "
            f"{'Runtime Deps':<{max_runtime_deps_width}}"
        )
        print(header)
        print("-" * len(header))

        if output_file:
            print(header, file=output_file)
            print("-" * len(header), file=output_file)

        # Print package information
        for pkg_name in sorted(self.packages.keys()):
            pkg_info = self.packages[pkg_name]

            # Truncate description if too long
            description = pkg_info.description
            if len(description) > max_desc_width:
                description = description[: max_desc_width - 3] + "..."

            # Format reverse dependencies
            reverse_deps = list(self.reverse_dependencies.get(pkg_name, set()))
            reverse_deps_str = ", ".join(reverse_deps[:3])  # Show first 3
            if len(reverse_deps) > 3:
                reverse_deps_str += f" (+{len(reverse_deps)-3} more)"
            if len(reverse_deps_str) > max_reverse_deps_width:
                reverse_deps_str = (
                    reverse_deps_str[: max_reverse_deps_width - 3] + "..."
                )

            # Format build dependencies
            build_deps_str = self.format_dependencies(pkg_info.build_dependencies)
            if len(build_deps_str) > max_build_deps_width:
                build_deps_str = build_deps_str[: max_build_deps_width - 3] + "..."

            # Format runtime dependencies
            runtime_deps_str = self.format_dependencies(pkg_info.runtime_dependencies)
            if len(runtime_deps_str) > max_runtime_deps_width:
                runtime_deps_str = (
                    runtime_deps_str[: max_runtime_deps_width - 3] + "..."
                )

            # Print row
            row = (
                f"{pkg_name:<{max_name_width}} | "
                f"{description:<{max_desc_width}} | "
                f"{reverse_deps_str:<{max_reverse_deps_width}} | "
                f"{build_deps_str:<{max_build_deps_width}} | "
                f"{runtime_deps_str:<{max_runtime_deps_width}}"
            )
            print(row)

            if output_file:
                print(row, file=output_file)

    def print_summary(self, output_file: Optional[TextIO] = None):
        """Print summary statistics."""
        total_packages = len(self.packages)
        cask_count = sum(1 for pkg in self.packages.values() if pkg.is_cask)
        formula_count = total_packages - cask_count

        total_build_deps = sum(
            len(pkg.build_dependencies) for pkg in self.packages.values()
        )
        total_runtime_deps = sum(
            len(pkg.runtime_dependencies) for pkg in self.packages.values()
        )

        print("\nSummary:")
        print(f"  Total packages: {total_packages}")
        print(f"  Formulas: {formula_count}")
        print(f"  Casks: {cask_count}")
        print(f"  Total build dependencies: {total_build_deps}")
        print(f"  Total runtime dependencies: {total_runtime_deps}")

        if output_file:
            print("\nSummary:", file=output_file)
            print(f"  Total packages: {total_packages}", file=output_file)
            print(f"  Formulas: {formula_count}", file=output_file)
            print(f"  Casks: {cask_count}", file=output_file)
            print(f"  Total build dependencies: {total_build_deps}", file=output_file)
            print(
                f"  Total runtime dependencies: {total_runtime_deps}", file=output_file
            )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze installed Homebrew packages and their dependencies"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file to save the table (in addition to console output)",
    )

    args = parser.parse_args()
    analyzer = BrewAnalyzer()
    output_file = None

    try:
        analyzer.analyze_packages()

        # Handle file output if specified
        if args.output:
            try:
                output_file = open(args.output, "w", encoding="utf-8")
                print(f"Writing output to {args.output}...")
            except IOError as e:
                print(f"Error opening output file {args.output}: {e}", file=sys.stderr)
                sys.exit(1)

        analyzer.print_table(output_file)
        analyzer.print_summary(output_file)

        if output_file:
            output_file.close()
            print(f"Output saved to {args.output}")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        if output_file:
            output_file.close()
        sys.exit(1)
    except (OSError, RuntimeError) as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        if output_file:
            output_file.close()
        sys.exit(1)


if __name__ == "__main__":
    main()
