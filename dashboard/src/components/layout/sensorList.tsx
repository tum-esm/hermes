import { useSensorsStore } from "../../utils/state";
import { maxBy } from "lodash";
import { determineSensorStatus, renderTimeString } from "../../utils/functions";
import { VARIANT_TO_BG_COLOR } from "../../utils/colors";

function SensorListItem({ sensorIdentifier }: { sensorIdentifier: string }) {
  const networkState = useSensorsStore((state) => state.state);
  const sensorState = networkState.filter(
    (sensor) => sensor.sensorId === sensorIdentifier
  )[0];

  const sensorStatus = determineSensorStatus(sensorState);
  const lastDataTime = maxBy(
    sensorState?.data,
    (data) => data.creation_timestamp
  )?.creation_timestamp;
  const lastLogTime = maxBy(
    sensorState?.logs,
    (log) => log.creation_timestamp
  )?.creation_timestamp;

  const isSelected = false;

  return (
    <li
      key={sensorIdentifier}
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
            : VARIANT_TO_BG_COLOR[sensorStatus])
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
        <p className="mr-2 font-medium">{sensorState.name}</p>
        <p className="text-xs">
          <span className="inline-block w-14">last data:</span>{" "}
          {renderTimeString(lastDataTime)}
        </p>
        <p className="text-xs">
          <span className="inline-block w-14">last logs:</span>{" "}
          {renderTimeString(lastLogTime)}
        </p>
      </div>
    </li>
  );
}

export function SensorList() {
  let sensors = useSensorsStore((state) => state.state);
  return (
    <ul>
      {Object.values(sensors).map((sensor) => (
        <a
          href={`/sensor/${sensor.sensorId}`}
          className="block border-b group border-slate-100 last:border-none hover:bg-slate-50"
        >
          <SensorListItem sensorIdentifier={sensor.sensorId} />
        </a>
      ))}
    </ul>
  );
}
