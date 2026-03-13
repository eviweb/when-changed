import sys
import types
from unittest.mock import MagicMock, patch

# Mock watchdog before any import of whenchanged
watchdog_mock = types.ModuleType('watchdog')
watchdog_observers = types.ModuleType('watchdog.observers')
watchdog_events = types.ModuleType('watchdog.events')

watchdog_observers.Observer = MagicMock
watchdog_events.FileSystemEventHandler = object

watchdog_mock.observers = watchdog_observers
watchdog_mock.events = watchdog_events

sys.modules['watchdog'] = watchdog_mock
sys.modules['watchdog.observers'] = watchdog_observers
sys.modules['watchdog.events'] = watchdog_events
sys.modules['subprocess32'] = MagicMock()
