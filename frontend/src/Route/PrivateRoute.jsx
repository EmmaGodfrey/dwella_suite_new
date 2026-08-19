/* eslint-disable react-hooks/exhaustive-deps */
import React, { useEffect, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";

const PrivateRoute = () => {
  const [login, setLogin] = useState(JSON.parse(localStorage.getItem("login")) ? JSON.parse(localStorage.getItem("login")) : false);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    setAuthenticated(JSON.parse(localStorage.getItem("authenticated")));
    localStorage.setItem("authenticated", authenticated);
    setLogin(JSON.parse(localStorage.getItem("login")));
  }, [setLogin]);

  return login !== false || authenticated !== false ? <Outlet /> : <Navigate exact to={`/login`} />;
};

export default PrivateRoute;
