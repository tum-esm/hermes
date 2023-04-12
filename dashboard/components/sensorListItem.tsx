"use client";

import { ICONS } from "@/components/icons";
import { usePathname } from "next/navigation";

export function SensorListItem(props: { sensorName: string }) {
  // TODO: fetch data and logs
  // TODO: determine color

  const pathname = usePathname();

  const isSelected = pathname === `/sensor/${props.sensorName}`;

  return (
    <li
      key={props.sensorName}
      className={
        "flex w-full flex-row items-center justify-start gap-x-4 px-5 py-4 " +
        (isSelected
          ? "border-r-4 border-slate-900 bg-slate-50"
          : "hover:bg-slate-50")
      }
    >
      <div className="w-2 h-2 bg-green-500 rounded-sm" />
      <div
        className={
          "flex flex-col leading-tight " +
          (isSelected
            ? "text-black"
            : "text-slate-800 group-hover:text-slate-900")
        }
      >
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
