export type UserRow = {
  id: string;
  username: string;
  displayName: string;
  email: string;
  phone: string | null;
  roles: string[];
  isActive: boolean;
  lastLogin: string | null;
};

export type UserListResponse = {
  users: UserRow[];
};

export type CreateUserInput = {
  username: string;
  display_name: string;
  email: string;
  phone?: string;
  roles: string[];
};

export type CredentialResetResponse = {
  token: string;
  ttl: number;
  reset_url: string;
};

export type UserRoleUpdateInput = {
  roles: string[];
};
