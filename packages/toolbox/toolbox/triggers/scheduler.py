import json
import os
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from croniter import croniter
from loguru import logger

from toolbox.mcp_installer.uv_utils import find_uv_path
from toolbox.triggers.models import Event
from toolbox.triggers.trigger_store import Trigger, TriggerDB

DEFAULT_TRIGGER_TIMEOUT = 300  # Default timeout for trigger execution in seconds


def setup_logger(log_file: Path | None = None):
    """Setup loguru logger with optional file output"""
    if log_file:
        logger.remove()
        logger.add(log_file, rotation="10 MB")


class Scheduler:
    def __init__(self, db: TriggerDB, pid_file: Path = None):
        self.db = db
        self.running = True
        self.pid_file = pid_file or Path.home() / ".toolbox" / "scheduler.pid"

        # Ensure pid directory exists
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}")
        self.running = False

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _write_pid_file(self):
        """Write current process PID to file"""
        with open(self.pid_file, "w") as f:
            f.write(str(os.getpid()))

    def _remove_pid_file(self):
        """Remove PID file"""
        try:
            self.pid_file.unlink()
        except FileNotFoundError:
            pass

    def should_run_trigger(self, trigger: Trigger, now: datetime) -> bool:
        """Check if trigger should run based on cron schedule and last execution"""
        # Get last completed execution
        last_executions = self.db.executions.get_all(
            trigger_id=trigger.id, completed=True, limit=1
        )

        if not last_executions:
            # Never run before - check if current minute matches
            now_minute = now.replace(second=0, microsecond=0)
            return croniter.match(trigger.cron_schedule, now_minute)

        # Check  if we're overdue based on last execution
        last_run = last_executions[0].completed_at
        iter = croniter(trigger.cron_schedule, last_run)
        next_due = iter.get_next(datetime)

        logger.debug(f"Next due: {next_due}, now: {now}")

        return next_due <= now

    def get_triggers_to_run(self, now: datetime) -> list[Trigger]:
        """Get all enabled triggers that should run now"""
        triggers = self.db.triggers.get_all(enabled=True, has_schedule=True)
        return [t for t in triggers if self.should_run_trigger(t, now)]

    def _format_events_for_trigger(self, events: list[Event] | None) -> str | None:
        if not events:
            return None

        events_json = [
            Event(
                name=event.name,
                data=event.data,
                timestamp=event.timestamp,
                source=event.source,
            ).model_dump(mode="json")
            for event in events
        ]
        return json.dumps(events_json)

    def execute_trigger(
        self,
        trigger: Trigger,
        events: list[Event] | None = None,
    ) -> None:
        """Execute a trigger script using uv run"""
        # Create execution record

        execution = self.db.executions.create(trigger.id)
        self.db.events.mark_events_triggered(
            trigger_id=trigger.id,
            event_ids=[e.id for e in events],
            execution_id=execution.id,
        )

        try:
            stdin_str = self._format_events_for_trigger(events)
            # Find UV path and run the script
            uv_path = find_uv_path()
            if uv_path is None:
                raise FileNotFoundError("UV not found in PATH or common locations")

            uv_cmd = str(uv_path)
            logger.info(
                f"Executing trigger {trigger.name} with {uv_cmd} run python {trigger.script_path}"
            )
            result = subprocess.run(
                [uv_cmd, "run", trigger.script_path],
                capture_output=True,
                text=True,
                timeout=DEFAULT_TRIGGER_TIMEOUT,
                input=stdin_str,
            )

            # Store results
            logs = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            self.db.executions.set_completed(execution.id, result.returncode, logs)

        except subprocess.TimeoutExpired:
            self.db.executions.set_completed(execution.id, -1, "Execution timed out")
        except Exception as e:
            self.db.executions.set_completed(
                execution.id, -2, f"Execution failed: {str(e)}"
            )

    def run(self, log_file: Path = None):
        """Main scheduler loop - checks every second"""
        import time
        from concurrent.futures import ThreadPoolExecutor

        # Setup logging
        setup_logger(log_file)

        # Check if already running BEFORE writing our PID
        if self.is_running():
            logger.error(f"Scheduler already running (PID file: {self.pid_file})")
            sys.exit(78)  # EX_CONFIG - configuration error

        # Setup signal handlers and PID file
        self._setup_signal_handlers()
        self._write_pid_file()

        logger.info(f"Scheduler started with PID {os.getpid()}")

        try:
            with ThreadPoolExecutor(max_workers=4) as executor:
                while self.running:
                    try:
                        now = datetime.now(timezone.utc)
                        triggers_to_run = self.get_triggers_to_run(now)

                        # Submit each trigger to the thread pool
                        for trigger in triggers_to_run:
                            if trigger.is_event_based:
                                events = self.db.events.get_events_for_trigger(
                                    trigger, is_consumed=False
                                )
                                if len(events) == 0:
                                    logger.info(
                                        f"No events found for trigger {trigger.name}"
                                    )
                                    continue
                                executor.submit(self.execute_trigger, trigger, events)
                            else:
                                executor.submit(self.execute_trigger, trigger)

                        time.sleep(1)

                    except Exception as e:
                        logger.error(f"Scheduler error: {e}")
                        time.sleep(1)

        finally:
            logger.info("Scheduler shutting down...")
            self._remove_pid_file()

    def is_running(self) -> bool:
        """Check if scheduler is currently running by checking PID file"""
        if not self.pid_file.exists():
            return False

        try:
            with open(self.pid_file, "r") as f:
                pid = int(f.read().strip())

            # Check if process with this PID exists
            os.kill(pid, 0)  # This raises OSError if process doesn't exist
            return True

        except (OSError, ValueError, FileNotFoundError):
            # Process doesn't exist or PID file is corrupted
            self._remove_pid_file()
            return False

    def stop(self) -> bool:
        """Stop the scheduler daemon"""
        if not self.pid_file.exists():
            return False

        try:
            with open(self.pid_file, "r") as f:
                pid = int(f.read().strip())

            # Send SIGTERM for graceful shutdown
            os.kill(pid, signal.SIGTERM)

            # Wait a bit and check if it stopped
            import time

            for _ in range(10):  # Wait up to 10 seconds
                time.sleep(1)
                if not self.is_running():
                    return True

            # If still running, force kill
            try:
                os.kill(pid, signal.SIGKILL)
                return True
            except OSError:
                return False

        except (OSError, ValueError, FileNotFoundError):
            self._remove_pid_file()
            return False
