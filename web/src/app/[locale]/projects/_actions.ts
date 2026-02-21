"use server";

import { apiFetch } from "@/lib/api";
import { revalidatePath } from "next/cache";
import type { CreateProjectInput } from "@/types/project";

type ActionResult<T = void> =
  | { success: true; data: T }
  | { success: false; error: string };

export async function createProject(
  data: CreateProjectInput,
): Promise<ActionResult<{ id: number }>> {
  try {
    const result = await apiFetch<{ id: number }>("/projects", {
      method: "POST",
      body: JSON.stringify(data),
    });
    revalidatePath("/[locale]/projects");
    return { success: true, data: result };
  } catch (e) {
    return {
      success: false,
      error: e instanceof Error ? e.message : "Failed to create project",
    };
  }
}
