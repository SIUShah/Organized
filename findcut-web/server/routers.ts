import { COOKIE_NAME } from "@shared/const";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { adminProcedure, publicProcedure, router } from "./_core/trpc";
import { createBetaRequest, listBetaRequests } from "./db";
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
