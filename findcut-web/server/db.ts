import { desc, eq } from "drizzle-orm";
import { drizzle } from "drizzle-orm/mysql2";
import { BetaRequest, InsertBetaRequest, InsertMediaAsset, InsertProject, InsertUser, MediaAsset, Project, betaRequests, mediaAssets, projects, users } from "../drizzle/schema";
import { ENV } from './_core/env';

let _db: ReturnType<typeof drizzle> | null = null;

// Lazily create the drizzle instance so local tooling can run without a DB.
export async function getDb() {
  if (!_db && process.env.DATABASE_URL) {
    try {
      _db = drizzle(process.env.DATABASE_URL);
    } catch (error) {
      console.warn("[Database] Failed to connect:", error);
      _db = null;
    }
  }
  return _db;
}

export async function upsertUser(user: InsertUser): Promise<void> {
  if (!user.openId) {
    throw new Error("User openId is required for upsert");
  }

  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot upsert user: database not available");
    return;
  }

  try {
    const values: InsertUser = {
      openId: user.openId,
    };
    const updateSet: Record<string, unknown> = {};

    const textFields = ["name", "email", "loginMethod"] as const;
    type TextField = (typeof textFields)[number];

    const assignNullable = (field: TextField) => {
      const value = user[field];
      if (value === undefined) return;
      const normalized = value ?? null;
      values[field] = normalized;
      updateSet[field] = normalized;
    };

    textFields.forEach(assignNullable);

    if (user.lastSignedIn !== undefined) {
      values.lastSignedIn = user.lastSignedIn;
      updateSet.lastSignedIn = user.lastSignedIn;
    }
    if (user.role !== undefined) {
      values.role = user.role;
      updateSet.role = user.role;
    } else if (user.openId === ENV.ownerOpenId) {
      values.role = 'admin';
      updateSet.role = 'admin';
    }

    if (!values.lastSignedIn) {
      values.lastSignedIn = new Date();
    }

    if (Object.keys(updateSet).length === 0) {
      updateSet.lastSignedIn = new Date();
    }

    await db.insert(users).values(values).onDuplicateKeyUpdate({
      set: updateSet,
    });
  } catch (error) {
    console.error("[Database] Failed to upsert user:", error);
    throw error;
  }
}

export async function getUserByOpenId(openId: string) {
  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot get user: database not available");
    return undefined;
  }

  const result = await db.select().from(users).where(eq(users.openId, openId)).limit(1);

  return result.length > 0 ? result[0] : undefined;
}

export async function createBetaRequest(request: InsertBetaRequest): Promise<BetaRequest | undefined> {
  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot create beta request: database not available");
    return undefined;
  }
  const result = await db.insert(betaRequests).values(request);
  const insertedId = Number(result[0].insertId);
  const rows = await db.select().from(betaRequests).where(eq(betaRequests.id, insertedId)).limit(1);
  return rows[0];
}

export async function listBetaRequests() {
  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot list beta requests: database not available");
    return [];
  }
  return db.select().from(betaRequests).orderBy(desc(betaRequests.createdAt));
}

export async function createProject(project: InsertProject): Promise<Project | undefined> {
  const db = await getDb();
  if (!db) return undefined;
  const result = await db.insert(projects).values(project);
  const rows = await db.select().from(projects).where(eq(projects.id, Number(result[0].insertId))).limit(1);
  return rows[0];
}

export async function listProjects(ownerOpenId: string) {
  const db = await getDb();
  if (!db) return [];
  return db.select().from(projects).where(eq(projects.ownerOpenId, ownerOpenId)).orderBy(desc(projects.updatedAt));
}

export async function createMediaAsset(asset: InsertMediaAsset): Promise<MediaAsset | undefined> {
  const db = await getDb();
  if (!db) return undefined;
  const result = await db.insert(mediaAssets).values(asset);
  const rows = await db.select().from(mediaAssets).where(eq(mediaAssets.id, Number(result[0].insertId))).limit(1);
  return rows[0];
}

export async function listMediaAssets(ownerOpenId: string) {
  const db = await getDb();
  if (!db) return [];
  return db.select().from(mediaAssets).where(eq(mediaAssets.ownerOpenId, ownerOpenId)).orderBy(desc(mediaAssets.createdAt));
}

// TODO: add feature queries here as your schema grows.
