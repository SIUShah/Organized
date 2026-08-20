import { ENV } from "./_core/env";

export type BetaNotification = {
  id: number | null;
  name: string;
  email: string;
  useCase: string;
};

export function discordIsConfigured() {
  return Boolean(ENV.discordWebhookUrl);
}

export async function sendDiscordBetaNotification(request: BetaNotification) {
  if (!ENV.discordWebhookUrl) return { configured: false, delivered: false } as const;

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 8_000);
  try {
    const response = await fetch(ENV.discordWebhookUrl, {
      method: "POST",
      headers: { "content-type": "application/json" },
      signal: controller.signal,
      body: JSON.stringify({
        username: "FindCut CTO",
        avatar_url: "https://findcutedit-hqvr4hl8.manus.space/manus-storage/findcut-smiling-creators_5d30efdb.png",
        embeds: [{
          title: "New private beta request",
          color: 16763904,
          fields: [
            { name: "Applicant", value: request.name.slice(0, 256), inline: true },
            { name: "Email", value: request.email.slice(0, 256), inline: true },
            { name: "Request ID", value: String(request.id ?? "pending"), inline: true },
            { name: "Use case", value: request.useCase.slice(0, 1024) },
          ],
          footer: { text: "FindCut private beta · review manually before inviting" },
          timestamp: new Date().toISOString(),
        }],
      }),
    });
    return { configured: true, delivered: response.ok } as const;
  } catch (error) {
    console.error("[Discord] Beta notification failed:", error);
    return { configured: true, delivered: false } as const;
  } finally {
    clearTimeout(timeout);
  }
}

export async function sendDiscordCtoMessage(message: string) {
  if (!ENV.discordWebhookUrl) return { configured: false, delivered: false } as const;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 8_000);
  try {
    const response = await fetch(ENV.discordWebhookUrl, {
      method: "POST",
      headers: { "content-type": "application/json" },
      signal: controller.signal,
      body: JSON.stringify({ username: "FindCut CTO", content: message.slice(0, 1900) }),
    });
    return { configured: true, delivered: response.ok } as const;
  } catch (error) {
    console.error("[Discord] CTO message failed:", error);
    return { configured: true, delivered: false } as const;
  } finally {
    clearTimeout(timeout);
  }
}
