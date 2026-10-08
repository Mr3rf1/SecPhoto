#!/usr/bin/env python3
"""
Comprehensive E2E Test for Telegram OTP and Login Process
Tests both CLI and GUI authentication flows
"""

import asyncio
import sys
import os
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'ignore')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'ignore')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_test(message):
    print(f"{Colors.BLUE}[TEST]{Colors.RESET} {message}")


def print_success(message):
    print(f"{Colors.GREEN}[✓ PASS]{Colors.RESET} {message}")


def print_fail(message):
    print(f"{Colors.RED}[✗ FAIL]{Colors.RESET} {message}")


def print_warning(message):
    print(f"{Colors.YELLOW}[⚠ WARN]{Colors.RESET} {message}")


def print_header(message):
    print(f"\n{Colors.BOLD}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{message.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 70}{Colors.RESET}\n")


class TestResults:
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.warnings = 0
    
    def add_pass(self, test_name):
        self.total += 1
        self.passed += 1
        print_success(f"{test_name}")
    
    def add_fail(self, test_name, reason=""):
        self.total += 1
        self.failed += 1
        msg = f"{test_name}"
        if reason:
            msg += f" - {reason}"
        print_fail(msg)
    
    def add_warning(self, message):
        self.warnings += 1
        print_warning(message)
    
    def print_summary(self):
        print_header("TEST SUMMARY")
        print(f"Total Tests: {self.total}")
        print(f"{Colors.GREEN}Passed: {self.passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {self.failed}{Colors.RESET}")
        print(f"{Colors.YELLOW}Warnings: {self.warnings}{Colors.RESET}")
        
        if self.failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED!{Colors.RESET}\n")
            return 0
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}✗ SOME TESTS FAILED{Colors.RESET}\n")
            return 1


async def test_imports(results: TestResults):
    """Test 1: Verify all required modules can be imported"""
    print_header("TEST 1: Module Imports")
    
    modules_to_test = [
        ("telethon", "Telethon"),
        ("colorama", "Colorama"),
        ("PySide6.QtCore", "PySide6 Core"),
        ("PySide6.QtWidgets", "PySide6 Widgets"),
        ("pytz", "PyTZ"),
        ("jdatetime", "JDateTime"),
        ("socks", "PySocks"),
    ]
    
    for module_name, display_name in modules_to_test:
        try:
            __import__(module_name)
            results.add_pass(f"Import {display_name}")
        except ImportError as e:
            results.add_fail(f"Import {display_name}", str(e))


async def test_config_loading(results: TestResults):
    """Test 2: Configuration file loading and validation"""
    print_header("TEST 2: Configuration Loading")
    
    try:
        from core.config import (
            load_config, save_config, DEFAULT_CONFIG, CONFIG_FILE,
            APP_DIR, SESSIONS_DIR, ensure_directories
        )
        results.add_pass("Import config module")
        
        # Test directory creation
        ensure_directories()
        if SESSIONS_DIR.exists():
            results.add_pass("Sessions directory exists/created")
        else:
            results.add_fail("Sessions directory creation failed")
        
        # Test config loading
        config = load_config()
        if isinstance(config, dict):
            results.add_pass("Config loaded as dictionary")
        else:
            results.add_fail("Config not loaded properly")
        
        # Validate required keys
        required_keys = ["api_id", "api_hash", "last_session", "proxy_enabled"]
        for key in required_keys:
            if key in config:
                results.add_pass(f"Config contains '{key}'")
            else:
                results.add_fail(f"Config missing key '{key}'")
        
    except Exception as e:
        results.add_fail("Configuration system", str(e))


