import { ICONS } from "@/src/components/icons";
import Link from "next/link";

export function Header() {
  return (
    <header className="flex h-16 w-full flex-shrink-0 flex-row items-center justify-start border-b border-slate-300 px-6">
      <Link
        href="/"
        className="-ml-6 flex h-full w-[5.5rem] items-center border-r border-slate-300 bg-slate-900 px-6 text-slate-100"
      >
        {ICONS.tum}
      </Link>
      <Link href="/">
        <h1 className="hidden pl-5 font-light uppercase text-slate-950 xl:block xl:text-lg 2xl:text-xl">
          <span className="font-medium">Acropolis Sensor Network</span>{" "}
          &nbsp;|&nbsp; Professorship of Environmental Sensing and Modeling
        </h1>
      </Link>
      <div className="flex-grow" />
      <p className="text-slate-800">
        powered by{" "}
        <Link
          href="https://github.com/tum-esm/hermes"
          target="_blank"
          className="font-medium text-slate-950 underline hover:text-rose-600"
        >
          github.com/tum-esm/hermes
        </Link>
      </p>
    </header>
  );
}
