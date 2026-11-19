from odyssey import Odyssey
client_factory = Odyssey

async def run(key, prompt):
    client = client_factory(api_key=key)
    await client.connect()
    await client.start_stream(prompt=prompt)
    await client.disconnect()
