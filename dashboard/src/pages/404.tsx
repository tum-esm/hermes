import Link from "next/link";

export default function Page() {
  return (
    <div className="flex h-full w-full flex-col items-center justify-center gap-y-2">
      <div className="text-xl text-slate-950">
        <span className="font-medium">404</span> | Page not found
      </div>
      <Link href="/" className="text-slate-800 hover:text-rose-600">
        Go back to Overview
      </Link>
    </div>
  );
}
