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

describe("projects", () => {
  it("requires authentication to list projects", async () => {
    const caller = appRouter.createCaller(context());
    await expect(caller.projects.list()).rejects.toMatchObject({ code: "UNAUTHORIZED" });
  });

  it("rejects oversized project documents before persistence", async () => {
    const caller = appRouter.createCaller(context({
      id: 1,
      openId: "project-user",
      email: "project@example.com",
      name: "Project User",
      loginMethod: "test",
      role: "user",
      createdAt: new Date(),
      updatedAt: new Date(),
      lastSignedIn: new Date(),
    }));
    await expect(caller.projects.create({ name: "Test", document: "x".repeat(200001) })).rejects.toThrow();
  });
});
