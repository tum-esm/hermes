import indexPage from "./pages/index";
import Layout from "./components/layout";
import {
    BrowserRouter,
    Route,
    Routes
} from "react-router-dom";
import loginPage from "@/src/pages/login";
import adminPage from "@/src/pages/admin";
import sensorPage from "@/src/pages/sensor/[sensorName]";

export default function App() {
    return (
        <Layout>
            <BrowserRouter>
                <Routes>
                    <Route path="/" Component={indexPage} />
                    <Route path="/login" Component={loginPage} />
                    <Route path="/admin*" Component={adminPage} />
                    <Route path="/sensor/:identifier" Component={sensorPage} />
                </Routes>
            </BrowserRouter>
        </Layout>
    );
}
