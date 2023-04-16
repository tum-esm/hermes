import { SENSOR_IDS } from "@/components/constants";
import { ICONS } from "@/components/icons";
import Link from "next/link";
import { useState } from "react";
import { determinSensorStatus, useNetworkStore } from "@/components/state";

export function getStaticPaths() {
  return {
    paths: Object.keys(SENSOR_IDS).map((sensorName) => ({
      params: { sensorName },
    })),
    fallback: false,
  };
}

// `getStaticPaths` requires using `getStaticProps`
export function getStaticProps(context: any) {
  return {
    // Passed to the page component as props
    props: { sensorName: context.params.sensorName },
  };
}

const TAB_NAMES: ("data" | "logs (aggregated)")[] = [
  "data",
  "logs (aggregated)",
];

export default function Page({ sensorName }: { sensorName: string }) {
  const sensorId = SENSOR_IDS[sensorName];
  const [tab, setTab] = useState<"data" | "logs (aggregated)">("data");

  const networkState = useNetworkStore((state) => state.state);
  const sensorState = networkState.filter(
    (sensor) => sensor.sensorId === SENSOR_IDS[sensorName]
  )[0];

  const sensorStatus = determinSensorStatus(sensorState);

  return (
    <>
      <Link
        href="/"
        className="inline-flex flex-row items-center justify-center gap-x-1 p-1 text-sm font-medium text-slate-800 hover:text-rose-600"
      >
        <div className="h-3.5 w-3.5 rotate-180">{ICONS.chevronRight}</div>
        <p>back to overview</p>
      </Link>

      <h2 className="mt-3 px-4 text-2xl text-slate-800">
        <span className="font-semibold text-black">{sensorName}</span> <br />
        <span className="text-lg">ID: {sensorId}</span>
      </h2>

      <div className="mb-4 mt-6 inline-flex w-full flex-row items-center justify-start space-x-4 border-b border-slate-300 px-4 pb-4 text-slate-700">
        {TAB_NAMES.map((tabName) => (
          <button
            key={tabName}
            className={`${
              tab === tabName ? "bg-slate-200 text-slate-950" : "text-slate-500"
            } rounded-md px-3 py-2 text-sm font-medium`}
            onClick={() => setTab(tabName)}
          >
            {tabName}
          </button>
        ))}
      </div>

      {sensorStatus === undefined && <p className="px-4">loading...</p>}
      {sensorStatus !== undefined && (
        <>
          <div
            className={
              (tab === "data" ? "block" : "hidden") +
              " flex w-full flex-col gap-y-4"
            }
          >
            {sensorState.data
              ?.sort((a, b) => b.creation_timestamp - a.creation_timestamp)
              .map((data) => (
                <div
                  className="flex w-full flex-col overflow-hidden rounded-lg border border-slate-300 bg-white shadow"
                  key={data.creation_timestamp}
                >
                  <div className="flex flex-row items-center justify-start gap-x-2 px-3 py-2 text-sm text-slate-900">
                    <div className="h-2 w-2 flex-shrink-0 rounded-sm bg-blue-500" />
                    <div>
                      {new Date(
                        data.creation_timestamp * 1000
                      ).toLocaleString()}{" "}
                      (local time, unix timestamp ={" "}
                      {Math.round(data.creation_timestamp)})
                    </div>
                  </div>
                  <div className="whitespace-break-spaces border-t border-slate-200 bg-slate-100 px-3 py-2 text-xs leading-tight text-slate-700">
                    {JSON.stringify(data, null, 4)}
                  </div>
                </div>
              ))}
          </div>
          <div
            className={
              (tab === "logs (aggregated)" ? "block" : "hidden") +
              " flex w-full flex-col gap-y-4"
            }
          >
            {sensorState.logs
              ?.sort(
                (a, b) => b.max_creation_timestamp - a.max_creation_timestamp
              )
              .map((log) => (
                <div
                  className="flex w-full flex-col overflow-hidden rounded-lg border border-slate-300 bg-white shadow"
                  key={log.subject}
                >
                  <div className="flex flex-row items-center justify-start gap-x-2 px-3 pb-1 pt-2 text-sm text-slate-900">
                    <div
                      className={
                        "h-2 w-2 flex-shrink-0 rounded-sm " +
                        (log.severity === "info"
                          ? "bg-slate-300"
                          : log.severity === "warning"
                          ? "bg-yellow-500"
                          : "bg-red-500")
                      }
                    />
                    <div>
                      {log.subject.length > 100
                        ? `${log.subject.slice(0, 100)} ...`
                        : log.subject}
                    </div>
                  </div>
                  <span className="pb-2 pl-7 text-xs">
                    last occured at{" "}
                    {new Date(
                      log.max_creation_timestamp * 1000
                    ).toLocaleString()}{" "}
                    (local time)
                  </span>
                  <div className="whitespace-break-spaces border-t border-slate-200 bg-slate-100 px-3 py-2 text-xs leading-tight text-slate-700">
                    {JSON.stringify(log, null, 4)}
                  </div>
                </div>
              ))}
          </div>
        </>
      )}
    </>
  );
}
