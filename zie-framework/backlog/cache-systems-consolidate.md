# cache-systems-consolidate

## Problem

Three separate cache systems exist in the codebase: session config caching (config reads re-fetched per hook invocation), ROADMAP caching (mtime-gated session cache), and content-hash TTL caching (spec/plan content hashes). Each has its own cache invalidation logic, TTL management, and cache directory structure. This creates maintenance overhead and inconsistent cache behavior.

## Rough Scope

- Unify config-session-cache, roadmap-cache-unify, and existing content-hash cache into a single `CacheManager` class or module
- Single cache directory under `.zie/cache/` with consistent TTL and invalidation
- Migrate existing cache consumers to use the unified API
- Remove duplicate cache logic from individual hooks
- Maintain backward compatibility during migration

## Priority

MEDIUM — reduces maintenance surface and ensures consistent caching behavior

## Merged From

- config-session-cache — session-level config read caching
- roadmap-cache-unify — unify ROADMAP/ADR caching with session-scoped TTL

Reason: Both touch the same caching subsystem. cache-systems-consolidate already covers their scope. Merging avoids implementing two caches that will be replaced by the unified system.