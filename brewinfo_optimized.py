#!/usr/bin/env python3
"""
Optimized Homebrew Package Information Analyzer

This version uses batch queries and other optimizations to significantly
improve performance over the original command-by-command approach.
"""

import subprocess
import json
import sys
import argparse
import time
from typing import Dict, List, Set, Tuple, Optional, TextIO
from dataclasses import dataclass
from collections import defaultdict

import requests


@dataclass
class PackageInfo:
    """Data structure to hold package information."""

    name: str
    description: str
    url: str
    build_dependencies: List[str]
    runtime_dependencies: List[str]
    is_cask: bool = False


class OptimizedBrewAnalyzer:
    """Optimized analyzer for Homebrew packages."""

    def __init__(self, use_api: bool = False, batch_size: int = 50):
        self.packages: Dict[str, PackageInfo] = {}
        self.reverse_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.installed_packages: Set[str] = set()
        self.use_api = use_api
        self.batch_size = batch_size
        self._api_cache = {}

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

    def fetch_api_data(self) -> Tuple[Dict, Dict]:
        """Fetch formula and cask data from Homebrew API."""
        if self._api_cache:
            return self._api_cache["formulas"], self._api_cache["casks"]

        print("Fetching data from Homebrew API...")

        try:
            # Fetch formulas
            formula_response = requests.get(
                "https://formulae.brew.sh/api/formula.json", timeout=30
            )
            formula_response.raise_for_status()
            formulas = {f["name"]: f for f in formula_response.json()}

            # Fetch casks
            cask_response = requests.get(
                "https://formulae.brew.sh/api/cask.json", timeout=30
            )
            cask_response.raise_for_status()
            casks = {c["token"]: c for c in cask_response.json()}

            self._api_cache = {"formulas": formulas, "casks": casks}
            return formulas, casks

        except requests.RequestException as e:
            print(f"Error fetching API data: {e}", file=sys.stderr)
            print("Falling back to CLI method...", file=sys.stderr)
            return {}, {}

    def parse_api_data(
        self, package_name: str, is_cask: bool, formulas: Dict, casks: Dict
    ) -> Optional[PackageInfo]:
        """Parse package info from API data."""
        try:
            if is_cask:
                if package_name not in casks:
                    return None
                pkg_data = casks[package_name]
                description = pkg_data.get("desc", "No description available")
                url = pkg_data.get("homepage", "")
                build_deps = []
                runtime_deps = []
            else:
                if package_name not in formulas:
                    return None
                pkg_data = formulas[package_name]
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

        except (KeyError, IndexError) as e:
            print(f"Error parsing API data for {package_name}: {e}", file=sys.stderr)
            return None

    def parse_brew_info_batch(  # pylint: disable=too-many-branches
        self, packages: List[Tuple[str, bool]]
    ) -> List[Optional[PackageInfo]]:
        """Parse brew info output for multiple packages at once."""
        if not packages:
            return []

        # Separate formulas and casks
        formulas = [pkg[0] for pkg in packages if not pkg[1]]
        casks = [pkg[0] for pkg in packages if pkg[1]]

        results = []

        # Process formulas in batch
        if formulas:
            info_args = ["info", "--json"] + formulas
            info_output = self.run_brew_command(info_args)

            if info_output:
                try:
                    info_data = json.loads(info_output)
                    formula_data = {pkg["name"]: pkg for pkg in info_data}

                    for formula_name in formulas:
                        if formula_name in formula_data:
                            pkg_data = formula_data[formula_name]
                            results.append(
                                PackageInfo(
                                    name=formula_name,
                                    description=pkg_data.get(
                                        "desc", "No description available"
                                    ),
                                    url=pkg_data.get("homepage", ""),
                                    build_dependencies=pkg_data.get(
                                        "build_dependencies", []
                                    ),
                                    runtime_dependencies=pkg_data.get(
                                        "dependencies", []
                                    ),
                                    is_cask=False,
                                )
                            )
                        else:
                            results.append(None)
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Error parsing batch formula info: {e}", file=sys.stderr)
                    results.extend([None] * len(formulas))
            else:
                results.extend([None] * len(formulas))

        # Process casks in batch
        if casks:
            info_args = ["info", "--json", "--cask"] + casks
            info_output = self.run_brew_command(info_args)

            if info_output:
                try:
                    info_data = json.loads(info_output)
                    cask_data = {pkg["token"]: pkg for pkg in info_data}

                    for cask_name in casks:
                        if cask_name in cask_data:
                            pkg_data = cask_data[cask_name]
                            results.append(
                                PackageInfo(
                                    name=cask_name,
                                    description=pkg_data.get(
                                        "desc", "No description available"
                                    ),
                                    url=pkg_data.get("homepage", ""),
                                    build_dependencies=[],
                                    runtime_dependencies=[],
                                    is_cask=True,
                                )
                            )
                        else:
                            results.append(None)
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Error parsing batch cask info: {e}", file=sys.stderr)
                    results.extend([None] * len(casks))
            else:
                results.extend([None] * len(casks))

        return results

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
        """Main method to analyze all packages with optimizations."""
        start_time = time.time()

        print("Getting list of installed packages...")
        installed_list = self.get_installed_packages()

        if not installed_list:
            print("No packages found.")
            return

        # Build set of installed package names for dependency checking
        self.installed_packages = {pkg[0] for pkg in installed_list}

        print(f"Found {len(installed_list)} packages. Analyzing...")

        if self.use_api:
            # Use API method
            formulas, casks = self.fetch_api_data()

            if formulas or casks:
                print("Using API data for faster analysis...")
                for package_name, is_cask in installed_list:
                    pkg_info = self.parse_api_data(
                        package_name, is_cask, formulas, casks
                    )
                    if pkg_info:
                        self.packages[package_name] = pkg_info
            else:
                print("API unavailable, falling back to batch CLI method...")
                self.use_api = False

        if not self.use_api:
            # Use optimized batch CLI method
            print("Using batch CLI queries for faster analysis...")

            # Process packages in batches
            for i in range(0, len(installed_list), self.batch_size):
                batch = installed_list[i : i + self.batch_size]
                batch_end = min(i + self.batch_size, len(installed_list))

                batch_num = i // self.batch_size + 1
                total_packages = len(installed_list)
                print(
                    f"Processing batch {batch_num} ({i+1}-{batch_end}/{total_packages})...",
                    end="\r",
                )
                print("\033[K", end="")  # Clear rest of line

                batch_results = self.parse_brew_info_batch(batch)

                for (package_name, _), pkg_info in zip(batch, batch_results):
                    if pkg_info:
                        self.packages[package_name] = pkg_info

        print("\nBuilding dependency relationships...")
        self.build_reverse_dependencies()

        elapsed_time = time.time() - start_time
        print(f"Analysis complete in {elapsed_time:.2f} seconds!\n")

    def print_table(
        self, output_file: Optional[TextIO] = None
    ):  # pylint: disable=too-many-locals
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
        description=(
            "Analyze installed Homebrew packages and their dependencies "
            "(optimized version)"
        )
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file to save the table (in addition to console output)",
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="Use Homebrew API for fastest performance (requires internet)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Batch size for CLI queries (default: 50)",
    )

    args = parser.parse_args()
    analyzer = OptimizedBrewAnalyzer(use_api=args.api, batch_size=args.batch_size)
    output_file = None

    try:
        analyzer.analyze_packages()

        # Handle file output if specified
        if args.output:
            try:
                with open(args.output, "w", encoding="utf-8") as output_file:
                    print(f"Writing output to {args.output}...")
                    analyzer.print_table(output_file)
                    analyzer.print_summary(output_file)
                print(f"Output saved to {args.output}")
            except IOError as e:
                print(f"Error opening output file {args.output}: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            analyzer.print_table()
            analyzer.print_summary()

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
