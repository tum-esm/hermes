import { SENSOR_IDS } from "@/components/constants";
import Link from "next/link";

export default function Home() {
  return (
    <>
      <h1>Hello world!</h1>
      <p>Sensors:</p>
      <ul>
        {Object.keys(SENSOR_IDS).map((sensorName) => (
          <li key={sensorName}>
            <Link href={`/sensor/${sensorName}`}>{sensorName}</Link>
          </li>
        ))}
      </ul>
    </>
  );
}
