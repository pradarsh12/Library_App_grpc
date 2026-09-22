import "server-only";

import { memberClient, call } from "./client";
import { MemberMethod } from "./methods";
import type {
  CreateMemberRequest,
  ListMembersRequest,
  ListMembersResponse,
  Member,
  UpdateMemberRequest,
} from "./types";

export function listMembers(search = ""): Promise<ListMembersResponse> {
  const req: ListMembersRequest = { search, page: { pageSize: 100 } };
  return call(memberClient, MemberMethod.ListMembers, req);
}

export function getMember(id: string): Promise<Member> {
  return call(memberClient, MemberMethod.GetMember, { id });
}

export function createMember(req: CreateMemberRequest): Promise<Member> {
  return call(memberClient, MemberMethod.CreateMember, req);
}

export function updateMember(req: UpdateMemberRequest): Promise<Member> {
  return call(memberClient, MemberMethod.UpdateMember, req);
}
