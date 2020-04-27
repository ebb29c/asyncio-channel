"""
A demo of communication and coordination between coroutines.
"""

from asyncio import create_task, gather, get_running_loop, run, sleep
from asyncio_channel import create_channel
from random import random


async def player(response, recv, send):
    # Wait for messages on the recv channel.
    async for msg in recv:
        # Display message received.
        print(msg)

        # Sleep 0-1.5 seconds.
        await sleep(1.5 * random())

        await send.put(response)

    # Loop exits when recv channel closes.
    #
    # Close the send channel to indicate that no more
    # messages should be expected.
    send.close()


async def main():
    ping = create_channel()
    pong = create_channel()

    # Stop the game after 10 seconds.
    #
    # Closing the ping channel will stop the ping player,
    # which will then close the pong channel, which then
    # stops the pong player.
    get_running_loop().call_later(10, ping.close)

    # Kick off the game!
    ping.offer('ping')

    # Wait until the game is done.
    await gather(
        player('ping', pong, ping),
        player('     pong', ping, pong))


run(main())
