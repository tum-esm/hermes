import "./globals.css";
import { RecoilRoot } from "recoil";
import Layout from "@/components/layout.tsx";

export default function App({ Component, pageProps }) {
  return (
    <RecoilRoot>
      <Layout>
        <Component {...pageProps} />
      </Layout>
    </RecoilRoot>
  );
}
