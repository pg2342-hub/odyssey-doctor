import asyncio, os
from odyssey import Odyssey
from odyssey.exceptions import OdysseyUsageError

async def main():
    client = Odyssey(api_key=os.environ["ODYSSEY_API_KEY"])
    def on_err(reason, message):
        if reason == "session_timeout":
            pass
    try:
        await client.connect(on_stream_error=on_err)
        await client.start_stream("A cat")
    except OdysseyUsageError:
        pass
    finally:
        await client.disconnect()
asyncio.run(main())
