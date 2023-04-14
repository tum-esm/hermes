import { determinSensorStatus, useNetworkStore } from "@/components/state";

const variantToBgColor = {
  online: "bg-green-500",
  unstable: "bg-yellow-500",
  error: "bg-red-500",
  offline: "bg-slate-500",
};

const variantToTextColor = {
  online: "text-green-800",
  unstable: "text-yellow-800",
  error: "text-red-800",
  offline: "text-slate-800",
};

const variantToDescription = {
  online: (
    <>
      <span className="font-medium">only</span> data in the last 30 minutes
    </>
  ),
  unstable: (
    <>
      data <span className="font-medium">and</span> logs in the last 30 minutes{" "}
    </>
  ),
  error: (
    <>
      <span className="font-medium">only</span> logs in the last 30 minutes
    </>
  ),
  offline: (
    <>
      no data <span className="font-medium">or</span> logs in the last 30
      minutes
    </>
  ),
};

function NetworkActivityItem(props: {
  count: number;
  total: number;
  variant: "online" | "unstable" | "error" | "offline";
}) {
  return (
    <div className="flex w-full flex-col overflow-hidden rounded border border-slate-300 bg-white shadow">
      <div className="flex flex-row items-center justify-start gap-x-2 bg-white p-4">
        <div
          className={"h-3 w-3 rounded-sm " + variantToBgColor[props.variant]}
        />
        <p
          className={
            "font-medium uppercase " + variantToTextColor[props.variant]
          }
        >
          {props.variant}
        </p>
        <div className="flex-grow" />
        <p className="px-1 text-2xl font-semibold">{props.count}</p> of{" "}
        {props.total}
      </div>
      <div className="w-full flex-grow bg-slate-50 px-4 py-2 text-sm text-slate-700">
        {variantToDescription[props.variant]}
      </div>
    </div>
  );
}

export function NetworkActivity() {
  const networkState = useNetworkStore((state) => state.state);

  const sensorCountOnline = networkState.filter(
    (sensor) => determinSensorStatus(sensor) === "online"
  ).length;

  const sensorCountUnstable = networkState.filter(
    (sensor) => determinSensorStatus(sensor) === "unstable"
  ).length;

  const sensorCountError = networkState.filter(
    (sensor) => determinSensorStatus(sensor) === "error"
  ).length;

  const sensorCountOffline = networkState.filter(
    (sensor) => determinSensorStatus(sensor) === "offline"
  ).length;

  const sensorCountTotal =
    sensorCountOnline +
    sensorCountUnstable +
    sensorCountError +
    sensorCountOffline;

  return (
    <div className="mx-auto grid max-w-3xl grid-cols-2 gap-x-3 gap-y-3">
      <NetworkActivityItem
        variant="online"
        count={sensorCountOnline}
        total={sensorCountTotal}
      />
      <NetworkActivityItem
        variant="unstable"
        count={sensorCountUnstable}
        total={sensorCountTotal}
      />
      <NetworkActivityItem
        variant="error"
        count={sensorCountError}
        total={sensorCountTotal}
      />
      <NetworkActivityItem
        variant="offline"
        count={sensorCountOffline}
        total={sensorCountTotal}
      />
    </div>
  );
}
