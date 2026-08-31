import "server-only";

import { memberClient, call } from "./client";
import type {
  CreateMemberRequest,
  ListMembersRequest,
  ListMembersResponse,
  Member,
  UpdateMemberRequest,
} from "./types";

export function listMembers(search = ""): Promise<ListMembersResponse> {
  const req: ListMembersRequest = { search, page: { pageSize: 100 } };
  return call(memberClient, "ListMembers", req);
}

export function getMember(id: string): Promise<Member> {
  return call(memberClient, "GetMember", { id });
}

export function createMember(req: CreateMemberRequest): Promise<Member> {
  return call(memberClient, "CreateMember", req);
}

export function updateMember(req: UpdateMemberRequest): Promise<Member> {
  return call(memberClient, "UpdateMember", req);
}
