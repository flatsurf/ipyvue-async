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
        }

    def is_connected(self):
        return self._comm.done()

    def connect(self, comm):
        if self.is_connected():
            raise Exception("Cannot reconnect already connected channel.")
        self._comm.set_result(comm)

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

        self._log.warning(f"Sending message to client: {message}")

        (await self._comm).send(message)

        self._log.warn("Message sent.")

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
        value = data["value"]
        identifier = data["identifier"]
    
        if identifier not in self._queries:
            raise ValueError(f"No pending callback for {identifier}")

        self._queries[identifier]._future.set_result(value)
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
