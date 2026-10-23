/* eslint-disable no-unused-vars */
import React, { Suspense, useEffect, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Signin from "../Auth/Signin";
import Signup from "../Auth/Signup";
import LayoutRoutes from "../Route/LayoutRoutes";
import PrivateRoute from "./PrivateRoute";
import { AUTHENTICATED_STORAGE_KEY } from "../shared/storage";

const routerBasePath = (import.meta.env.VITE_BASE_PATH || "/").replace(/\/$/, "") || "/";

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
          </Routes>
        </Suspense>
      </>
    </BrowserRouter>
  );
};

export default Routers;
