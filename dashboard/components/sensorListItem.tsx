export function SensorListItem(props: { sensorName: string }) {
  // TODO: fetch data and logs
  // TODO: determine color

  return (
    <li
      key={props.sensorName}
      className="flex flex-row items-center justify-start w-full px-5 py-4 gap-x-4"
    >
      <div className="w-2 h-2 bg-green-500 rounded-sm" />
      <div className="flex flex-col leading-tight text-slate-800 group-hover:text-black">
        <p className="mr-2 font-medium">{props.sensorName}</p>
        <p className="text-xs">
          <span className="inline-block w-14">last data:</span> ...
        </p>
        <p className="text-xs">
          <span className="inline-block w-14">last log:</span> ...
        </p>
      </div>
    </li>
  );
}
