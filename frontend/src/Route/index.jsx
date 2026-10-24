/* eslint-disable no-unused-vars */
import React, { Suspense, useEffect, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";
import Signin from "../Auth/Signin";
import Signup from "../Auth/Signup";
import VerifyEmail from "../Auth/VerifyEmail";
import AcceptInvitation from "../Auth/AcceptInvitation";
import LayoutRoutes from "../Route/LayoutRoutes";
import PrivateRoute from "./PrivateRoute";
import { AUTHENTICATED_STORAGE_KEY } from "../shared/storage";
const PublicSigning = React.lazy(() => import("../Components/Documents/PublicSigning"));

const routerBasePath = (import.meta.env.VITE_BASE_PATH || "/").replace(/\/$/, "") || "/";

function RouteEffects() {
  const location = useLocation();
  useEffect(() => { window.dispatchEvent(new Event("dwella:route-changed")); }, [location.pathname]);
  return null;
}

const Routers = () => {
  const [currentUser, setCurrentUser] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    let abortController = new AbortController();
    setAuthenticated(JSON.parse(localStorage.getItem(AUTHENTICATED_STORAGE_KEY)));
    console.ignoredYellowBox = ["Warning: Each", "Warning: Failed"];
        console.disableYellowBox = true;
    return () => {
      abortController.abort();
    };
  }, []);

  return (
    <BrowserRouter basename={routerBasePath}>
      <RouteEffects />
      <>
        <Suspense fallback={<div className="dwella-route-loading">Loading Dwella Suite</div>}>
          <Routes>
            <Route path={"/"} element={<PrivateRoute />}>
              {currentUser !== null || authenticated ? (
                <>
                  <Route exact path={``} element={<Navigate to={`/dashboard`} />} />
                  <Route exact path={`/`} element={<Navigate to={`/dashboard`} />} />
                </>
              ) : (
                ""
              )}
              <Route path={`/*`} element={<LayoutRoutes />} />
            </Route>
            <Route exact path={`/login`} element={<Signin />} />
            <Route path="/register" element={<Signup />} />
            <Route path="/verify-email" element={<VerifyEmail />} />
            <Route path="/accept-invitation" element={<AcceptInvitation />} />
            <Route path="/sign/:token" element={<PublicSigning />} />
          </Routes>
        </Suspense>
      </>
    </BrowserRouter>
  );
};

export default Routers;