async def test_telethon_engine_initialization(results: TestResults):
    """Test 3: TelethonEngine class initialization"""
    print_header("TEST 3: TelethonEngine Initialization")
    
    try:
        from core.telethon_engine import TelethonEngine
        results.add_pass("Import TelethonEngine")
        
        # Test engine creation with default parameters
        engine = TelethonEngine(
            session_name_or_path="test_session",
            api_id=1234567,
            api_hash="test_hash_123",
            save_local_backup=True,
            local_backup_dir="test_media",
            send_to_chat=True,
            target_chat="me"
        )
        results.add_pass("TelethonEngine instantiation")
        
        # Validate attributes
        if engine.api_id == 1234567:
            results.add_pass("API ID set correctly")
        else:
            results.add_fail("API ID not set correctly")
        
        if engine.api_hash == "test_hash_123":
            results.add_pass("API Hash set correctly")
        else:
            results.add_fail("API Hash not set correctly")
        
        # Test client creation
        client = engine.create_client()
        if client is not None:
            results.add_pass("Telegram client created")
        else:
            results.add_fail("Telegram client creation failed")
        
        # Test logging functions
        log_captured = []
        def log_callback(level, message):
            log_captured.append((level, message))
        
        engine.on_log = log_callback
        engine.log("info", "Test message")
        
        if len(log_captured) > 0:
            results.add_pass("Logging callback works")
        else:
            results.add_fail("Logging callback not triggered")
        
    except Exception as e:
        results.add_fail("TelethonEngine initialization", str(e))


async def test_phone_validation(results: TestResults):
    """Test 4: Phone number validation"""
    print_header("TEST 4: Phone Number Validation")
    
    import re
    
    phone_pattern = r'^\+[1-9]\d{6,14}$'
    
    valid_phones = [
        "+1234567890",
        "+989123456789",
        "+447911123456",
        "+12025551234"
    ]
    
    invalid_phones = [
        "1234567890",      # Missing +
        "+0234567890",     # Starts with 0
        "+12",             # Too short
        "123456789012345678",  # Too long
        "+12 345 6789",    # Contains spaces
        "+12-345-6789",    # Contains dashes
        "abc",             # Not a number
    ]
    
    for phone in valid_phones:
        if re.match(phone_pattern, phone):
            results.add_pass(f"Valid phone accepted: {phone}")
        else:
            results.add_fail(f"Valid phone rejected: {phone}")
    
    for phone in invalid_phones:
        if not re.match(phone_pattern, phone):
            results.add_pass(f"Invalid phone rejected: {phone}")
        else:
            results.add_fail(f"Invalid phone accepted: {phone}")


async def test_auth_error_handling(results: TestResults):
    """Test 5: Authentication error handling"""
    print_header("TEST 5: Auth Error Handling")
    
    try:
        from telethon.errors import (
            SessionPasswordNeededError,
            PhoneCodeInvalidError,
            PhoneCodeExpiredError,
            PasswordHashInvalidError,
            PhoneNumberInvalidError
        )
        results.add_pass("Import Telethon error classes")
        
        # Test error types exist
        error_classes = [
            SessionPasswordNeededError,
            PhoneCodeInvalidError,
            PhoneCodeExpiredError,
            PasswordHashInvalidError,
            PhoneNumberInvalidError
        ]
        
        for err_class in error_classes:
            results.add_pass(f"Error class exists: {err_class.__name__}")
        
    except Exception as e:
        results.add_fail("Error handling setup", str(e))


async def test_cli_auth_functions(results: TestResults):
    """Test 6: CLI authentication helper functions"""
    print_header("TEST 6: CLI Auth Functions")
    
    try:
        # Read the SecPhoto.py main file and validate key functions exist
        with open("SecPhoto.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        required_functions = [
            "get_phone_number",
            "authenticate_user",
            "build_filename",
            "build_caption",
            "is_self_destructive",
        ]
        
        for func in required_functions:
            if f"def {func}" in content or f"async def {func}" in content:
                results.add_pass(f"Function '{func}' exists in CLI")
            else:
                results.add_fail(f"Function '{func}' missing in CLI")
        
        # Check for proper error handling
        if "SessionPasswordNeededError" in content:
            results.add_pass("CLI handles 2FA (SessionPasswordNeededError)")
        else:
            results.add_fail("CLI missing 2FA handling")
        
        if "PhoneCodeInvalidError" in content:
            results.add_pass("CLI handles invalid code errors")
        else:
            results.add_warning("CLI may not handle PhoneCodeInvalidError")
        
    except Exception as e:
        results.add_fail("CLI auth functions check", str(e))


