import { ReactNode } from "react";
import UserShell from "../UserShell";

export default function AppLayout({ children }: { children: ReactNode }) {
  return <UserShell>{children}</UserShell>;
}
