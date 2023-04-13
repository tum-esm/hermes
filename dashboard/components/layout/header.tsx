import { ICONS } from "@/components/icons";
import { useStore } from "@/components/state";

export function Header() {
  const increasePopulation = useStore((state) => state.increasePopulation);

  return (
    <header className="flex h-16 w-full flex-shrink-0 flex-row items-center justify-start border-b border-slate-300 px-6">
      <div className="-ml-6 flex h-full w-[5.5rem] items-center border-r border-slate-300 bg-slate-900 px-6 text-slate-100">
        {ICONS.tum}
      </div>
      <h1 className="pl-5 text-xl font-light uppercase text-slate-950">
        <span className="font-medium">Acropolis Sensor Network</span>{" "}
        &nbsp;|&nbsp; Professorship of Environmental Sensing and Modeling
      </h1>
      <div className="flex-grow" />
      <button onClick={increasePopulation}>one up</button>
      <p className="text-slate-800">
        powered by{" "}
        <a
          href="https://github.com/tum-esm/hermes"
          target="_blank"
          className="font-medium text-slate-950 underline"
        >
          github.com/tum-esm/hermes
        </a>
      </p>
    </header>
  );
}