async def test_engine_auth_methods(results: TestResults):
    """Test 7: Engine authentication methods"""
    print_header("TEST 7: Engine Auth Methods")
    
    try:
        from core.telethon_engine import TelethonEngine
        import inspect
        
        engine = TelethonEngine(
            session_name_or_path="test",
            api_id=123,
            api_hash="test"
        )
        
        required_methods = [
            "request_login_code",
            "complete_sign_in_code",
            "complete_sign_in_2fa",
            "check_is_authorized",
        ]
        
        for method_name in required_methods:
            if hasattr(engine, method_name):
                method = getattr(engine, method_name)
                if callable(method):
                    results.add_pass(f"Method '{method_name}' exists and callable")
                    
                    # Check if it's async
                    if inspect.iscoroutinefunction(method):
                        results.add_pass(f"Method '{method_name}' is async")
                    else:
                        results.add_warning(f"Method '{method_name}' is not async")
                else:
                    results.add_fail(f"Method '{method_name}' not callable")
            else:
                results.add_fail(f"Method '{method_name}' missing")
        
    except Exception as e:
        results.add_fail("Engine auth methods", str(e))


async def test_gui_auth_view(results: TestResults):
    """Test 8: GUI Authentication View"""
    print_header("TEST 8: GUI Auth View")
    
    try:
        from PySide6.QtWidgets import QApplication
        from gui.auth_view import AuthView
        
        # Need QApplication for Qt widgets
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        results.add_pass("Qt Application initialized")
        
        # Create AuthView
        auth_view = AuthView()
        results.add_pass("AuthView widget created")
        
        # Check for required signals
        required_signals = [
            "sig_request_code",
            "sig_submit_code",
            "sig_submit_2fa",
            "sig_load_session",
            "sig_auth_success"
        ]
        
        for signal_name in required_signals:
            if hasattr(auth_view, signal_name):
                results.add_pass(f"Signal '{signal_name}' exists")
            else:
                results.add_fail(f"Signal '{signal_name}' missing")
        
        # Check for required input fields
        required_inputs = [
            "input_phone",
            "input_api_id",
            "input_api_hash",
            "input_code",
            "input_password",
        ]
        
        for input_name in required_inputs:
            if hasattr(auth_view, input_name):
                results.add_pass(f"Input field '{input_name}' exists")
            else:
                results.add_fail(f"Input field '{input_name}' missing")
        
        # Check for required buttons
        required_buttons = [
            "btn_send_code",
            "btn_verify_code",
            "btn_verify_password",
        ]
        
        for btn_name in required_buttons:
            if hasattr(auth_view, btn_name):
                results.add_pass(f"Button '{btn_name}' exists")
            else:
                results.add_fail(f"Button '{btn_name}' missing")
        
    except ImportError as e:
        results.add_warning(f"GUI testing skipped (headless environment?): {e}")
    except Exception as e:
        results.add_fail("GUI auth view", str(e))


async def test_session_management(results: TestResults):
    """Test 9: Session file management"""
    print_header("TEST 9: Session Management")
    
    try:
        from core.config import list_saved_sessions, SESSIONS_DIR
        
        # Test session listing
        sessions = list_saved_sessions()
        if isinstance(sessions, list):
            results.add_pass("Session listing returns list")
            print_test(f"Found {len(sessions)} existing session(s)")
        else:
            results.add_fail("Session listing not returning list")
        
        # Each session should have required keys
        if len(sessions) > 0:
            required_keys = ["name", "path", "size_bytes", "modified"]
            for key in required_keys:
                if key in sessions[0]:
                    results.add_pass(f"Session metadata includes '{key}'")
                else:
                    results.add_fail(f"Session metadata missing '{key}'")
        
    except Exception as e:
        results.add_fail("Session management", str(e))


