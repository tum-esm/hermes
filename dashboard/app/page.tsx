import { SENSOR_IDS } from "@/components/constants";
import { ICONS } from "@/components/icons";
import Link from "next/link";

// TODO: render server status and URL
// TODO: render point color legend

function PointColorLegend() {
  return (
    <div className="flex flex-row items-center justify-start w-full max-w-4xl px-5 py-3 text-sm border-t gap-x-4 border-slate-200 bg-slate-50">
      <h2 className="font-medium whitespace-nowrap">
        Station Status Indicators
      </h2>
      <div className="flex flex-col items-start justify-start w-full gap-y-1">
        <div className="flex w-full flex-row items-center justify-start gap-x-1.5">
          <div className="w-2 h-2 bg-green-500 rounded-sm" />
          <p className="text-slate-800">
            = only measurement data in the last 30 minutes
          </p>
        </div>
        <div className="flex w-full flex-row items-center justify-start gap-x-1.5">
          <div className="w-2 h-2 bg-yellow-500 rounded-sm" />
          <p className="text-slate-800">
            = measurement data and logs in the last 30 minutes
          </p>
        </div>
        <div className="flex w-full flex-row items-center justify-start gap-x-1.5">
          <div className="w-2 h-2 bg-red-500 rounded-sm" />
          <p className="text-slate-800">= only logs in the last 30 minutes</p>
        </div>
        {/* the same but a slate-500 color for no data in the last 30 minutes */}
        <div className="flex w-full flex-row items-center justify-start gap-x-1.5">
          <div className="w-2 h-2 rounded-sm bg-slate-500" />
          <p className="text-slate-800">= no data in the last 30 minutes</p>
        </div>
      </div>
    </div>
  );
}

function SensorListItem(props: { sensorName: string }) {
  // TODO: fetch data and logs
  // TODO: determine color

  return (
    <li
      key={props.sensorName}
      className="flex flex-row items-center justify-start w-full px-5 py-4 gap-x-4"
    >
      <div className="w-2 h-2 bg-green-500 rounded-sm" />
      <div className="flex flex-col leading-tight text-slate-800 group-hover:text-black">
        <p className="mr-2 font-medium">{props.sensorName}</p>
        <p className="text-xs">
          <span className="inline-block w-14">last data:</span> ...
        </p>
        <p className="text-xs">
          <span className="inline-block w-14">last log:</span> ...
        </p>
      </div>
      <div className="flex-grow"></div>
      <div className="w-4 text-slate-800 group-hover:text-black">
        {ICONS.chevronRight}
      </div>
    </li>
  );
}

export default function Home() {
  return (
    <>
      <header className="flex flex-row items-center justify-start flex-shrink-0 w-full h-16 px-6 border-b border-slate-300">
        <div className="-ml-6 flex h-full w-[5.5rem] items-center border-r border-slate-300 bg-slate-900 px-6 text-slate-100">
          {ICONS.tum}
        </div>
        <h1 className="pl-5 text-xl font-light uppercase text-slate-950">
          <span className="font-medium">Acropolis Sensor Network</span>{" "}
          &nbsp;|&nbsp; Professorship of Environmental Sensing and Modeling
        </h1>
        <div className="flex-grow" />
        <p className="text-slate-800">
          powered by{" "}
          <a
            href="https://github.com/tum-esm/hermes"
            target="_blank"
            className="font-medium underline text-slate-950"
          >
            github.com/tum-esm/hermes
          </a>{" "}
          ({process.env.NEXT_PUBLIC_COMMIT_SHA})
        </p>
      </header>
      <main className="flex h-[calc(100vh-6.5rem)] w-screen flex-row">
        <nav className="flex max-h-full w-[24rem] flex-col overflow-y-scroll border-r border-slate-300">
          <ul>
            {Object.keys(SENSOR_IDS).map((sensorName) => (
              <Link
                href={`/sensor/${sensorName}`}
                className="block border-b group border-slate-100 last:border-none hover:bg-slate-50"
              >
                <SensorListItem sensorName={sensorName} />
              </Link>
            ))}
          </ul>
        </nav>
        <div className="flex-grow bg-slate-50"></div>
      </main>
      <footer className="flex flex-row items-center justify-center h-10 text-sm bg-slate-900 text-slate-100">
        © TUM Professorship of Environmental Sensing and Modeling
        {process.env.NEXT_PUBLIC_BUILD_TIMESTAMP !== undefined && (
          <>
            ,{" "}
            {new Date(
              parseInt(process.env.NEXT_PUBLIC_BUILD_TIMESTAMP) * 1000
            ).getFullYear()}
          </>
        )}
      </footer>
    </>
  );
}

/*

<div className="w-full max-w-3xl overflow-hidden bg-white border rounded-lg shadow border-slate-300">
        <ul>
          {Object.keys(SENSOR_IDS).map((sensorName) => (
            <Link
              href={`/sensor/${sensorName}`}
              className="block border-b group border-slate-100 last:border-none hover:bg-slate-50"
            >
              <SensorListItem sensorName={sensorName} />
            </Link>
          ))}
        </ul>
        <PointColorLegend />
      </div>

*/
