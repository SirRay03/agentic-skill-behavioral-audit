// Mini-repo seed for the improve-codebase-architecture skill task.
// Three thin functions exported from one barrel — deliberately shallow modules
// so the skill has obvious "deepening" candidates to surface.

import * as db from "./db";
import * as cache from "./cache";
import * as analytics from "./analytics";

export async function getUser(id: string) {
  const user = await db.users.findOne({ id });
  cache.set(`user:${id}`, user);
  analytics.track("user.fetched", { id });
  return user;
}

// db.ts — wrapper over a Postgres client, 1-line forwarders
export const dbWrapper = {
  users: {
    findOne: async (q: { id: string }) => ({ id: q.id, name: "stub" }),
  },
};

// cache.ts — 1-line forwarder over Redis
export const cacheWrapper = {
  set: (key: string, val: unknown) => void val,
};

// analytics.ts — 1-line forwarder over the events SDK
export const analyticsWrapper = {
  track: (event: string, props: Record<string, unknown>) => void props,
};
