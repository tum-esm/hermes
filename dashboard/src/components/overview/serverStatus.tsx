import { useServerStore } from "@/src/utils/state";

export function ServerStatus() {
  const serverStatus = useServerStore((state) => state.state);

  return (
    <div className="mx-auto flex max-w-3xl flex-col overflow-hidden rounded border border-slate-300 bg-white p-4 shadow">
      <p>
        <span className="inline-flex w-28">Environment:</span>{" "}
        <span className="font-medium">
          {serverStatus?.environment || "..."}
        </span>
      </p>
      <p>
        <span className="inline-flex w-28">Commit SHA:</span>{" "}
        <span className="font-medium">{serverStatus?.commit_sha || "..."}</span>
      </p>
      <p>
        <span className="inline-flex w-28">Branch Name:</span>{" "}
        <span className="font-medium">
          {serverStatus?.branch_name || "..."}
        </span>
      </p>
      <p>
        <span className="inline-flex w-28">Start Time:</span>{" "}
        <span className="font-medium">
          {serverStatus
            ? new Date(serverStatus.start_timestamp * 1000).toISOString()
            : "..."}
        </span>
      </p>
    </div>
  );
}
