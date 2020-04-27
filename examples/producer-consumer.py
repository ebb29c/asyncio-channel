"""
Classic producer-consumer example.
"""

from asyncio import create_task, gather, run, sleep
from asyncio_channel import create_channel
from functools import partial
from itertools import count
from random import random


async def produce(name, produce_item, n, channel):
    for _ in range(n):
        await sleep(2 * random())
        item = produce_item()

        if await channel.put(item):
            print(f'{name}: produced {item}')
        else:
            print(f'{name}: channel rejected {item}')

    print(f'{name}: done')


async def consume(name, channel):
    async for item in channel:
        print(f'{name}: consumed {item}')

        await sleep(2 * random())

    print(f'{name}: done')


async def gather_then_call(coros, callback):
    await gather(*coros)
    callback()


async def main():
    channel = create_channel(3)

    counter = count()
    produce_item = partial(next, counter)

    producers = tuple(produce(name, produce_item, 10, channel)
                      for name in 'AB')
    consumers = tuple(consume(f'\t\t{name}', channel) for name in 'YZ')

    await gather(gather_then_call(producers, channel.close),
                 *consumers)

    await sleep(2)


run(main())
