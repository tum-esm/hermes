import { SensorState } from "@/src/utils/state";

export function renderTimeString(time: number | undefined): string {
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

export function determinSensorStatus(
  sensor: SensorState
): "online" | "unstable" | "error" | "offline" | undefined {
  if (
    sensor.data === null ||
    sensor.logs === null ||
    sensor.aggregatedLogs === null
  ) {
    return undefined;
  }

  // has data in last 30 minutes
  const hasData =
    sensor.data.filter(
      (data) => data.creation_timestamp > Date.now() - 30 * 60 * 1000
    ).length > 0;

  // has logs in last 30 minutes
  const hasLogs =
    sensor.logs.filter(
      (log) => log.creation_timestamp > Date.now() - 30 * 60 * 1000
    ).length > 0;

  if (hasData && !hasLogs) {
    return "online";
  } else if (hasData && hasLogs) {
    return "unstable";
  } else if (!hasData && hasLogs) {
    return "error";
  } else {
    return "offline";
  }
}
