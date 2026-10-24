import React from "react";
import { Navigate, Outlet } from "react-router-dom";
import { getAuthToken } from "../Services/apiClient";
import { useCurrentUserQuery } from "../Services/queries";
import { Button } from "@fluentui/react-components";

const PrivateRoute = () => {
  const token = getAuthToken();
  const query = useCurrentUserQuery({ enabled: Boolean(token), retry: false });
  if (!token || query.error?.status === 401 || query.error?.status === 403) return <Navigate to="/login" replace />;
  if (query.isPending) return <p role="status" className="dwella-route-loading">Loading your account…</p>;
  if (query.isError) return <div role="alert" className="dwella-route-loading"><p>Could not load your account.</p><Button onClick={() => query.refetch()}>Retry</Button></div>;
  return query.data?.email_verification?.required ? <Navigate to="/verify-email" replace /> : <Outlet />;
};

export default PrivateRoute;
