import { COOKIE_NAME } from "@shared/const";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { adminProcedure, protectedProcedure, publicProcedure, router } from "./_core/trpc";
import { createBetaRequest, createMediaAsset, createProject, listBetaRequests, listMediaAssets, listProjects } from "./db";
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
        return { success: Boolean(request), requestId: request?.id ?? null };
      }),
    list: adminProcedure.query(() => listBetaRequests()),
  }),
});

export type AppRouter = typeof appRouter;
