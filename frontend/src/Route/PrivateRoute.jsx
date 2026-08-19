import React from "react";
import { Navigate, Outlet } from "react-router-dom";
import { getAuthToken } from "../Services/apiClient";

const PrivateRoute = () => {
  return getAuthToken() ? <Outlet /> : <Navigate to="/login" replace />;
};

export default PrivateRoute;
