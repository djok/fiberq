export type ProjectCard = {
  id: number;
  name: string;
  description: string | null;
  status: string;
  memberCount: number;
  memberNames: string[];
  extent: GeoJSON.Geometry | null;
  createdAt: string;
};

export type ProjectDetail = {
  id: number;
  name: string;
  description: string | null;
  status: string;
  createdAt: string;
  createdBySub: string | null;
  members: ProjectMember[];
  extent: GeoJSON.Geometry | null;
};

export type ProjectMember = {
  id: number;
  userSub: string;
  userDisplayName: string | null;
  userEmail: string | null;
  projectRole: string;
  assignedAt: string;
};

export type CreateProjectInput = {
  name: string;
  description?: string;
};

export type AssignableUser = {
  userSub: string;
  displayName: string | null;
  email: string | null;
};
