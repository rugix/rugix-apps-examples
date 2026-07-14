import asyncio
import math
import os
import time

from asyncua import Server


NAMESPACE_URI = "urn:rugix:examples:opcua"


async def main():
    endpoint = os.environ.get(
        "OPCUA_ENDPOINT", "opc.tcp://0.0.0.0:4840/rugix/examples/server/"
    )

    server = Server()
    await server.init()
    server.set_endpoint(endpoint)
    server.set_server_name("Rugix Apps OPC UA Machine Simulator")

    idx = await server.register_namespace(NAMESPACE_URI)
    machine = await server.nodes.objects.add_object(idx, "CNC-7")
    spindle = await machine.add_variable(idx, "SpindleLoadPct", 0.0)
    feed = await machine.add_variable(idx, "FeedRateMmMin", 0.0)
    parts = await machine.add_variable(idx, "PartCount", 0)

    count = 0
    async with server:
        print(f"OPC UA simulator listening at {endpoint}", flush=True)
        while True:
            now = time.time()
            count += 1
            await spindle.write_value(round(48 + 22 * math.sin(now / 11), 2))
            await feed.write_value(round(900 + 180 * math.sin(now / 17), 2))
            await parts.write_value(count)
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())

