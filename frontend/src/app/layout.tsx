import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SplitBill",
  description: "Shared expenses, accurate to the satang",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
