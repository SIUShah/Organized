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

describe("beta access workflow", () => {
  it("rejects incomplete public beta requests", async () => {
    const caller = appRouter.createCaller(context());
    await expect(caller.beta.submit({ name: "A", email: "bad", useCase: "short" })).rejects.toThrow();
  });

  it("protects the beta review queue from non-admin users", async () => {
    const caller = appRouter.createCaller(appRouterContext("user"));
    await expect(caller.beta.list()).rejects.toMatchObject({ code: "FORBIDDEN" });
  });
});

function appRouterContext(role: "user" | "admin"): TrpcContext {
  return context({
    id: 1,
    openId: "test-user",
    email: "test@example.com",
    name: "Test User",
    loginMethod: "test",
    role,
    createdAt: new Date(),
    updatedAt: new Date(),
    lastSignedIn: new Date(),
  });
}
