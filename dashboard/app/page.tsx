// TODO: render server status and URL
// TODO: render point color legend

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
  number: number;
  variant: "online" | "unstable" | "error" | "offline";
}) {
  return (
    <div className="flex flex-col w-full overflow-hidden bg-white border rounded shadow border-slate-300">
      <div className="flex flex-row items-center justify-start p-4 bg-white gap-x-2">
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
        <p className="px-1 text-2xl font-semibold">{props.number}</p> of 20
      </div>
      <div className="flex-grow w-full px-4 py-2 text-sm bg-slate-50 text-slate-700">
        {variantToDescription[props.variant]}
      </div>
    </div>
  );
}

// TODO: connect data

function NetworkActivity() {
  return (
    <div className="grid max-w-3xl grid-cols-2 mx-auto gap-x-3 gap-y-3">
      <NetworkActivityItem variant="online" number={12} />
      <NetworkActivityItem variant="unstable" number={3} />
      <NetworkActivityItem variant="error" number={2} />
      <NetworkActivityItem variant="offline" number={3} />
    </div>
  );
}

function DashboardStatus() {
  return (
    <div className="flex flex-col max-w-3xl p-4 mx-auto overflow-hidden bg-white border rounded shadow border-slate-300">
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

export default function Home() {
  return (
    <>
      <h2 className="w-full pt-8 pb-4 text-2xl font-medium text-center">
        Server Status
      </h2>
      <h2 className="w-full pt-8 pb-4 text-2xl font-medium text-center">
        Network Activity
      </h2>
      <NetworkActivity />
      <h2 className="w-full pt-8 pb-4 text-2xl font-medium text-center">
        Dashboard Status
      </h2>
      <DashboardStatus />
    </>
  );
}

// ({process.env.NEXT_PUBLIC_COMMIT_SHA})
