#*******************************************************************************
# Copyright (c) 2021 Julian Rüth <julian.rueth@fsfe.org>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#*******************************************************************************

import asyncio

class Channel:
    r"""
    A channel from the server to a single frontend widget.
    """
    def __init__(self, log):
        self._comm = asyncio.get_running_loop().create_future()
        self._log = log
        self._queries = {}

        self._commands = {
            "callback": self._callback,
            # TODO: Add heartbeat to destroy channels that don't react anymore.
        }

    def is_connected(self):
        return self._comm.done()

    def connect(self, comm):
        if self.is_connected():
            raise Exception("Cannot reconnect already connected channel.")

        self._comm.set_result([comm])

        @comm.on_msg
        def _recv(msg):
            self._receive(msg)

    async def message(self, action, data):
        r"""
        Send ``data`` to the frontend.

        Raises an except if the client has not sent an ACK for the previous
        data.
        """
        message = {
            "action": action,
            "data": data
        }

        self._log.debug(f"Sending message to client: {message}")

        (await self._comm)[0].send(message)

    def _receive(self, message):
        r"""
        Handla an incomming ``message``.
        """
        self._log.debug(f"Backend received message: {message}")
        try:
            data = message.get("content", {}).get("data", {})
            command = data.get("command", None)

            if command not in self._commands:
                raise NotImplementedError(f"Unsupported command {command}")

            self._commands[command](data.get("data", {}))
        except Exception as e:
            self._log.error(e)

    def _callback(self, data):
        identifier = data["identifier"]

        if identifier not in self._queries:
            raise ValueError(f"No pending callback for {identifier}")

        if "value" in data:
            value = data["value"]
            self._queries[identifier]._future.set_result(value)
        elif "error" in data:
            error = data["error"]
            self._queries[identifier]._future.set_exception(Exception(error))

        del self._queries[identifier]

    async def query(self, data):
        class Query:
            def __init__(self):
                import uuid
                self._identifier = uuid.uuid1().hex

                import asyncio
                self._future = asyncio.get_running_loop().create_future()

        query = Query()
        self._queries[query._identifier] = query

        try:
            await self.message("query", {
                "identifier": query._identifier,
                "data": data
            })

            return await query._future
        except asyncio.CancelledError:
            await self.message("cancel", {
                "identifier": query._identifier,
            });
            raise
