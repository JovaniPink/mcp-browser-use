"""Client helpers for interacting with the in-process FastMCP server."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Callable, Optional

from fastmcp.client import Client

from .server import app


class AgentNotRegisteredError(RuntimeError):
    """Error raised when attempting to control an agent that is not running."""


@asynccontextmanager
async def create_client_session(
    client: Optional[Client] = None,
    *,
    client_factory: Optional[Callable[[], Client]] = None,
    **client_kwargs: Any,
) -> AsyncIterator[Client]:
    """Create an asynchronous context manager for interacting with the server.

    Parameters
    ----------
    client:
        An existing :class:`fastmcp.client.Client` instance. If provided, the
        caller is responsible for its configuration. ``client_kwargs`` must not
        be supplied in this case.
    client_factory:
        Optional callable used to lazily construct a client. This is useful in
        testing where a lightweight stub client might be injected. If provided,
        the callable is invoked with no arguments and ``client_kwargs`` must not
        be supplied.
    **client_kwargs:
        Additional keyword arguments forwarded to :class:`fastmcp.client.Client`
        when neither ``client`` nor ``client_factory`` is provided.

    Yields
    ------
    Client
        A connected FastMCP client ready for use within the context manager.
    """

    if client is not None and client_factory is not None:
        raise ValueError("Provide either 'client' or 'client_factory', not both.")

    if client is not None and client_kwargs:
        raise ValueError(
            "'client_kwargs' cannot be used when an explicit client instance is provided."
        )

    if client_factory is not None and client_kwargs:
        raise ValueError(
            "'client_kwargs' cannot be combined with 'client_factory'."
        )

    session_client = client
    if session_client is None:
        session_client = client_factory() if client_factory else Client(app, **client_kwargs)

    async with session_client as connected_client:
        yield connected_client
