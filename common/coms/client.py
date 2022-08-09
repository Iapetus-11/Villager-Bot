import asyncio
import logging
from typing import Optional

from websockets.client import WebSocketClientProtocol, connect
from websockets.exceptions import ConnectionClosed

from common.coms.coms_base import ComsBase
from common.coms.errors import InvalidPacketReceived, WebsocketStateError
from common.coms.packet import T_PACKET_DATA, Packet
from common.coms.packet_handling import PacketHandler
from common.coms.packet_type import PacketType


class Client(ComsBase):
    def __init__(
        self,
        host: str,
        port: int,
        packet_handlers: dict[PacketType, PacketHandler],
        logger: logging.Logger,
    ):
        super().__init__(host, port, packet_handlers, logger.getChild("client"))

        self.ws: Optional[WebSocketClientProtocol] = None

        self._current_id = 0
        self._task: Optional[asyncio.Task] = None
        self._closing = False
        self._connected = asyncio.Event()
        self._waiting = dict[str, asyncio.Future[Packet]]()

    def _get_packet_id(self) -> str:
        packet_id = self._current_id
        self._current_id += 1
        return f"c{packet_id}"

    async def _disconnect(self) -> None:
        if self.ws is not None:
            await self.ws.close()
            self.ws = None

        self._connected.clear()

    async def _send(self, packet: Packet) -> None:
        if self.ws is None or self.ws.closed:
            raise WebsocketStateError("Websocket connection is not open")

        await self.ws.send(packet.json())

    async def _authorize(self, auth: str) -> None:
        await self._send(Packet(id=self._get_packet_id(), type=PacketType.AUTH, data=auth))

    async def _connect(self, auth: str) -> None:
        async for self.ws in connect(f"ws://{self.host}:{self.port}", logger=self.logger):
            try:
                await self._authorize(auth)
                self._connected.set()

                async for message in self.ws:
                    try:
                        packet = self._decode(message)
                    except InvalidPacketReceived:
                        self.logger.error("Invalid packet received from server", exc_info=True)
                        await self._disconnect()
                        break

                    # handle expected packets
                    if packet.id in self._waiting:
                        self._waiting[packet.id].set_result(packet)
                        continue

                    try:
                        response = await self._call_handler(packet)
                    except Exception:
                        self.logger.error(
                            "An error ocurred while calling the packet handler for packet type %s",
                            packet.type,
                            exc_info=True,
                        )
                    else:
                        await self._send(Packet(id=packet.id, data=response))
            except ConnectionClosed:
                if self._closing:
                    break

    async def connect(self, auth: str) -> None:
        self._task = asyncio.create_task(self._connect(auth))
        await self._connected.wait()

    async def close(self) -> None:
        self._closing = True
        await self._disconnect()

        if self._task is not None:
            try:
                await asyncio.wait_for(self._task, 1)
            except asyncio.TimeoutError:
                self._task.cancel()

    async def send(
        self, packet_type: PacketType, packet_data: Optional[dict[str, T_PACKET_DATA]] = None
    ) -> Packet:
        packet_id = self._get_packet_id()

        packet = Packet(id=packet_id, type=packet_type, data=(packet_data or {}))

        self._waiting[packet.id] = asyncio.Future[Packet]()
        await self._send(packet)
        return await self._waiting[packet.id]

    async def broadcast(
        self, packet_type: PacketType, packet_data: Optional[dict[str, T_PACKET_DATA]] = None
    ) -> Packet:
        return await self.send(
            PacketType.BROADCAST_REQUEST, {"type": packet_type, "data": (packet_data or {})}
        )
