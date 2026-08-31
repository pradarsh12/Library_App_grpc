import type { LoanStatus, MemberStatus } from "./types";

export const memberStatusLabel: Record<
  MemberStatus,
  { label: string; color: "green" | "amber" | "gray" | "red" }
> = {
  MEMBER_STATUS_UNSPECIFIED: { label: "Unspecified", color: "gray" },
  MEMBER_STATUS_ACTIVE: { label: "Active", color: "green" },
  MEMBER_STATUS_INACTIVE: { label: "Inactive", color: "gray" },
  MEMBER_STATUS_SUSPENDED: { label: "Suspended", color: "red" },
};

export const loanStatusLabel: Record<
  LoanStatus,
  { label: string; color: "green" | "amber" | "gray" | "red" }
> = {
  LOAN_STATUS_UNSPECIFIED: { label: "Unspecified", color: "gray" },
  LOAN_STATUS_ACTIVE: { label: "Active", color: "green" },
  LOAN_STATUS_OVERDUE: { label: "Overdue", color: "red" },
  LOAN_STATUS_RETURNED: { label: "Returned", color: "gray" },
};
