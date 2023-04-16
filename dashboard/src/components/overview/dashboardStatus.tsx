import { renderTimeString } from "@/src/utils/functions";

export function DashboardStatus() {
  return (
    <div className="mx-auto flex max-w-3xl flex-col overflow-hidden rounded border border-slate-300 bg-white p-4 shadow">
      <p>
        <span className="inline-flex w-28">Commit SHA:</span>{" "}
        {process.env.NEXT_PUBLIC_COMMIT_SHA}
      </p>
      <p>
        <span className="inline-flex w-28">Deploy Time:</span>{" "}
        {renderTimeString(
          parseInt(process.env.NEXT_PUBLIC_BUILD_TIMESTAMP || "0")
        )}{" "}
        (
        {new Date(
          parseInt(process.env.NEXT_PUBLIC_BUILD_TIMESTAMP || "0") * 1000
        ).toISOString()}
        )
      </p>
    </div>
  );
}
