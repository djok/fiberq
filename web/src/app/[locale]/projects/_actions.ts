"use server";

import { apiFetch } from "@/lib/api";
import { revalidatePath } from "next/cache";
import type {
  CreateProjectInput,
  AssignableUser,
  ActivityPage,
} from "@/types/project";

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

export async function deleteProject(
  projectId: number,
): Promise<ActionResult> {
  try {
    await apiFetch(`/projects/${projectId}`, {
      method: "DELETE",
    });
    revalidatePath("/[locale]/projects");
    return { success: true, data: undefined };
  } catch (e) {
    return {
      success: false,
      error: e instanceof Error ? e.message : "Failed to delete project",
    };
  }
}

type ApiActivityEntry = {
  event_type: string;
  event_at: string;
  user_sub: string | null;
  user_display_name: string | null;
  details: Record<string, unknown> | null;
};

type ApiActivityPage = {
  entries: ApiActivityEntry[];
  has_more: boolean;
};

export async function fetchActivity(
  projectId: number,
  before?: string,
): Promise<ActionResult<ActivityPage>> {
  try {
    const url = before
      ? `/projects/${projectId}/activity?limit=20&before=${before}`
      : `/projects/${projectId}/activity?limit=20`;
    const data = await apiFetch<ApiActivityPage>(url);
    return {
      success: true,
      data: {
        entries: data.entries.map((e) => ({
          eventType: e.event_type,
          eventAt: e.event_at,
          userSub: e.user_sub,
          userDisplayName: e.user_display_name,
          details: e.details,
        })),
        hasMore: data.has_more,
      },
    };
  } catch (e) {
    return {
      success: false,
      error: e instanceof Error ? e.message : "Failed to fetch activity",
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
