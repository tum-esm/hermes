import { SENSOR_IDS } from "@/components/constants";
import { ICONS } from "@/components/icons";
import Link from "next/link";

// TODO: render server status and URL

function SensorListItem(props: { sensorName: string }) {
  // TODO: fetch measurement and logs data
  // TODO: green if measurements in the last 10 minutes
  // TODO: yellow if no measurements in the last 10 minutes but logs in the last 30 minutes (doing reset routine)
  // TODO: red otherwise

  return (
    <li
      key={props.sensorName}
      className="flex w-full flex-row items-center justify-start gap-x-3 px-5 py-4"
    >
      <div className="h-1.5 w-1.5 rounded-full bg-green-500" />
      <p className="text-slate-800 group-hover:text-black">
        {props.sensorName}
      </p>
      <div className="flex-grow"></div>
      <div className="w-4 text-slate-800 group-hover:text-black">
        {ICONS.chevronRight}
      </div>
    </li>
  );
}

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center gap-y-6 bg-slate-50 px-8 py-16">
      <h1 className="text-3xl font-medium">TUM ESM - Acropolis</h1>
      <div className="w-full max-w-4xl overflow-hidden rounded-lg border border-slate-300 bg-white shadow">
        <ul>
          {Object.keys(SENSOR_IDS).map((sensorName) => (
            <Link
              href={`/sensor/${sensorName}`}
              className="group block border-b border-slate-100 last:border-none hover:bg-slate-50"
            >
              <SensorListItem sensorName={sensorName} />
            </Link>
          ))}
        </ul>
      </div>
    </main>
  );
}
