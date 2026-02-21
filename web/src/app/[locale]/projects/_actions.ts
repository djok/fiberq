"use server";

import { apiFetch } from "@/lib/api";
import { revalidatePath } from "next/cache";
import type { CreateProjectInput, AssignableUser } from "@/types/project";

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

export async function updateProject(
  projectId: number,
  data: { name?: string; description?: string; status?: string },
): Promise<ActionResult> {
  try {
    await apiFetch(`/projects/${projectId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
    revalidatePath("/[locale]/projects");
    revalidatePath(`/[locale]/projects/${projectId}`);
    return { success: true, data: undefined };
  } catch (e) {
    return {
      success: false,
      error: e instanceof Error ? e.message : "Failed to update project",
    };
  }
}

export async function assignMember(
  projectId: number,
  data: {
    user_sub: string;
    user_display_name?: string;
    user_email?: string;
    project_role: string;
  },
): Promise<ActionResult> {
  try {
    await apiFetch(`/projects/${projectId}/members`, {
      method: "POST",
      body: JSON.stringify(data),
    });
    revalidatePath(`/[locale]/projects/${projectId}`);
    return { success: true, data: undefined };
  } catch (e) {
    return {
      success: false,
      error: e instanceof Error ? e.message : "Failed to assign member",
    };
  }
}

export async function removeMember(
  projectId: number,
  memberId: number,
): Promise<ActionResult> {
  try {
    await apiFetch(`/projects/${projectId}/members/${memberId}`, {
      method: "DELETE",
    });
    revalidatePath(`/[locale]/projects/${projectId}`);
    return { success: true, data: undefined };
  } catch (e) {
    return {
      success: false,
      error: e instanceof Error ? e.message : "Failed to remove member",
    };
  }
}

type ApiAssignableUser = {
  user_sub: string;
  display_name: string | null;
  email: string | null;
};

export async function fetchAssignableUsers(
  projectId: number,
): Promise<ActionResult<AssignableUser[]>> {
  try {
    const data = await apiFetch<ApiAssignableUser[]>(
      `/projects/${projectId}/assignable-users`,
    );
    const users: AssignableUser[] = data.map((u) => ({
      userSub: u.user_sub,
      displayName: u.display_name,
      email: u.email,
    }));
    return { success: true, data: users };
  } catch (e) {
    return {
      success: false,
      error: e instanceof Error ? e.message : "Failed to fetch assignable users",
    };
  }
}
