class Client:
    r"""
    A channel from the server to single frontend client widget.
    """
    def __init__(self, comm, log):
        self._comm = comm
        self._log = log
        self._queries = {}

        @comm.on_msg
        def _recv(msg):
            self._receive(msg)

        self._commands = {
            "callback": self._callback,
        }

    def message(self, action, data):
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

        self._comm.send(message)

    def _receive(self, message):
        r"""
        Handla an incomming ``message``.
        """
        self._log.debug(f"Client received message: {message}")
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

    def query(self, data):
        class Query:
            def __init__(self):
                import uuid
                self._identifier = uuid.uuid1().hex

                import asyncio
                self._future = asyncio.get_running_loop().create_future()

            def done(self):
                return self._future.done()

            @property
            async def value(self):
                import asyncio

                delay = .001
                events = 1
                import jupyter_ui_poll
                async with jupyter_ui_poll.ui_events() as poll:
                    while not self.done():
                        await poll(events)

                        events = min(events + 1, 64)

                        await asyncio.sleep(delay)

                        # Wait for at most 250ms, the reaction time of most
                        # people, https://stackoverflow.com/a/44755058/812379.
                        delay = min(2*delay, .25)

                return self._future.result()

        query = Query()
        self._queries[query._identifier] = query

        self.message("query", {
            "identifier": query._identifier,
            "data": data
        })

        return query
