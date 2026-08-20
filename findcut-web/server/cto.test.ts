import { describe, expect, it } from "vitest";
import { appRouter } from "./routers";
import type { TrpcContext } from "./_core/context";

function context(user?: TrpcContext["user"]): TrpcContext {
  return {
    user,
    req: { protocol: "https", headers: {} } as TrpcContext["req"],
    res: {} as TrpcContext["res"],
  };
}

describe("cto dashboard authorization", () => {
  it("rejects anonymous status checks", async () => {
    const caller = appRouter.createCaller(context());
    await expect(caller.cto.status()).rejects.toMatchObject({ code: "FORBIDDEN" });
  });

  it("rejects a signed-in non-admin account", async () => {
    const caller = appRouter.createCaller(context({
      id: 2,
      openId: "regular-user",
      email: "user@example.com",
      name: "Regular User",
      loginMethod: "test",
      role: "user",
      createdAt: new Date(),
      updatedAt: new Date(),
      lastSignedIn: new Date(),
    }));
    await expect(caller.cto.status()).rejects.toMatchObject({ code: "FORBIDDEN" });
  });
});
