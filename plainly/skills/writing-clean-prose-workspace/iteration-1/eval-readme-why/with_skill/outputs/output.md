## Why this exists

Most rate limiters are buried inside something bigger. Your web framework has one. Your API gateway has one. Your cloud provider charges you for one. So why write another?

Because the moment you need to limit a background job, a CLI tool, or a worker that never touches HTTP, those built-in limiters are gone. You end up copying a token-bucket snippet off Stack Overflow, getting the refill math slightly wrong, and finding out in production when a third-party API bans your IP for an hour.

This library is the limiter on its own. No framework, no server, no assumptions about where the calls come from. You give it a key and a rate, and it tells you whether to proceed or wait. It runs in-process by default and talks to Redis when you need the count shared across machines.

The algorithms are the boring, correct ones: token bucket, sliding window, and a fixed window for when you just want a counter that resets. Each one is about 200 lines you can read in a sitting. We wrote the tests first, and the clock is injectable, so you can fast-forward an hour in a unit test instead of sleeping through it.

If your framework already does this well, use that. Reach for this when the thing you need to throttle doesn't fit the shape your framework expects.
