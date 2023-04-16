import "./globals.css";
import Layout from "@/src/components/layout.tsx";

export default function App({ Component, pageProps }) {
  return (
    <Layout>
      <Component {...pageProps} />
    </Layout>
  );
}
