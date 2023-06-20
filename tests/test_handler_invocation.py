#   Copyright 2022 Modelyst LLC
#   All Rights Reserved

import asyncio
from typing import TypeVar
from unittest.mock import patch

import pytest

from eventyst.concurrency.handler_invocation import HandlerInvocation

T = TypeVar('T')
E = TypeVar('E')


def test_handler_invocation_sync():
    """Test running a synchronous handler invocation."""

    def handler(event):
        return event['x'] + event['y']

    event = {'x': 1, 'y': 2}
    invocation = HandlerInvocation(handler, event)

    result = invocation.run()

    assert result is None
    assert invocation.future.result() == 3


@pytest.mark.asyncio
async def test_handler_invocation_async():
    """Test running an asynchronous handler invocation."""

    async def handler(event):
        await asyncio.sleep(0.1)
        return event['x'] + event['y']

    event = {'x': 1, 'y': 2}
    invocation = HandlerInvocation(handler, event)

    result = invocation.run()

    assert asyncio.isfuture(result)
    assert await invocation.async_result() == 3


def test_handler_invocation_sync_exception():
    """Test running a synchronous handler invocation that raises an exception."""

    def handler(event):
        raise ValueError('test error')

    event = {'x': 1, 'y': 2}
    invocation = HandlerInvocation(handler, event)

    result = invocation.run()

    assert result is None
    with pytest.raises(ValueError, match='test error'):
        invocation.future.result()


@pytest.mark.asyncio
async def test_handler_invocation_async_exception():
    """Test running an asynchronous handler invocation that raises an exception."""

    async def handler(event):
        await asyncio.sleep(0.1)
        raise ValueError('test error')

    event = {'x': 1, 'y': 2}
    invocation = HandlerInvocation(handler, event)

    invocation.run()
    with pytest.raises(ValueError, match='test error'):
        await invocation.async_result()


def test_handler_invocation_async_no_loop():
    """Test running an asynchronous handler invocation without an event loop."""

    async def handler(event):
        await asyncio.sleep(0.1)
        return event['x'] + event['y']

    event = {'x': 1, 'y': 2}
    invocation = HandlerInvocation(handler, event)

    with patch('eventyst.concurrency.handler_invocation.get_running_loop', return_value=None):
        result = invocation.run()

    assert result is None
    assert invocation.result() == 3


@pytest.mark.asyncio
async def test_handler_invocation_async_with_loop():
    """Test running an asynchronous handler invocation with an event loop."""

    async def handler(event):
        await asyncio.sleep(0.1)
        return event['x'] + event['y']

    event = {'x': 1, 'y': 2}
    invocation = HandlerInvocation(handler, event)

    result = invocation.run()

    assert asyncio.isfuture(result)
    assert await invocation.async_result() == 3


def test_handler_call_sync():
    """Test calling a handler."""

    def handler(event):
        return event['x'] + event['y']

    event = {'x': 1, 'y': 2}
    invocation = HandlerInvocation(handler, event)
    assert 3 == invocation()


def test_handler_call_async():
    """Test calling a handler."""

    async def handler(event):
        await asyncio.sleep(0.1)
        return event['x'] + event['y']

    event = {'x': 1, 'y': 2}
    invocation = HandlerInvocation(handler, event)
    assert 3 == invocation()


@pytest.mark.asyncio
async def test_handler_call_async_with_loop():
    async def handler(event):
        await asyncio.sleep(0.1)
        return event['x'] + event['y']

    event = {'x': 1, 'y': 2}
    invocation = HandlerInvocation(handler, event)
    assert 3 == await invocation()
