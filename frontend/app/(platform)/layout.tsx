import { Shell } from "@/components/platform/Shell";

export default function PlatformLayout({ children }: { children: React.ReactNode }) {
  return <Shell>{children}</Shell>;
}
