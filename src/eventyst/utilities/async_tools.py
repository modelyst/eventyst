#   Copyright 2022 Modelyst LLC
#   All Rights Reserved

import asyncio


def get_running_loop() -> asyncio.AbstractEventLoop | None:
    """
    Returns the running event loop. If there is no running event loop, None is returned.
    """
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        return None
