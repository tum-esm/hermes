import { SENSOR_IDS } from "@/components/constants";
import { ICONS } from "@/components/icons";
import Link from "next/link";

// TODO: render overview section (last measurement, last log, sensor id)
// TODO: render tbs for logs and measurements
// TODO: render logs
// TODO: render measurements

export function generateStaticParams() {
  return Object.values(SENSOR_IDS).map((sensorName) => ({
    sensorName,
  }));
}

export default function Page({ params }: { params: { sensorName: string } }) {
  const sensorId = SENSOR_IDS[params.sensorName];

  return (
    <>
      <Link
        href="/"
        className="inline-flex flex-row items-center justify-center p-1 text-sm font-medium gap-x-1 text-slate-800 hover:text-rose-600"
      >
        <div className="h-3.5 w-3.5 rotate-180">{ICONS.chevronRight}</div>
        <p>back to overview</p>
      </Link>

      <h2 className="px-4 mt-3 text-2xl text-slate-800">
        Station{" "}
        <span className="font-semibold text-black">{params.sensorName}</span>{" "}
        (ID: {sensorId})
      </h2>
    </>
  );
}
