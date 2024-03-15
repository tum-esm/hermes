import { SENSOR_IDS } from "@/src/utils/constants";
import { ICONS } from "@/src/components/icons";
import Link from "next/link";
import { useState } from "react";
import { useSensorsStore } from "@/src/utils/state";
import { determinSensorStatus, renderTimeString } from "@/src/utils/functions";
import { maxBy } from "lodash";
import { VARIANT_TO_PILL_COLOR } from "@/src/utils/colors";

function Tab(props: { visible: boolean; children: React.ReactNode }) {
  return (
    <div
      className={
        (props.visible ? "block" : "hidden") + " flex w-full flex-col gap-y-4"
      }
    >
      {props.children}
    </div>
  );
}

function Card(props: {
  key: string | number;
  title: React.ReactNode;
  subtitle: React.ReactNode;
  bottom: any;
}) {
  return (
    <div className="flex flex-col w-full overflow-hidden bg-white border rounded-lg shadow border-slate-300">
      <div className="flex flex-row items-center justify-start px-3 pt-2 pb-1 text-sm gap-x-2 text-slate-900">
        {props.title}
      </div>
      <div className="pb-2 text-xs pl-7">{props.subtitle}</div>
      <div className="px-3 py-2 text-xs leading-tight border-t whitespace-break-spaces border-slate-200 bg-slate-50 text-slate-900 text-opacity-80">
        {JSON.stringify(props.bottom, null, 4)}
      </div>
    </div>
  );
}

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

const TAB_NAMES: ("data" | "logs" | "logs (aggregated)")[] = [
  "data",
  "logs",
  "logs (aggregated)",
];

export default function Page({ sensorName }: { sensorName: string }) {
  const sensorId = SENSOR_IDS[sensorName];
  const [tab, setTab] = useState<"data" | "logs" | "logs (aggregated)">("data");

  const networkState = useSensorsStore((state) => state.state);
  const sensorState = networkState.filter(
    (sensor) => sensor.sensorId === SENSOR_IDS[sensorName]
  )[0];

  const sensorStatus = determinSensorStatus(sensorState);
  const lastDataTime = maxBy(
    sensorState?.data,
    (data) => data.creation_timestamp
  )?.creation_timestamp;
  const lastLogTime = maxBy(
    sensorState?.logs,
    (log) => log.creation_timestamp
  )?.creation_timestamp;

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
        <span className="font-semibold text-black">{sensorName}</span>
      </h2>

      <div className="flex flex-col px-4 pb-4 mt-2 mb-4 text-base border-b border-slate-300">
        <div>
          <span className="inline-block w-24">Status:</span>
          {sensorStatus === undefined ? (
            "-"
          ) : (
            <span
              className={
                "rounded px-1.5 py-0.5 text-sm leading-tight " +
                VARIANT_TO_PILL_COLOR[sensorStatus]
              }
            >
              {sensorStatus}
            </span>
          )}
        </div>
        <div>
          <span className="inline-block w-24">Identifier:</span>
          {sensorId}
        </div>
        <div>
          <span className="inline-block w-24">Last data:</span>
          {renderTimeString(lastDataTime)}
        </div>
        <div>
          <span className="inline-block w-24">Last logs:</span>
          {renderTimeString(lastLogTime)}
        </div>
      </div>

      <div className="inline-flex flex-row items-center justify-start w-full px-4 pb-4 mb-4 space-x-4 border-b border-slate-300 text-slate-700">
        {TAB_NAMES.map((tabName) => (
          <button
            key={tabName}
            className={`${
              tab === tabName ? "bg-slate-200 text-black" : "text-slate-800/60"
            } rounded-md px-3 py-1 text-sm font-medium`}
            onClick={() => setTab(tabName)}
          >
            {tabName}
          </button>
        ))}
      </div>

      {sensorStatus === undefined && <p className="px-4">loading...</p>}
      {sensorStatus !== undefined && (
        <>
          <Tab visible={tab == "data"}>
            {sensorState.data
              ?.sort((a, b) => b.creation_timestamp - a.creation_timestamp)
              .map((data) => (
                <>
                  <Card
                    key={data.creation_timestamp}
                    title={
                      <>
                        <div className="flex-shrink-0 w-2 h-2 bg-blue-500 rounded-sm" />
                        <div>
                          {new Date(
                            data.creation_timestamp * 1000
                          ).toLocaleString()}{" "}
                          (local time)
                        </div>
                      </>
                    }
                    subtitle={renderTimeString(data.creation_timestamp)}
                    bottom={data}
                  />
                </>
              ))}
          </Tab>

          <Tab visible={tab == "logs"}>
            {sensorState.logs
              ?.sort((a, b) => b.creation_timestamp - a.creation_timestamp)
              .map((log) => (
                <Card
                  key={log.creation_timestamp}
                  title={
                    <>
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
                    </>
                  }
                  subtitle={renderTimeString(log.creation_timestamp)}
                  bottom={log}
                />
              ))}
          </Tab>

          <Tab visible={tab == "logs (aggregated)"}>
            {sensorState.aggregatedLogs
              ?.sort(
                (a, b) => b.max_creation_timestamp - a.max_creation_timestamp
              )
              .map((log) => (
                <Card
                  key={log.subject}
                  title={
                    <>
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
                    </>
                  }
                  subtitle={
                    <>
                      last occured{" "}
                      {renderTimeString(log.max_creation_timestamp)} -{" "}
                      {new Date(
                        log.max_creation_timestamp * 1000
                      ).toLocaleString()}{" "}
                      (local time)
                    </>
                  }
                  bottom={log}
                />
              ))}
          </Tab>
        </>
      )}
    </>
  );
}
