"use server";

import { apiFetch } from "@/lib/api";
import { revalidatePath } from "next/cache";
import type {
  CreateUserInput,
  CredentialResetResponse,
  UserRoleUpdateInput,
} from "@/types/user";

type ActionResult<T = void> =
  | { success: true; data: T }
  | { success: false; error: string };

export async function createUser(
  data: CreateUserInput,
): Promise<ActionResult<CredentialResetResponse>> {
  try {
    const result = await apiFetch<CredentialResetResponse>("/users", {
      method: "POST",
      body: JSON.stringify(data),
    });
    revalidatePath("/[locale]/users");
    return { success: true, data: result };
  } catch (e) {
    return {
      success: false,
      error: e instanceof Error ? e.message : "Failed to create user",
    };
  }
}

export async function deactivateUser(
  userId: string,
): Promise<ActionResult> {
  try {
    await apiFetch(`/users/${userId}/deactivate`, { method: "POST" });
    revalidatePath("/[locale]/users");
    return { success: true, data: undefined };
  } catch (e) {
    return {
      success: false,
      error: e instanceof Error ? e.message : "Failed to deactivate user",
    };
  }
}

export async function reactivateUser(
  userId: string,
): Promise<ActionResult> {
  try {
    await apiFetch(`/users/${userId}/reactivate`, { method: "POST" });
    revalidatePath("/[locale]/users");
    return { success: true, data: undefined };
  } catch (e) {
    return {
      success: false,
      error: e instanceof Error ? e.message : "Failed to reactivate user",
    };
  }
}

export async function updateUserRoles(
  userId: string,
  data: UserRoleUpdateInput,
): Promise<ActionResult> {
  try {
    await apiFetch(`/users/${userId}/roles`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
    revalidatePath("/[locale]/users");
    return { success: true, data: undefined };
  } catch (e) {
    return {
      success: false,
      error: e instanceof Error ? e.message : "Failed to update roles",
    };
  }
}

export async function resetUserPassword(
  userId: string,
): Promise<ActionResult<CredentialResetResponse>> {
  try {
    const result = await apiFetch<CredentialResetResponse>(
      `/users/${userId}/reset-password`,
      { method: "POST" },
    );
    revalidatePath("/[locale]/users");
    return { success: true, data: result };
  } catch (e) {
    return {
      success: false,
      error: e instanceof Error ? e.message : "Failed to reset password",
    };
  }
}
