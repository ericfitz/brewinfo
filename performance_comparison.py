#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "requests>=2.25.0",
# ]
# ///
"""
Performance comparison between original and optimized Homebrew analyzers.
"""

import time
import sys
import requests
from brewinfo import BrewAnalyzer
from brewinfo_optimized import OptimizedBrewAnalyzer


def time_analyzer(analyzer_class, name, **kwargs):
    """Time how long it takes to analyze packages."""
    print(f"\n=== Testing {name} ===")

    analyzer = analyzer_class(**kwargs)

    start_time = time.time()
    analyzer.analyze_packages()
    end_time = time.time()

    elapsed = end_time - start_time
    package_count = len(analyzer.packages)

    print(f"{name} Results:")
    print(f"  Time: {elapsed:.2f} seconds")
    print(f"  Packages analyzed: {package_count}")
    print(f"  Rate: {package_count/elapsed:.1f} packages/second")

    return elapsed, package_count


def main():
    """Run performance comparison."""
    print("Homebrew Package Analyzer Performance Comparison")
    print("=" * 50)

    try:
        # Test original version
        original_time, original_count = time_analyzer(BrewAnalyzer, "Original Version")

        # Test optimized batch version
        batch_time, batch_count = time_analyzer(
            OptimizedBrewAnalyzer, "Optimized Batch Version", use_api=False
        )

        # Test API version (if internet available)
        try:
            api_time, api_count = time_analyzer(
                OptimizedBrewAnalyzer, "API Version", use_api=True
            )
        except (requests.RequestException, OSError, RuntimeError) as e:
            print(f"\nAPI version failed: {e}")
            api_time = None
            api_count = None

        # Print comparison
        print("\n" + "=" * 50)
        print("PERFORMANCE COMPARISON")
        print("=" * 50)

        if original_time > 0:
            batch_speedup = original_time / batch_time if batch_time > 0 else 0
            print(f"Batch version is {batch_speedup:.1f}x faster than original")

            if api_time and api_time > 0:
                api_speedup = original_time / api_time
                print(f"API version is {api_speedup:.1f}x faster than original")

                batch_vs_api = batch_time / api_time if api_time > 0 else 0
                print(f"API version is {batch_vs_api:.1f}x faster than batch version")

        print(f"\nOriginal: {original_time:.2f}s for {original_count} packages")
        print(f"Batch:    {batch_time:.2f}s for {batch_count} packages")
        if api_time:
            print(f"API:      {api_time:.2f}s for {api_count} packages")

    except KeyboardInterrupt:
        print("\nComparison cancelled by user.")
        sys.exit(1)
    except (OSError, RuntimeError) as e:
        print(f"Error during comparison: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
