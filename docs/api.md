# asyncio_channel API Reference

All public symbols are available from top-level `asyncio_channel` package.

<a name="index"></a>
## Function Index

- [complete_one](#complete_one)
- [create_blocking_buffer](#create_blocking_buffer)
- [create_channel](#create_channel)
- [create_dropping_buffer](#create_dropping_buffer)
- [create_mix](#create_mix)
- [create_multiple](#create_multiple)
- [create_publication](#create_publication)
- [create_sliding_buffer](#create_sliding_buffer)
- [itermerge](#itermerge)
- [iterzip](#iterzip)
- [map](#map)
- [merge](#merge)
- [onto_channel](#onto_channel)
- [pipe](#pipe)
- [reduce](#reduce)
- [shield_from_close](#shield_from_close)
- [shield_from_read](#shield_from_read)
- [shield_from_write](#shield_from_write)
- [split](#split)
- [to_channel](#to_channel)

---

<a name="complete_one"></a>
*coroutine* `asyncio_channel.complete_one(*ch_ops, priority=False [, default=*])`

Complete at most one channel operation.

`ch_ops` should be a collection of channels, i.e. attempt to take an item from channel, or a two-tuple of channel and item, i.e. attempt to put an item on channel.

Returns a two-tuple of value and channel for the completed operation.  If the operation was a take, then value will be the item taken; if the operation was a put, then value will be `True`.

If `default` is present and no operation can complete immediately then return a two-tuple of `default` and `'default'`.

If `priority` is `True` then the first operation be become ready from the ordered list of arguments will be completed.  Otherwise, the operation to complete will be a non-deterministic selection.

```python
a = create_channel()
b = create_channel()
loop.call_soon(b.offer, 42)  # Put on item on b.

await complete_one(a, b)  # => (42, b)
```

```python
a = create_channel()
b = create_channel()

a.offer(42)
b.offer(99)
loop.call_soon(b.poll)  # Free up capacity on b.

await complete_one((a, 1), (b, 11))  # => (True, b)
```

```python
# Operations may be any combination of puts or takes.
value, ch = await complete_one(a, (b, 11))
```

[Index &uarr;](#index)

---

<a name="create_blocking_buffer"></a>
`asyncio_channel.create_blocking_buffer(n)`

`n` must be an integer greater than zero.

Get a new buffer with capacity `n`.  A channel using a blocking buffer will block when full and attempting to add an item; the buffer will unblock as soon as capacity becomes available.

```python
buf = create_blocking_buffer(n=2)
ch = create_channel(buf)
for i in range(10):
	await ch.put(i)  # Blocks after two items are added.
```

[Index &uarr;](#index)

---

<a name="create_channel"></a>
`asyncio_channel.create_channel(n_or_buffer=1)`

Get a new channel using given buffer, or if given a positive integer then a new [dropping_buffer](#dropping_buffer) will be used.

A channel is a sequence type which supports adding and removing items both synchronously and asynchronously.  A channel may be "closed", preventing any more items from being added.  Items may still be removed even after the channel is closed.

A channel supports asynchronous iteration which terminates when the channel will no longer produce items, i.e. is closed and empty.

**Channel methods:**

- `empty()`

  Return `True` if the channel has no items, otherwise `False`.

- `full()`

  Return `True` if the channel has no capacity, otherwise `False`.

- *coroutine* `capacity()`

  Block until the channel has capacity or is closed.  Returns `True` if the channel is open, otherwise `False`.

- *coroutine* `item()`

  Block until the channel has an item or is closed.  Returns `True` if the channel has an item, otherwise `False`.

- *coroutine* `closed()`

  Block until the channel is closed.

- `close()`

  Close the channel.

- `is_closed()`

  Return `True` if the channel is closed, otherwise `False`.

- `offer(x)`

  Attempt to synchronously add `x` to the channel.  Returns `True` if `x` was added, otherwise `False`, i.e. the channel is closed or full.

- `poll(*, default=None)`

  Attempt to synchronously remove an item from the channel.  Returns `default` if the channel is empty.

- *coroutine* `put(x, *, timeout=None)`

  Block until `x` is accepted by the channel, according to the buffering strategy.  If `timeout` is `None` then block indefinitely, otherwise abandon the attempt after the number of seconds has elapsed.  Returns `True` if `x` was added, otherwise `False`.

- *coroutine* `take(*, timeout=None, default=None)`

  Block until an item is removed from the channel.  If `timeout` is `None` then block indefinitely, otherwise abandon the attempt after the number seconds has elapsed and return `default`.

[Index &uarr;](#index)

---

<a name="create_dropping_buffer"></a>
`asyncio_channel.create_dropping_buffer(n)`

`n` must be an integer greater than zero.

Get a new buffer with capacity `n`.  A channel using a dropping buffer will never block, instead when the buffer is full new items will be dropped.

```python
buf = create_dropping_buffer(n=2)
ch = create_channel(buf)
for i in range(10):
	ch.offer(i)

ch.poll()   # => 0
ch.poll()   # => 1
```

[Index &uarr;](#index)

---

<a name="create_mix"></a>
`asyncio_channel.create_mix(out)`

Create a mix of input channels that will put items on `out`.  Items will stop being taken from input channels when `out` is closed.

The mix may be put in "priority mode" to include only a marked subset of input channels in the create_mix.

<a name="mix-ch-flags"></a>
Each input channel has multiple associated flags which may be set using `.toggle()`:

- `'priority'`

  If `True` then include this channel when the mix is in priority mode; ignorning the channel's `'mute'` and `'pause'` flags.  Default is `False`.

- `'mute'`

  If `True` then items will be taken from channel but put on `out`.  Default is `False`.

- `'pause'`
  If `True` then items will *not* be taken from channel.  Default is `False`.

**ChannelMix properties and methods:**

- `PRIORITY_OFF`

  Disable priority mode.

- `PRIORITY_MUTE`

  Enable priority mode.  All non-priority, non-pause channels will be treated as muted.

- `PRIORITY_PAUSE`

  Enable priority mode.  All non-priority channels will be treated as paused.

- `priority_mode`

  One of `PRIORITY_OFF`, `PRIORITY_MUTE`, or `PRIORITY_PAUSE`.  Assign to change the mode of the mix.

- `add_input(ch)`

  Add `ch` to input mix.  All control flags are set to `False`.

- `remove_input(ch)`

  Remove `ch` from input mix.

- `remove_all_inputs()`

  Remove all channels from input mix.

- `toggle(ch1, ch1_opts [, ch2, ch2_opts, ...])`

  Arguments should always be in pairs of a channel and a `dict` with any of the control flags describe [above](#mix-ch-flags).

```python
out = create_channel()
m = create_mix(out)

a = create_channel()
b = create_channel()
m.add_input(a)
m.add_input(b)
# equivalent to m.toggle(a, {}, b, {})

await a.put(42)
await out.take()  # => 42

await b.put(99)
await out.take()  # => 99
```

[Index &uarr;](#index)

---

<a name="create_multiple"></a>
`asyncio_channel.create_multiple(src)`

Create a multiple of `src`.  Items will be taken from `src` and distributed to each output channel.

**ChannelMultiple methods:**

- `add_output(ch, *, close=True)`

  Add `ch` to multiple.  If `close` is `True` then `ch` will be closed when source channel is closed.

- `remove_output(ch)`

  Remove `ch` from the multiple.

- `remove_all_outputs()`

  Remove all channels from the multiple.

```python
ch = create_channel()
m = create_multiple(ch)

a = create_channel()
m.add_output(a)
b = create_channel()
m.add_output(b)

await ch.put(42)
await a.take()  # => 42
await b.take()  # => 42
```

[Index &uarr;](#index)

---

<a name="create_publication"></a>
`asyncio_channel.create_publication(src, topic_fn, *, n_or_buffer=1)`

Create a publication for `src` channel.

When an item is taken from `src` it is passed to `topic_fn` which returns a "topic" -- i.e. any hashable value.  The item is then distributed to all channels which subscribe to that topic.

Topic channels are created with [create_channel()](#create_channel), and is passed `n_or_buffer`.

**Publication methods:**

- `subscribe(topic, ch, *, close=True)`

  Subscribe `ch` to receive items on `topic`.  If `close` is `True` then `ch` will be closed when the publication source channel is closed.

- `unsubscribe(topic, ch)`

  Unsubscribe `ch` from `topic`.

- `unsubscribe_all(topic=None)`

  Unsubscribe all channels from `topic`, or all topics if `None`.

```python
p = create_publication(ch, topic_fn=itertools.itemgetter('type'))

await ch.put({'type': 'cat', 'name': 'Fluffy'})
await ch.put({'type': 'dog', 'name': 'Spot'})

# Elsehwere ...

cats = create_channel()
p.subscribe('cat', cats)
dogs = create_channel()
p.subscribe('dog', dogs)

await cats.take()  # => {'type': 'cat', 'name': 'Fluffy'}
await dogs.take()  # => {'type': 'dog', 'name': 'Spot'}
```

[Index &uarr;](#index)

---

<a name="create_sliding_buffer"></a>
`asyncio_channel.create_sliding_buffer(n)`

`n` must be an integer greater than zero.

Get a new buffer with capacity `n`.  A channel using a sliding buffer will never block, instead when the buffer is full the oldest item in the buffer is discarded to free up capacity.

```python
buf = create_sliding_buffer(n=2)
ch = create_channel(buf)
for i in range(10):
	ch.offer(i)

ch.poll()   # => 8
ch.poll()   # => 9
```

[Index &uarr;](#index)

---

<a name="itermerge"></a>
`asyncio_channel.itermerge(*chs)`

Get an asynchronous iterator that yields the first item taken from any of the channels, then the next item taken, and so on until all channels are closed and empty.

```python
async for a_or_b in itermerge(cha, chb):
	print(f'got {a_or_b}')
```

[Index &uarr;](#index)

---

<a name="iterzip"></a>
`asyncio_channel.iterzip(*chs)`

Get an asynchronous iterator that first yields a tuple containing the first items taken from each channel in `chs`, next a tuple containing the second items taken from each channel, and so on until one or more channels is closed and empty.

```python
async for a, b in iterzip(cha, chb):
	print(f'got {a} and {b}')
```

[Index &uarr;](#index)

---

<a name="map"></a>
`asyncio_channel.map(fn, chs, n_or_buffer=1)`

Get a new channel where each put item is the result of `fn` applied to the set of items taken from all channels in `chs`.  The channel is created by calling [create_channel()](#create_channel) with `n_or_buffer`, and is closed when any input channel is closed.

```python
a = create_channel()
b = create_channel()

out = map(operator.add, (a, b))

await a.put(2)
await b.put(5)
await out.take()  # => 7
```

[Index &uarr;](#index)

---

<a name="merge"></a>
`asyncio_channel.merge(chs, n_or_buffer=1)`

Get a new channel that merges multiple channels.  The channel is created by calling [create_channel()](#create_channel) with `n_or_buffer`, and is closed when all input channels are closed.

```python
a = create_channel()
b = create_channel()

out = merge(a, b)

await a.put(42)
await out.take()  # => 42
await b.put(99)
await out.take()  # => 99
```

[Index &uarr;](#index)

---

<a name="onto_channel"></a>
`asyncio_channel.onto_channel(collection, ch, *, close=True)`

Copy items from `collection` onto `ch`.  If `close` is `True` then `ch` will be closed once all items have been put.

```python
n = 4
ch = create_channel(n)

onto_channel(range(n), ch)

async for x in ch:
	# 0, 1, 2, 3
```

[Index &uarr;](#index)

---

<a name="pipe"></a>
`asyncio_channel.pipe(src, dest, *, close=True)`

Take items from `src` and put on `dest` until either `dest` is closed or `srcs` is closed and empty.  If `close` is `True` then `dest` will be closed when `src` is closed.

```python
a = create_channel()
b = create_channel()

pipe(a, b)

await a.put(42)
await b.take()  # => 42
```

[Index &uarr;](#index)

---

<a name="reduce"></a>
`asyncio_channel.reduce(fn, ch, init=None)`

Get a new channel which will receive the result of reducing items taken from `ch`.

`fn` should be a two-arity function.  When the first item is taken from `ch`, `fn` is called with `init` and the item.  For additional items taken, `fn` is called with the previous result and the item.

When `ch` is closed, the last result of calling `fn`, or `init` if no item was taken, is put on the returned channel.  The channel will then be closed.

```python
onto_channel(range(10), ch)

out = reduce(operator.add, ch, 0)

await out.take()  # => 45
```

[Index &uarr;](#index)

---

<a name="shield_from_close"></a>
`asyncio_channel.shield_from_close(ch, *, silent=False)`

Shield a channel from being closed when `.close()` is called. Only the returned object is shielded, `ch` is unchanged.

If `silent` is false then calls to `.close()` will raise a `asyncio_channel.ProhibitedOperationError`.

[Index &uarr;](#index)

---

<a name="shield_from_read"></a>
`asyncio_channel.shield_from_read(ch, *, silent=False)`

Shield a channel from having items taken, or "read".  Only the returned object is shielded, `ch` is unchanged.

If `silent` is false then calls to `.item()`, `.poll()`, or `.take()` will raise a `asyncio_channel.ProhibitedOperationError`, otherwise the methods will return false or the default value, as appropriate.

[Index &uarr;](#index)

---

<a name="shield_from_write"></a>
`asyncio_channel.shield_from_write(ch, *, silent=False)`

Shield a channel from having items put, or "written".  Only the returned object is shielded, `ch` is unchanged.

If `silent` is false then calls to `.capacity()`, `.offer()`, or `.put()` will raise a `asyncio_channel.ProhibitedOperationError`, otherwise the methods will return false.

[Index &uarr;](#index)

---

<a name="split"></a>
`asyncio_channel.split(predicate, ch, true_n_or_buffer=1, false_n_or_buffer=1)`

Returns a two-tuple of new channels.  The channel at index zero will receive items from `ch` for which `predicate` returned true, the other items will be put on the channel at index one.

Both channels are created with [create_channel()](#create_channel), which is passed the corresponding `*_n_or_buffer` argument.

Both channels will be closed when `ch` is closed.

```python
is_even = lambda n: n % 2 == 0

evens, odds = split(is_even, ch)
onto_channel(range(10), ch)

async for even in evens:
	# 0, 2, 4, 6, 8
async for odd in odds:
	# 1, 3, 5, 7, 9
```

[Index &uarr;](#index)

---

<a name="to_channel"></a>
`asyncio_channel.to_channel(collection)`

Returns a new channel onto which items from `collection` will be copied.
The channel will be closed once all items have been copied.

```python
nums = to_channel(range(10))

async for n in nums:
	# 0, 1, 2, ...
```

[Index &uarr;](#index)
