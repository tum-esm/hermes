import { SENSOR_IDS } from "@/components/constants";
import { ICONS } from "@/components/icons";
import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center gap-y-6 bg-slate-50 px-8 py-16">
      <h1 className="text-3xl font-medium">TUM ESM - Acropolis</h1>
      <div className="w-full max-w-4xl overflow-hidden rounded-lg border border-slate-300 bg-white shadow">
        <ul>
          {Object.keys(SENSOR_IDS).map((sensorName) => (
            <Link
              href={`/sensor/${sensorName}`}
              className="block border-b border-slate-100 last:border-none hover:bg-slate-100"
            >
              <li
                key={sensorName}
                className="flex w-full flex-row items-center justify-start gap-x-3 p-4"
              >
                <div className="w-5 text-green-700">{ICONS.router}</div>
                <p className="text-slate-900">{sensorName}</p>
                <div className="flex-grow"></div>
                <div className="w-5 text-slate-700">{ICONS.chevronRight}</div>
              </li>
            </Link>
          ))}
        </ul>
      </div>
    </main>
  );
}
