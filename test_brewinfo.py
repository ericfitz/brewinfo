#!/usr/bin/env python3
"""
Test script for brewinfo.py

This script tests the core functionality of the Homebrew analyzer.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
from brewinfo import BrewAnalyzer, PackageInfo


class TestBrewAnalyzer(unittest.TestCase):
    """Test cases for BrewAnalyzer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = BrewAnalyzer()

    def test_package_info_creation(self):
        """Test PackageInfo dataclass creation."""
        pkg = PackageInfo(
            name="test-package",
            description="Test package description",
            url="https://example.com",
            build_dependencies=["cmake", "pkgconf"],
            runtime_dependencies=["openssl", "zlib"],
            is_cask=False,
        )

        self.assertEqual(pkg.name, "test-package")
        self.assertEqual(pkg.description, "Test package description")
        self.assertEqual(pkg.url, "https://example.com")
        self.assertEqual(pkg.build_dependencies, ["cmake", "pkgconf"])
        self.assertEqual(pkg.runtime_dependencies, ["openssl", "zlib"])
        self.assertFalse(pkg.is_cask)

    @patch("subprocess.run")
    def test_run_brew_command_success(self, mock_run):
        """Test successful brew command execution."""
        mock_result = MagicMock()
        mock_result.stdout = "test output\n"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = self.analyzer.run_brew_command(["list"])

        self.assertEqual(result, "test output")
        mock_run.assert_called_once_with(
            ["brew", "list"], capture_output=True, text=True, check=True
        )

    def test_parse_brew_info_formula(self):
        """Test parsing brew info JSON for a formula."""
        test_json = json.dumps(
            [
                {
                    "name": "test-formula",
                    "desc": "Test formula description",
                    "homepage": "https://test.com",
                    "build_dependencies": ["cmake"],
                    "dependencies": ["openssl", "zlib"],
                }
            ]
        )

        with patch.object(self.analyzer, "run_brew_command", return_value=test_json):
            pkg_info = self.analyzer.parse_brew_info("test-formula", False)

        self.assertIsNotNone(pkg_info)
        if pkg_info is not None:  # Type guard for Pylance
            self.assertEqual(pkg_info.name, "test-formula")
            self.assertEqual(pkg_info.description, "Test formula description")
            self.assertEqual(pkg_info.url, "https://test.com")
            self.assertEqual(pkg_info.build_dependencies, ["cmake"])
            self.assertEqual(pkg_info.runtime_dependencies, ["openssl", "zlib"])
            self.assertFalse(pkg_info.is_cask)

    def test_parse_brew_info_cask(self):
        """Test parsing brew info JSON for a cask."""
        test_json = json.dumps(
            [
                {
                    "token": "test-cask",
                    "desc": "Test cask description",
                    "homepage": "https://testcask.com",
                }
            ]
        )

        with patch.object(self.analyzer, "run_brew_command", return_value=test_json):
            pkg_info = self.analyzer.parse_brew_info("test-cask", True)

        self.assertIsNotNone(pkg_info)
        if pkg_info is not None:  # Type guard for Pylance
            self.assertEqual(pkg_info.name, "test-cask")
            self.assertEqual(pkg_info.description, "Test cask description")
            self.assertEqual(pkg_info.url, "https://testcask.com")
            self.assertEqual(pkg_info.build_dependencies, [])
            self.assertEqual(pkg_info.runtime_dependencies, [])
            self.assertTrue(pkg_info.is_cask)

    def test_check_dependency_status(self):
        """Test dependency status checking."""
        self.analyzer.installed_packages = {"openssl", "zlib", "cmake"}

        self.assertEqual(self.analyzer.check_dependency_status("openssl"), "✅")
        self.assertEqual(self.analyzer.check_dependency_status("missing-pkg"), "❌")

    def test_format_dependencies(self):
        """Test dependency formatting."""
        self.analyzer.installed_packages = {"openssl", "zlib"}

        # Test with installed dependencies
        result = self.analyzer.format_dependencies(["openssl", "zlib"])
        self.assertEqual(result, "✅ openssl, ✅ zlib")

        # Test with mixed dependencies
        result = self.analyzer.format_dependencies(["openssl", "missing"])
        self.assertEqual(result, "✅ openssl, ❌ missing")

        # Test with empty dependencies
        result = self.analyzer.format_dependencies([])
        self.assertEqual(result, "")

    def test_build_reverse_dependencies(self):
        """Test reverse dependency building."""
        # Set up test packages
        pkg1 = PackageInfo("pkg1", "desc1", "url1", ["cmake"], ["openssl"], False)
        pkg2 = PackageInfo("pkg2", "desc2", "url2", [], ["openssl", "zlib"], False)

        self.analyzer.packages = {"pkg1": pkg1, "pkg2": pkg2}
        self.analyzer.build_reverse_dependencies()

        # Check reverse dependencies
        self.assertIn("pkg1", self.analyzer.reverse_dependencies["cmake"])
        self.assertIn("pkg1", self.analyzer.reverse_dependencies["openssl"])
        self.assertIn("pkg2", self.analyzer.reverse_dependencies["openssl"])
        self.assertIn("pkg2", self.analyzer.reverse_dependencies["zlib"])


if __name__ == "__main__":
    unittest.main()
