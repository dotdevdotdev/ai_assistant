from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Union, Awaitable
from asyncio import Queue, iscoroutinefunction


class EventType(Enum):
    AUDIO_STARTED = auto()
    AUDIO_STOPPED = auto()
    TRANSCRIPTION_STARTED = auto()
    TRANSCRIPTION_STOPPED = auto()
    TRANSCRIPTION_RESULT = auto()
    ASSISTANT_RESPONSE_STARTED = auto()
    ASSISTANT_RESPONSE_CHUNK = auto()
    ASSISTANT_RESPONSE_FINISHED = auto()
    ERROR = auto()


@dataclass
class Event:
    type: EventType
    data: Optional[Any] = None
    error: Optional[Exception] = None


class EventBus:
    _instance = None

    def __init__(self):
        self._subscribers: Dict[
            EventType,
            List[Union[Callable[[Event], None], Callable[[Event], Awaitable[None]]]],
        ] = {}
        self._queue: Queue[Event] = Queue()

    @classmethod
    def get_instance(cls) -> "EventBus":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def subscribe(
        self, event_type: EventType, callback: Callable[[Event], None]
    ) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def unsubscribe(
        self, event_type: EventType, callback: Callable[[Event], None]
    ) -> None:
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)

    async def emit(self, event: Event) -> None:
        await self._queue.put(event)
        if event.type in self._subscribers:
            for callback in self._subscribers[event.type]:
                try:
                    if iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    # Log the error instead of recursive emit
                    print(f"Error in event callback: {e}")

    async def get_event(self) -> Event:
        return await self._queue.get()
