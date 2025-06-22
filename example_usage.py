#!/usr/bin/env python3
"""
Example usage of the Homebrew Package Information Analyzer

This script demonstrates how to use the BrewAnalyzer class programmatically.
"""

from brewinfo import BrewAnalyzer


def main():
    """Example of using BrewAnalyzer programmatically."""
    print("=== Homebrew Package Analysis Example ===\n")

    # Create analyzer instance
    analyzer = BrewAnalyzer()

    # Analyze packages
    print("Starting analysis...")
    analyzer.analyze_packages()

    # Print results
    analyzer.print_table()
    analyzer.print_summary()

    # Example: Access data programmatically
    print("\n=== Programmatic Access Example ===")

    if analyzer.packages:
        # Find packages with the most dependencies
        pkg_with_most_deps = max(
            analyzer.packages.values(),
            key=lambda p: len(p.runtime_dependencies) + len(p.build_dependencies),
        )

        total_deps = len(pkg_with_most_deps.runtime_dependencies) + len(
            pkg_with_most_deps.build_dependencies
        )
        print(
            f"Package with most dependencies: {pkg_with_most_deps.name} ({total_deps} total deps)"
        )

        # Find most depended-upon packages
        if analyzer.reverse_dependencies:
            most_depended = max(
                analyzer.reverse_dependencies.items(), key=lambda x: len(x[1])
            )
            print(
                f"Most depended-upon package: {most_depended[0]} (used by {len(most_depended[1])} packages)"
            )

        # Count casks vs formulas
        cask_count = sum(1 for pkg in analyzer.packages.values() if pkg.is_cask)
        formula_count = len(analyzer.packages) - cask_count
        print(f"Breakdown: {formula_count} formulas, {cask_count} casks")


if __name__ == "__main__":
    main()
