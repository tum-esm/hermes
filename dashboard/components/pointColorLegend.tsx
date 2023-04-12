export function PointColorLegend() {
  return (
    <div className="flex flex-row items-center justify-start w-full max-w-4xl px-5 py-3 text-sm border-t gap-x-4 border-slate-200 bg-slate-50">
      <h2 className="font-medium whitespace-nowrap">
        Station Status Indicators
      </h2>
      <div className="flex flex-col items-start justify-start w-full gap-y-1">
        <div className="flex w-full flex-row items-center justify-start gap-x-1.5">
          <div className="w-2 h-2 bg-green-500 rounded-sm" />
          <p className="text-slate-800">
            = only measurement data in the last 30 minutes
          </p>
        </div>
        <div className="flex w-full flex-row items-center justify-start gap-x-1.5">
          <div className="w-2 h-2 bg-yellow-500 rounded-sm" />
          <p className="text-slate-800">
            = measurement data and logs in the last 30 minutes
          </p>
        </div>
        <div className="flex w-full flex-row items-center justify-start gap-x-1.5">
          <div className="w-2 h-2 bg-red-500 rounded-sm" />
          <p className="text-slate-800">= only logs in the last 30 minutes</p>
        </div>
        {/* the same but a slate-500 color for no data in the last 30 minutes */}
        <div className="flex w-full flex-row items-center justify-start gap-x-1.5">
          <div className="w-2 h-2 rounded-sm bg-slate-500" />
          <p className="text-slate-800">= no data in the last 30 minutes</p>
        </div>
      </div>
    </div>
  );
}
