import { COOKIE_NAME } from "@shared/const";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { adminProcedure, protectedProcedure, publicProcedure, router } from "./_core/trpc";
import { createBetaRequest, createMediaAsset, createProject, listBetaRequests, listMediaAssets, listProjects } from "./db";
import { discordIsConfigured, sendDiscordBetaNotification, sendDiscordCtoMessage } from "./discord";
import { invokeLLM } from "./_core/llm";
import { storagePut } from "./storage";
import { z } from "zod";

export const appRouter = router({
    // if you need to use socket.io, read and register route in server/_core/index.ts, all api should start with '/api/' so that the gateway can route correctly
  system: systemRouter,
  auth: router({
    me: publicProcedure.query(opts => opts.ctx.user),
    logout: publicProcedure.mutation(({ ctx }) => {
      const cookieOptions = getSessionCookieOptions(ctx.req);
      ctx.res.clearCookie(COOKIE_NAME, { ...cookieOptions, maxAge: -1 });
      return {
        success: true,
      } as const;
    }),
  }),

  projects: router({
    list: protectedProcedure.query(({ ctx }) => listProjects(ctx.user.openId)),
    create: protectedProcedure
      .input(z.object({ name: z.string().trim().min(1).max(160), document: z.string().max(200000) }))
      .mutation(({ ctx, input }) => createProject({ ownerOpenId: ctx.user.openId, ...input })),
  }),
  media: router({
    list: protectedProcedure.query(({ ctx }) => listMediaAssets(ctx.user.openId)),
    upload: protectedProcedure
      .input(z.object({ name: z.string().trim().min(1).max(255), mimeType: z.string().trim().min(1).max(120), base64: z.string().max(34000000) }))
      .mutation(async ({ ctx, input }) => {
        const buffer = Buffer.from(input.base64, "base64");
        if (buffer.byteLength > 25_000_000) throw new Error("Beta uploads are limited to 25 MB.");
        const stored = await storagePut(`findcut/${ctx.user.openId}/${input.name}`, buffer, input.mimeType);
        return createMediaAsset({ ownerOpenId: ctx.user.openId, name: input.name, mimeType: input.mimeType, sizeBytes: buffer.byteLength, storageKey: stored.key, storageUrl: stored.url });
      }),
  }),
  beta: router({
    submit: publicProcedure
      .input(z.object({
        name: z.string().trim().min(2).max(160),
        email: z.string().trim().email().max(320),
        useCase: z.string().trim().min(12).max(4000),
        donationReference: z.string().trim().max(160).optional(),
      }))
      .mutation(async ({ input }) => {
        const request = await createBetaRequest(input);
        const discord = request ? await sendDiscordBetaNotification({ id: request.id, name: input.name, email: input.email, useCase: input.useCase }) : { configured: discordIsConfigured(), delivered: false };
        return { success: Boolean(request), requestId: request?.id ?? null, discord };
      }),
    list: adminProcedure.query(() => listBetaRequests()),
  }),
  cto: router({
    status: adminProcedure.query(async () => ({
      discordConfigured: discordIsConfigured(),
      role: "FindCut CTO",
      channelMode: "webhook",
      capabilities: ["beta request forwarding", "NLP strategy conversation", "manual invite review"],
    })),
    ask: adminProcedure
      .input(z.object({ messages: z.array(z.object({ role: z.enum(["user", "assistant"]), content: z.string().trim().min(1).max(4000) })).min(1).max(20) }))
      .mutation(async ({ input }) => {
        const response = await invokeLLM({
          messages: [
            { role: "system", content: "You are the FindCut CTO communicating with the founder. Be practical, concise, technically honest, and focused on product, architecture, security, growth, and Pakistan-first operations. Never claim a feature is deployed unless the user’s message or system context confirms it. End with one concrete next action when useful." },
            ...input.messages.map((message) => ({ role: message.role, content: message.content })),
          ],
          reasoning: { effort: "low" },
        });
        const content = response.choices?.[0]?.message?.content;
        const answer = typeof content === "string" ? content : "I could not produce a CTO response right now. Please try again.";
        const discord = await sendDiscordCtoMessage(`**Founder → CTO**\n${input.messages.at(-1)?.content ?? ""}\n\n**CTO → Founder**\n${answer}`);
        return { answer, discord };
      }),
    broadcast: adminProcedure
      .input(z.object({ message: z.string().trim().min(1).max(1900) }))
      .mutation(({ input }) => sendDiscordCtoMessage(input.message)),
  }),
});

export type AppRouter = typeof appRouter;
