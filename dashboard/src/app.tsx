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
import {URL_BASE_NAME} from "@/src/utils/constants";

export default function App() {
    return (
        <BrowserRouter basename={URL_BASE_NAME}>
            <Layout>
                <Routes>
                    <Route path="/" Component={indexPage} />
                    <Route path="/login" Component={loginPage} />
                    <Route path="/admin*" Component={adminPage} />
                    <Route path="/sensor/:identifier" Component={sensorPage}/>
                </Routes>
            </Layout>
        </BrowserRouter>
    );
}
