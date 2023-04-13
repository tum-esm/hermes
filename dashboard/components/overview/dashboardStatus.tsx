import { useStore } from "@/components/state";

export function DashboardStatus() {
  const bears = useStore((state) => state.bears);

  return (
    <div className="mx-auto flex max-w-3xl flex-col overflow-hidden rounded border border-slate-300 bg-white p-4 shadow">
      <p>
        <span className="inline-flex w-28">Bears:</span>{" "}
        <span className="font-medium">{bears}</span>
      </p>
      <p>
        <span className="inline-flex w-28">Commit SHA:</span>{" "}
        <span className="font-medium">
          {process.env.NEXT_PUBLIC_COMMIT_SHA}
        </span>
      </p>
      <p>
        <span className="inline-flex w-28">Deploy Time:</span>{" "}
        <span className="font-medium">
          {new Date(
            parseInt(process.env.NEXT_PUBLIC_BUILD_TIMESTAMP || "0") * 1000
          ).toISOString()}
        </span>
      </p>
    </div>
  );
}
