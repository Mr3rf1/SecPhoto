import asyncio
import threading
import traceback
from typing import Optional, Dict, Any

from PySide6.QtCore import QObject, Signal, Slot
from core.telethon_engine import TelethonEngine


class TelethonWorker(QObject):
    """QObject worker managing an isolated background asyncio thread for Telethon."""

    # Signals emitted to the main GUI thread
    sig_log = Signal(str, str)  # (level, message)
    sig_status_changed = Signal(str)  # ("idle", "connecting", "listening", "error", etc.)
    sig_code_sent = Signal(bool, str)  # (success, message)
    sig_auth_result = Signal(bool, bool, str, dict)  # (success, requires_2fa, error_msg, user_info)
    sig_session_checked = Signal(bool, dict, str)  # (is_authorized, user_info, session_name)
    sig_media_captured = Signal(dict)  # media metadata dict
    sig_engine_stopped = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.engine: Optional[TelethonEngine] = None
        self._thread: Optional[threading.Thread] = None
        self._is_running = False

    def start_worker(self):
        """Start background asyncio event loop thread."""
        if self._thread and self._thread.is_alive():
            return

        self._is_running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="TelethonAsyncLoop")
        self._thread.start()

    def _run_loop(self):
        """Background thread worker loop."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def init_engine(
        self,
        session_name_or_path: str,
        api_id: int,
        api_hash: str,
        proxy: Optional[tuple] = None,
        save_local_backup: bool = True,
        local_backup_dir: str = "saved_media",
        send_to_chat: bool = True,
        target_chat: str = "saved messages",
        timezone_str: str = "Asia/Tehran"
    ):
        """Configure internal TelethonEngine."""
        self.engine = TelethonEngine(
            session_name_or_path=session_name_or_path,
            api_id=api_id,
            api_hash=api_hash,
            proxy=proxy,
            save_local_backup=save_local_backup,
            local_backup_dir=local_backup_dir,
            send_to_chat=send_to_chat,
            target_chat=target_chat,
            timezone_str=timezone_str
        )
        self.engine.on_log = lambda lvl, msg: self.sig_log.emit(lvl, msg)
        self.engine.on_media_captured = lambda data: self.sig_media_captured.emit(data)
        self.engine.on_status_changed = lambda st: self.sig_status_changed.emit(st)

    def update_engine_settings(
        self,
        save_local_backup: bool,
        local_backup_dir: str,
        send_to_chat: bool,
        target_chat: str,
        timezone_str: str,
        proxy: Optional[tuple] = None
    ):
        """Update runtime settings of active TelethonEngine."""
        if self.engine:
            self.engine.update_settings(
                save_local_backup=save_local_backup,
                local_backup_dir=local_backup_dir,
                send_to_chat=send_to_chat,
                target_chat=target_chat,
                timezone_str=timezone_str,
                proxy=proxy
            )

    def validate_target_chat(self, target: str, timeout: float = 6.0) -> tuple[bool, str]:
        """Check if target chat is available and accessible using active client."""
        if not self.engine:
            return False, "Engine not configured."

        if not self.loop or not self.loop.is_running():
            return False, "Event loop not running."

        future = asyncio.run_coroutine_threadsafe(
            self.engine.validate_target_chat(target),
            self.loop
        )
        try:
            return future.result(timeout=timeout)
        except Exception as e:
            return False, f"Chat verification timed out or failed: {str(e)}"

    def run_coroutine(self, coro):
        """Schedule a coroutine onto the worker's asyncio event loop safely."""
        if not self.loop or not self.loop.is_running():
            self.start_worker()
            # Brief wait for loop to start
            import time
            for _ in range(20):
                if self.loop and self.loop.is_running():
                    break
                time.sleep(0.05)

        if self.loop and self.loop.is_running():
            future = asyncio.run_coroutine_threadsafe(coro, self.loop)

            def _on_future_done(fut):
                try:
                    exc = fut.exception()
                    if exc:
                        print(f" [ERROR] Coroutine exception: {exc}", flush=True)
                        traceback.print_exception(type(exc), exc, exc.__traceback__)
                        self.sig_log.emit("error", f"Task error: {exc}")
                        self.sig_auth_result.emit(False, False, str(exc), {})
                        self.sig_status_changed.emit("idle")
                except Exception as err:
                    print(f" [ERROR] Error reading task future: {err}", flush=True)

            future.add_done_callback(_on_future_done)
            return future
        else:
            print(" [ERROR] Worker asyncio loop is not running!", flush=True)
            self.sig_log.emit("error", "Async loop not running.")
            return None

    # Asynchronous actions callable from GUI via Slots

    @Slot(str)
    def request_login_code(self, phone: str):
        """Request verification code for new login."""
        print(f" [DEBUG] request_login_code called for {phone}", flush=True)

        async def _task():
            self.sig_status_changed.emit("sending_code")
            try:
                res = await self.engine.request_login_code(phone)
                if res.get("success"):
                    self.sig_code_sent.emit(True, f"Code sent to {phone}")
                else:
                    self.sig_code_sent.emit(False, res.get("error", "Unknown error"))
            except Exception as e:
                self.sig_log.emit("error", f"Error requesting code: {str(e)}")
                self.sig_code_sent.emit(False, str(e))
            finally:
                self.sig_status_changed.emit("idle")

        self.run_coroutine(_task())

    @Slot(str)
    def submit_verification_code(self, code: str):
        """Submit verification code."""
        print(f" [DEBUG] submit_verification_code called with code: {code}", flush=True)

        async def _task():
            self.sig_status_changed.emit("verifying_code")
            try:
                res = await self.engine.complete_sign_in_code(code)
                if res.get("success"):
                    self.sig_auth_result.emit(True, False, "", res.get("user", {}))
                elif res.get("requires_2fa"):
                    self.sig_auth_result.emit(False, True, "2FA Password Required", {})
                else:
                    self.sig_auth_result.emit(False, False, res.get("error", "Sign in failed"), {})
            except Exception as e:
                self.sig_log.emit("error", f"Error during verification: {str(e)}")
                self.sig_auth_result.emit(False, False, str(e), {})
            finally:
                self.sig_status_changed.emit("idle")

        self.run_coroutine(_task())

    @Slot(str)
    def submit_2fa_password(self, password: str):
        """Submit 2FA password."""
        print(f" [DEBUG] submit_2fa_password called", flush=True)

        async def _task():
            self.sig_status_changed.emit("verifying_2fa")
            try:
                res = await self.engine.complete_sign_in_2fa(password)
                if res.get("success"):
                    self.sig_auth_result.emit(True, False, "", res.get("user", {}))
                else:
                    self.sig_auth_result.emit(False, True, res.get("error", "Invalid 2FA password"), {})
            except Exception as e:
                self.sig_log.emit("error", f"Error during 2FA: {str(e)}")
                self.sig_auth_result.emit(False, True, str(e), {})
            finally:
                self.sig_status_changed.emit("idle")

        self.run_coroutine(_task())

    @Slot(str)
    def validate_session(self, session_name: str):
        """Check if an existing session is authorized."""
        print(f" [DEBUG] validate_session called for {session_name}", flush=True)

        async def _task():
            self.sig_status_changed.emit("checking_session")
            try:
                user_info = await self.engine.check_is_authorized()
                if user_info:
                    self.sig_session_checked.emit(True, user_info, session_name)
                else:
                    self.sig_session_checked.emit(False, {}, session_name)
            except Exception as e:
                self.sig_log.emit("error", f"Error checking session {session_name}: {e}")
                self.sig_session_checked.emit(False, {}, session_name)
            finally:
                self.sig_status_changed.emit("idle")

        self.run_coroutine(_task())

    @Slot()
    def start_monitoring(self):
        """Start listening for self-destructing media."""
        print(" [DEBUG] start_monitoring called", flush=True)

        async def _task():
            try:
                await self.engine.start_monitoring()
            except Exception as e:
                self.sig_log.emit("error", f"Monitoring error: {e}")
                self.sig_status_changed.emit("error")

        self.run_coroutine(_task())

    @Slot()
    def stop_monitoring(self):
        """Stop listening and disconnect."""
        print(" [DEBUG] stop_monitoring called", flush=True)

        async def _task():
            try:
                if self.engine:
                    await self.engine.stop_monitoring()
            except Exception as e:
                self.sig_log.emit("error", f"Error stopping monitor: {e}")
            finally:
                self.sig_status_changed.emit("idle")
                self.sig_engine_stopped.emit()

        self.run_coroutine(_task())

    @Slot()
    def shutdown(self):
        """Cleanly stop the asyncio event loop."""
        async def _stop():
            if self.engine:
                await self.engine.stop_monitoring()
            if self.loop:
                self.loop.stop()

        if self.loop and self.loop.is_running():
            self.run_coroutine(_stop())
