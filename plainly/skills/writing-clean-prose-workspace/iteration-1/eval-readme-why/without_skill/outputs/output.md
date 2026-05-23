## Why this exists

Every service that talks to the outside world eventually needs to say "no, not that fast." A login endpoint gets hammered by a credential-stuffing script. A free-tier API key starts pulling ten thousand requests a minute. A retry storm from one misconfigured client threatens to take down the database for everyone else. Rate limiting is how you keep one caller from ruining the service for the rest.

The trouble is that most projects reinvent it badly. The first version is a counter in a dictionary. Then someone adds a second server and the counter no longer agrees with itself. Then the limits need to differ by user, by route, by plan. Then you want a token bucket here and a sliding window there, and the homegrown helper has quietly become a thousand lines of edge cases that nobody wants to touch.

This library exists so you don't write that thousand lines. It gives you the common algorithms—token bucket, fixed window, sliding window—behind one small interface, with backends for both in-memory use and shared stores like Redis so your limits stay consistent across every instance. The defaults are sensible, the hot path is fast, and the behavior under contention is documented rather than discovered in production.

It is deliberately narrow. It does not handle authentication, routing, or quota billing; it decides whether a given request is allowed right now and tells you when to try again. Keeping the scope that tight is what lets it stay correct, fast, and easy to reason about—which, for the piece of code standing between your service and a flood of traffic, is exactly what you want.
