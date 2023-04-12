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

function NetworkStatisticsElement(props: {
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
        {props.variant === "online" && (
          <>
            <span className="font-medium">only</span> data in the last 30
            minutes
          </>
        )}
        {props.variant === "unstable" && (
          <>
            data <span className="font-medium">and</span> logs in the last 30
            minutes
          </>
        )}
        {props.variant === "error" && (
          <>
            <span className="font-medium">only</span> logs in the last 30
            minutes
          </>
        )}
        {props.variant === "offline" && (
          <>
            no data <span className="font-medium">or</span> logs in the last 30
            minutes
          </>
        )}
      </div>
    </div>
  );
}

function NetworkStatistics() {
  return (
    <div className="grid max-w-3xl grid-cols-2 mx-auto gap-x-3 gap-y-3">
      <NetworkStatisticsElement variant="online" number={2} />
      <NetworkStatisticsElement variant="unstable" number={2} />
      <NetworkStatisticsElement variant="error" number={2} />
      <NetworkStatisticsElement variant="offline" number={2} />
    </div>
  );
}

export default function Home() {
  return (
    <>
      <h2 className="w-full pt-8 pb-4 text-2xl font-medium text-center">
        Server Stats
      </h2>
      <h2 className="w-full pt-8 pb-4 text-2xl font-medium text-center">
        Network Activity
      </h2>
      <NetworkStatistics />
    </>
  );
}
