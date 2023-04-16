import { SENSOR_IDS } from "@/components/constants";
import { determinSensorStatus, useNetworkStore } from "@/components/state";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { maxBy } from "lodash";

const variantToBgColor = {
  online: "bg-green-500",
  unstable: "bg-yellow-500",
  error: "bg-red-500",
  offline: "bg-slate-500",
};

function renderTimeString(time: number | undefined): string {
  if (time === undefined) {
    return "-";
  }
  const diff = new Date().getTime() / 1000 - time;
  const formatter = new Intl.RelativeTimeFormat("en");
  if (diff < 60) {
    return formatter.format(Math.floor(-diff), "seconds");
  } else if (diff < 60 * 60) {
    return formatter.format(Math.floor(-diff / 60), "minutes");
  } else if (diff < 60 * 60 * 24 * 2) {
    return formatter.format(Math.floor(-diff / (60 * 60)), "hours");
  } else {
    return formatter.format(Math.floor(-diff / (60 * 60 * 24)), "days");
  }
}

function SensorListItem(props: { sensorName: string }) {
  // TODO: connect data and logs
  // TODO: determine color

  const networkState = useNetworkStore((state) => state.state);
  const sensorState = networkState.filter(
    (sensor) => sensor.sensorId === SENSOR_IDS[props.sensorName]
  )[0];

  const sensorStatus = determinSensorStatus(sensorState);
  const lastDataTime = maxBy(
    sensorState?.data,
    (data) => data.creation_timestamp
  )?.creation_timestamp;
  const lastLogTime = maxBy(
    sensorState?.logs,
    (log) => log.max_creation_timestamp
  )?.max_creation_timestamp;

  const pathname = usePathname();
  const isSelected = pathname === `/sensor/${props.sensorName}`;

  return (
    <li
      key={props.sensorName}
      className={
        "flex w-full flex-row items-center justify-start gap-x-4 px-5 py-4 " +
        (isSelected
          ? "border-r-4 border-slate-900 bg-slate-50"
          : "hover:bg-slate-50")
      }
    >
      <div
        className={
          "h-2 w-2 rounded-sm " +
          (sensorStatus === undefined
            ? "bg-slate-200"
            : variantToBgColor[sensorStatus])
        }
      />
      <div
        className={
          "flex flex-col leading-tight " +
          (isSelected
            ? "text-black"
            : "text-slate-800 group-hover:text-slate-900")
        }
      >
        <p className="mr-2 font-medium">{props.sensorName}</p>
        <p className="text-xs">
          <span className="inline-block w-14">last data:</span>{" "}
          {renderTimeString(lastDataTime)}
        </p>
        <p className="text-xs">
          <span className="inline-block w-14">last log:</span>{" "}
          {renderTimeString(lastLogTime)}
        </p>
      </div>
    </li>
  );
}

export function SensorList() {
  return (
    <ul>
      {Object.keys(SENSOR_IDS).map((sensorName) => (
        <Link
          key={sensorName}
          href={`/sensor/${sensorName}`}
          className="group block border-b border-slate-100 last:border-none hover:bg-slate-50"
        >
          <SensorListItem sensorName={sensorName} />
        </Link>
      ))}
    </ul>
  );
}