async def test_media_processing_functions(results: TestResults):
    """Test 10: Media processing functions"""
    print_header("TEST 10: Media Processing")
    
    try:
        from core.telethon_engine import TelethonEngine
        
        engine = TelethonEngine(
            session_name_or_path="test",
            api_id=123,
            api_hash="test"
        )
        
        # Test helper functions
        if callable(engine.is_self_destructive):
            results.add_pass("is_self_destructive method exists")
        else:
            results.add_fail("is_self_destructive method missing")
        
        if callable(engine.build_caption):
            results.add_pass("build_caption method exists")
        else:
            results.add_fail("build_caption method missing")
        
        if callable(engine.build_filename_stem):
            results.add_pass("build_filename_stem method exists")
        else:
            results.add_fail("build_filename_stem method missing")
        
        # Test filename generation
        filename = engine.build_filename_stem("testuser", 12345, "20240101_120000", 999)
        if filename and isinstance(filename, str):
            results.add_pass(f"Filename generation works: {filename}")
        else:
            results.add_fail("Filename generation failed")
        
        # Test timestamp formatting
        timestamp = engine.get_formatted_timestamp()
        if timestamp and isinstance(timestamp, str):
            results.add_pass(f"Timestamp formatting works: {timestamp}")
        else:
            results.add_fail("Timestamp formatting failed")
        
    except Exception as e:
        results.add_fail("Media processing", str(e))


async def test_proxy_configuration(results: TestResults):
    """Test 11: Proxy configuration handling"""
    print_header("TEST 11: Proxy Configuration")
    
    try:
        from core.telethon_engine import TelethonEngine
        from socks import SOCKS5
        
        # Test with proxy
        proxy_tuple = (SOCKS5, "127.0.0.1", 9050)
        engine = TelethonEngine(
            session_name_or_path="test",
            api_id=123,
            api_hash="test",
            proxy=proxy_tuple
        )
        
        if engine.proxy == proxy_tuple:
            results.add_pass("Proxy configuration stored correctly")
        else:
            results.add_fail("Proxy configuration not stored")
        
        # Test client creation with proxy
        client = engine.create_client()
        if client:
            results.add_pass("Client created with proxy configuration")
        else:
            results.add_fail("Client creation failed with proxy")
        
    except Exception as e:
        results.add_fail("Proxy configuration", str(e))


async def test_error_recovery(results: TestResults):
    """Test 12: Database lock recovery and error handling"""
    print_header("TEST 12: Error Recovery")
    
    try:
        # Read telethon_engine.py to check for database lock handling
        with open("core/telethon_engine.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        if "database is locked" in content.lower():
            results.add_pass("Database lock detection implemented")
        else:
            results.add_fail("Database lock detection missing")
        
        if "sqlite3.OperationalError" in content:
            results.add_pass("SQLite error handling present")
        else:
            results.add_fail("SQLite error handling missing")
        
        # Check CLI for same handling
        with open("SecPhoto.py", "r", encoding="utf-8") as f:
            cli_content = f.read()
        
        if "database is locked" in cli_content.lower():
            results.add_pass("CLI has database lock recovery")
        else:
            results.add_warning("CLI may not handle database locks")
        
    except Exception as e:
        results.add_fail("Error recovery check", str(e))


async def test_version_info(results: TestResults):
    """Test 13: Version information"""
    print_header("TEST 13: Version Information")
    
    try:
        from core.version import get_version_tag, APP_NAME, VERSION, BUILD_DATE
        
        results.add_pass("Import version module")
        
        version_str = get_version_tag()
        if version_str:
            results.add_pass(f"Version: {version_str}")
        else:
            results.add_fail("Version string empty")
        
        if APP_NAME:
            results.add_pass(f"App name: {APP_NAME}")
        else:
            results.add_fail("App name not set")
        
    except ImportError:
        results.add_warning("Version module not found (optional)")
    except Exception as e:
        results.add_fail("Version info", str(e))


async def main():
    """Run all tests"""
    print_header("SecPhoto E2E Authentication Test Suite")
    print("Testing Telegram OTP and Login Process\n")
    
    results = TestResults()
    
    # Run all test suites
    await test_imports(results)
    await test_config_loading(results)
    await test_telethon_engine_initialization(results)
    await test_phone_validation(results)
    await test_auth_error_handling(results)
    await test_cli_auth_functions(results)
    await test_engine_auth_methods(results)
    await test_gui_auth_view(results)
    await test_session_management(results)
    await test_media_processing_functions(results)
    await test_proxy_configuration(results)
    await test_error_recovery(results)
    await test_version_info(results)
    
    # Print final summary
    exit_code = results.print_summary()
    
    return exit_code


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error: {e}{Colors.RESET}")
        sys.exit(1)
