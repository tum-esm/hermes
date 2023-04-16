import { renderTimeString } from "@/src/utils/functions";
import { useServerStore } from "@/src/utils/state";

export function ServerStatus() {
  const serverStatus = useServerStore((state) => state.state);

  return (
    <div className="mx-auto flex max-w-3xl flex-col overflow-hidden rounded border border-slate-300 bg-white p-4 shadow">
      <p>
        <span className="inline-flex w-28">Environment:</span>{" "}
        {serverStatus?.environment || "..."}
      </p>
      <p>
        <span className="inline-flex w-28">Commit SHA:</span>{" "}
        {serverStatus?.commit_sha || "..."}
      </p>
      <p>
        <span className="inline-flex w-28">Branch Name:</span>{" "}
        {serverStatus?.branch_name || "..."}
      </p>
      <p>
        <span className="inline-flex w-28">Start Time:</span>{" "}
        {renderTimeString(
          serverStatus ? serverStatus.start_timestamp : undefined
        )}{" "}
        (
        {serverStatus
          ? new Date(serverStatus.start_timestamp * 1000).toISOString()
          : "..."}
        )
      </p>
    </div>
  );
}
