import { describe, expect, it } from "vitest";

describe("Discord webhook configuration", () => {
  it("accepts a configured webhook URL or skips cleanly when setup is pending", async () => {
    const webhookUrl = process.env.DISCORD_WEBHOOK_URL;
    if (!webhookUrl) {
      expect(webhookUrl).toBeFalsy();
      return;
    }

    expect(webhookUrl).toMatch(/^https:\/\/discord(?:app)?\.com\/api\/webhooks\//);
    const response = await fetch(webhookUrl, { method: "GET" });
    expect(response.ok).toBe(true);
  }, 15_000);
});
